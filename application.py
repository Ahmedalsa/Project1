import os, json

from flask import Flask, session, render_template, request, redirect, url_for, jsonify, flash, g
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

# Read API key from env variable
KEY = os.getenv("GOODREADS_KEY")


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


@app.route("/book/<isbn>", methods=['GET','POST'])
@login_required
def book(isbn):

    current_user = session.get('user_id')
    #if request.method=="GET":
    if request.method=="GET":
        b_id= db.execute("SELECT isbn, title, author, year FROM books WHERE isbn= :isbn",{"isbn":isbn})
        if b_id.rowcount==0:
            return render_template("error.html", message="No Book Match")
        bookId = b_id.fetchall()

        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key":KEY, "isbns":isbn})
        data = res.json()

        average_rating=data['books'][0]['average_rating']
        rating_count = data['books'][0]['work_ratings_count']


        return render_template("book.html", bookId=bookId, average_rating=average_rating, rating_count=rating_count)

    if request.method=="POST":
        id = db.execute("SELECT id FROM users WHERE username =:username",{"username":current_user}).fetchone()
        id = id[0]
        b_id2= db.execute("SELECT isbn, title, author, year FROM books WHERE isbn= :isbn",{"isbn":isbn})
        if b_id2.rowcount==0:
            return render_template("error.html", message="No Book Match")
        bookId = b_id2.fetchone()
        bookId = bookId[0]
        rating = request.form.get("rating")
        comment = request.form.get("comment")
        check=db.execute("SELECT * FROM reviews WHERE user_id =:user_id AND book_id=:book_id", {"user_id":current_user, "book_id" :bookId})
        if check.rowcount>=1:
            flash('Review already submitted')
            return redirect("/book/" + isbn)
        else:
            db.execute("INSERT INTO reviews (id, user_id, book_id, rating, comment) VALUES (:id, :user_id, :book_id,:rating, :comment)",{"id": id, "user_id": current_user, "book_id": bookId, "comment": comment, "rating": rating})
            db.commit()
            flash("your review is submitted")
            return redirect("/book/" +isbn)


@app.route("/api/<string:isbn>")
@login_required
def api(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return jsonify({"error": "Book not found"}), 404

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key":KEY, "isbns":isbn})
    data = res.json()

    average_rating=data['books'][0]['average_rating']
    rating_count = data['books'][0]['work_ratings_count']

    return jsonify({
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "isbn": book.isbn,
            "review_count": str(rating_count),
            "average_score": str(average_rating)
    })
