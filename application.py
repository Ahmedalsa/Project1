import os, json

from flask import Flask, session, render_template, request, redirect, url_for, jsonify, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
from jinja2 import Template
from decorators import login_required


app = Flask(__name__)

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
@login_required
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

        if check_for_user:
            return render_template("error.html", message="That user already exists!")

        elif not password:
            return render_template("error.html", message="Please provide a valid password!")

        elif not confirm:
            return render_template("error.html", message="Please provide a valid confirmation!")
        #enter values to the database.
        register = "INSERT INTO users (username, password) VALUES (:username, :password)"
        db.execute(register, {"username": username, "password": password})
        db.commit()

        flash('User created', 'info')

        return render_template("login.html")
    else:
        return render_template("signup.html")



@app.route("/search", methods=["GET"])
@login_required
def search():
    #check if the book id is valid.
    if not request.args.get("book"):
        return render_template("error.html", message="Invalid book id")

    #Searh input query.
    query = "%" + request.args.get("book") + "%"

    #convert query to all caps.
    query = query.title()

    sql_string = "SELECT isbn, title, author, year FROM books WHERE isbn LIKE :query OR title LIKE :query OR author LIKE :query"
    result = db.execute(sql_string, {"query": query})


    #in case book is not found.
    if result.rowcount == 0:
        return render_template("error.html", message="Book Not Found!")

    books = result.fetchall()

    return render_template("results.html", books=books)


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    username = request.form.get("username")

    if request.method == "POST":
        password = request.form.get("password")
        #check for submitted username and password
        if not username:
            return render_template("error.html", message="Please provide a vaild username!")
        elif not request.form.get("password"):
            return render_template("error.html", message="Please provide a vaild password!")

        result = db.execute("SELECT * FROM users WHERE username = :username",
        {"username":username}).fetchone()
        if result is None:
            return render_template("error.html", message="invalid username and/or password")

        session["user_id"] = result[0]
        session["username"] = result[1]
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/logout")
@login_required
def logout():

    #Forget user id
    session.clear()

    #Redirect the user to the index page.
    return redirect("/")


app.route("/book/<isbn>", methods=["GET", "POST"])
@login_required
def book(isbn):
    #search book id using the isbn number.
    selected_book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn})
    #save as a variable.
    bookid = selected_book.fetchone()
    #read API key from goodreads.
    key = os.getenv("GOODREADS_KEY")
    #getting the api from the website goodreads.com

    response = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
    json_response = response.json()
    #pass json response to bookinfo.
    json_data = json_response['books'][0]

    query = db.execute("SELECT users.id, users.username, books.title, reviews.rating, reviews.review FROM reviews JOIN books ON reviews.isbn_book = books.isbn JOIN users ON reviews.id = users.id",
                        {"isbn": isbn})

    reviews = review_query.fetchall()

    user_review = False

    for review in reviews:
        print(review["review"])
        if review["id"] == session["user_id"]:
            user_review = True
            print(user_review)
    if request.method == "POST":
        if not user_review:
            current = session["user_id"]
            review = request.form.get("review")
            book_rating = request.form.get("rating")

            db.execute("INSERT INTO reviews(review, rating, id, isbn_book) VALUES (:review, :rating, :id, :isbn_book)",
                    {"review":review, "rating":rating, "id":session["user_id"], "isbn_book": isbn})
            db.commit()

    return render_template("book.html", bookid=bookid, json_data=json_data, reviews=reviews, user_review=user_review)


@app.route("/api/<string:isbn>", methods=["GET"])
@login_required
def api(isbn):

    sql_string = "SELECT * FROM books WHERE isbn = :isbn"

    #fetch the book details from query.
    query = db.execute(sql_string, {"isbn": isbn})
    selected_book = query.fetchone()
    if query.rowcount != 1:
        #return unprocessable entity error.
        return jsonify({"success": "False"}), 422

    review_count = db.execute("SELECT COUNT(*) FROM reviews WHERE isbn_book = :isbn", {"isbn": isbn}).first()
    average = db.execute("SELECT ROUND(AVG(rating::DECIMAL),2) FROM reviews WHERE isbn_book = :isbn", {"isbn": isbn}).first()

    if average is not None:
        average_rating = average[0]
    else:
        average_rating = 0

    return jsonify("title": book_in_db["title"],
                    "author": book_in_db["author"],
                    "year": book_in_db["year"],
                    "isbn": book_in_db["isbn"],
                    "review_count": review_count[0],
                    "average_rating": average_rating
                    })
