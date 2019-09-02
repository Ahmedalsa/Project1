import os

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
from jinja2 import Template


app = Flask(__name__, template_folder='C:/Users/welcome/Downloads/project1/templates')

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
user = []


@app.route("/")
def index():



    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
            #Read entered values from new user
        username = request.form.get("username")
        password = request.form.get("password")
        #enter values to the database.
        register = "INSERT INTO users (username, password) VALUES (:username, :password)"
        db.execute(register, {"username": username, "password": password})
        db.commit()

        return render_template("login.html")
    else:
        return render_template("signup.html")



@app.route("/search", methods=["GET", "POST"])
def search():
    result = []
    isbn = request.form.get("isbn")
    title = request.form.get("title")
    author = request.form.get("author")
    year = request.form.get("year")
    sql_string = "SELECT * FROM books WHERE isbn LIKE :isbn OR title = :title OR author = :author OR year LIKE :year "
    if request.method == "POST":
        result = db.execute(sql_string, {"isbn": f"%{isbn}%", "title": title, "author": author, "year": year}).fetchall()
        return render_template("search.html", result=result)

    return render_template("search.html", result=result)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':

        session['username'] = request.form['username']
        session['email'] = request.form['email']
        session['id'] = request.form['id']
        return redirect(url_for('index'))
    return render_template("login.html")

@app.route("/logout")
def logout():

    # Forget any user id
    session["user_id"] = []

    # Redirect user to login form
    return render_template("index.html")


app.route("/book/<int:id>", methods=["GET", "POST"])

def book(id):
    #getting the api from the website goodreads.com
    isbn = db.execute("SELECT isbn FROM books WHERE id = :id", {"id": id}).fetchone()
    response = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "odIyXgoUO32BFSKOfJwaEA", "isbns": "9781632168146"})
    d = response.json()
    books = d["books"]
    books_list = books[0]

    #check if selected book exists.
    check_book = db.execute("SELECT * FROM books WHERE id = :id", {"id": id}).fetchone()
    if check_book is None:
        return render_template("search.html")

        book_reviews = db.execute("SELECT * FROM reviews WHERE book_id = :id", {"id": id}).fetchall()
        user_id = session["user_id"]
        if request.method.form == "POST":
            book_review = request.form.get("review")
            book_rating = request.form.get("rating")

        #Checking that book reviews are not repeated.
        check_reviews = db.execute("SELECT book_id, user_id FROM reviews WHERE book_id = :book_id AND user_id = :user_id",
            {"book_id": id, "user_id": user_id}).fetchone()

        if check_reviews:
            return render_template("book.html", check_book=check_book, book_reviews=book_reviews, book_list=books_list, isbn=isbn, message="Reviewed Already!")
        else:
            db.execute("INSERT INTO reviews (rating, review, user_id, book_id) VALUES (:rating, :review, :user_id, :book_id)",
                    {"rating": book_rating, "review": book_review, "user_id": user_id, "book_id": id})
            db.commit()
            book_reviews = db.execute("SELECT * FROM reviews WHERE book_id = :id", {"id": id}).fetchall()
            return render_template("book.html", check_book=check_book, book_reviews=book_reviews, book_list=books_list, isbn=isbn)

    return render_template("book.html", check_book=check_book, book_reviews=book_reviews, book_list=books_list, isbn=isbn)








@app.route("/api/<string:isbn>", methods=["GET", "POST"])
def api(isbn):
    selected_book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn})
    if selected_book is None:
        #return unprocessable entity error.
        return jsonify({"error:" "isbn not vaild"}), 422

    response = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "odIyXgoUO32BFSKOfJwaEA", "isbns": "9781632168146"})
    d = response.json()
    books = d["books"]
    books_list = books[0]
    print(books_list)
    print(books_list['work_ratings_count'])

    return jsonify({
    "title": selected_book.title,
    "author": selected_book.author,
    "year": selected_book.year,
    "isbn": selected_book.isbn,
    "review_count": books_list['work_ratings_count'],
    "average_score": books_list['average_rating']
})
