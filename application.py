import os, json

from flask import Flask, session, render_template, request, redirect, url_for, jsonify, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests, re
from jinja2 import Template
from decorators import login_required
from goodreads import book, review



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


app.route("/book/<string:isbns>/", methods=["POST", "GET"])
@login_required
def book(isbns):
    #read API key from goodreads.
    key = os.getenv("GOODREADS_KEY")
    #search book_id using the isbn number.
    res = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    #import api from Goodreads.com
    r = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
    if r.status_code != 200:
      raise ValueError
    reviews_count=r.json()["books"][0]["reviews_count"]
    average_rating=r.json()["books"][0]["average_rating"]
    if request.method == "POST":
        username = session.get("username")
        review = request.form.get("comment")
        rating = request.form.get("rating")
        date = datetime.now()
        #get user_id to get # REVIEW
        user_id = db.execute("SELECT id FROM users WHERE username = :username",{"username":username}).fetchone()[0]

        db.execute("INSERT INTO reviews (user_id, username, review, rating, date) VALUES (:user_id, :username, :review, :rating, :date)", {"user_id": user_id, "date":date, "review":review, "rating":rating, "username":username})

        db.commit()


    return render_template("book.html", reviews_count = reviews_count, average_rating = average_rating)


@app.route("/api/<string:isbn>", methods=["GET"])
@login_required
def api(isbn):
    #read API key from goodreads.
    key = os.getenv("GOODREADS_KEY")
    #getting the api from the website goodreads.com
    response = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
    print(response.json())



    sql_string = "SELECT * FROM books WHERE isbn = :isbn"

    #fetch the book details from query.
    query = db.execute(sql_string, {"isbn": isbn})
    selected_book = query.fetchone()
    if query.rowcount != 1:
        #return unprocessable entity error.
        return jsonify({"success": "False"}), 422

    if db.execute("SELECT rating FROM public.reviews WHERE isbn_book = :isbn", {"isbn": isbn}).rowcount == 0:
        average_score = 0
        review_count = 0
    else:
        review_count = db.execute("SELECT COUNT(rating) FROM public.reviews WHERE isbn_book = :isbn", {"isbn": isbns}).fetchone()[0]

        average_rating = db.execute("SELECT AVG(rating) FROM public.reviews WHERE isbn_book = :isbn", {"isbn": isbns}).fetchone()[0]

    return jsonify({
            "title": selected_book.title,
            "author": selected_book.author,
            "year": selected_book.year,
            "isbn": selected_book.isbn,
            "review_count": str(review_count),
            "average_rating": str(round(average_score,2))
    })
