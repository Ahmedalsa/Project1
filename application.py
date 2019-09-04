import os, json

from flask import Flask, session, render_template, request, redirect, url_for, jsonify, flash
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
    session.clear()
    if request.method == "POST":
            #Read entered values from new user
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        #check for submitted username and password
        if not username:
            return render_template("error.html", message="Please provide a vaild username!")

        check_for_user = db.execute("SELECT * FROM users WHERE username = :username",
        {"username":username}).fetchone()

        if not password:
            return render_template("error.html", message="Please provide a valid password!")

        if not confirm:
            return render_template("error.html", message="Please provide a valid confirmation!")
        #enter values to the database.
        register = "INSERT INTO users (username, password) VALUES (:username, :password)"
        db.execute(register, {"username": username, "password": password})
        db.commit()

        flash('Account created', 'info')

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
    session.clear()

    username = request.form.get("username")

    if request.method == "POST":
        password = request.form.get("password")
        #check for submitted username and password
        if not username:
            return render_template("error.html", message="Please provide a vaild username!")

        result = db.execute("SELECT * FROM users WHERE username = :username",
        {"username":username}).fetchone()
        if result = None:
            return render_template("error.html", message="invalid username and/or password")

        session["user_id"] = result[0]
        session["username"] = result[1]
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():

    #Forget user id
    session.clear()

    #Redirect the user to the login form
    return redirect("/")


app.route("/book/<int:isbn>", methods=["GET", "POST"])

def book(isbn):
    if request.method == "POST":
        current = session["user_id"]
        book_review = request.form.get("review")
        book_rating = request.form.get("rating")
        #search book id using the isbn number.
        selected_book = db.execute("SELECT id FROM books WHERE isbn = :isbn", {"isbn": isbn})
        #save as a variable.
        bookid = selected_book.fetchone()
        bookid = bookid[0]

        book_reviews = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id",
         {"user_id": current, "book_id": bookid})

         if book_reviews.count == 1:
             flash('You already submitted a review for this book', 'warning')
             return redirect("/book/" + isbn)

        #to be save in the database.
        rating = int(rating)

        db.execute("INSERT INTO reviews (user_id, book_id, review, rating) VALUES (:user_id, :book_id, :review, :rating)",
                {"user_id": current, "book_id": bookid, "review": review, "rating": rating})
        db.commit()

        flash('submitted', 'info')
        return redirect("/book/" + isbn)

    else:
        selected = db.execute("SELECT isbn, title, author, year FROM books WHERE isbn = :isbn", {"isbn": isbn})
        info = selected.fetchall()

        #read API key from goodreads.
        key = os.getenv("GOODREADS_KEY")
        #getting the api from the website goodreads.com
        response = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
        json_response = response.json()

        #save user's book as a variable.
        user_book = selected.fetchone()
        user_book = user_book[0]

        review_query = db.execute("SELECT users.username, comment, rating, \
                            to_char(time, 'DD Mon YY - HH24:MI:SS') as time \
                            FROM users \
                            INNER JOIN reviews \
                            ON users.id = reviews.user_id \
                            WHERE book_id = :book \
                            ORDER BY time",
                            {"book": book})

        reviews = review_query.fetchall()
        return render_template("book.html", info=info, reviews=reviews)


    #check if selected book exists.


        #Checking that book reviews are not repeated.









@app.route("/api/<string:isbn>", methods=["GET", "POST"])
def api(isbn):



    selected_book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if selected_book is None:
        #return unprocessable entity error.
        return jsonify({"success:" "False"}), 422


    return jsonify({
    "title": selected_book.title,
    "author": selected_book.author,
    "year": selected_book.year,
    "isbn": selected_book.isbn,
    "review_count": books_list['work_ratings_count'],
    "average_score": books_list['average_rating']
})
