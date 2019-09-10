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


app.route("/book/<isbn>/", methods=["POST", "GET"])
@login_required
def book(isbn):
    #search book_id using the isbn number.
    user_id = db.execute("SELECT id FROM public.users WHERE username = :username", {"username": session["user_id"]}).fetchone()[0]

    # Get the book details
    book = db.execute("SELECT * FROM public.book WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book is None:
        flash("This book is not in our system.")
        return redirect(url_for('index'))

    else: # Get the book statistics from GoodreadsAPI and database
        review_statistics = GoodreadsAPI.review_data_isbn(isbn)

        if db.execute("SELECT rating FROM public.reviews WHERE isbn_book = :isbn", {"isbn": isbn}).rowcount == 0:
            average_score = 0
            review_count = 0
        else:
            review_count = db.execute("SELECT COUNT(rating) FROM public.reviews WHERE isbn_book = :isbn", {"isbn": isbn}).fetchone()[0]

            average_score = db.execute("SELECT AVG(rating) FROM public.reviews WHERE isbn_book = :isbn", {"isbn": isbn}).fetchone()[0]

    # Show all the user reviews
    reviews = db.execute("SELECT username, review, rating FROM public.users FULL OUTER JOIN public.reviews ON public.user.id = public.reviews.username_id WHERE isbn_book = :isbn", {"isbn": isbn})

    # Check if user has already added a # REVIEW:
    cur = db.execute("SELECT * FROM public.reviews WHERE (username_id = :user_id) AND (isbn_book = :isbn)", {"user_id": user_id, "isbn": isbn})

    if cur.rowcount > 0:
        reviewed = True
        rating = cur.fetchone()[3]

    else:
        reviewed = False
        rating = None

    # Add review
    if request.method == "POST":
        rating = int(request.form.get("rating"))
        review = request.form.get("review")

        #check for review rating
        if rating > 5 or rating < 1:
            flash("Please try again later.")
            return redirect(url_for('book', isbn=isbn))

        if db.execute("SELECT * FROM public.reviews WHERE (username_id = :user_id) AND (isbn_book = :isbn)", {"user_id": user_id, "isbn": isbn}).rowcount > 0:
            flash("It seems you've already reviewed this book.")

        else:
            db.execute("INSERT INTO public.reviews (username_id, isbn_book, review, rating) VALUES (:user_id, :book_isbn, :review, :rating)", {"user_id": user_id, "book_isbn": isbn, "review": review, "rating": rating})

            db.commit()

            flash("Review added successfully")
            return redirect(url_for('book', isbn=isbn))

    return render_template("book.html", book=book, reviewed=reviewed, rating=rating, reviews=reviews, review_statistics=review_statistics, review_count=review_count, average_score=str(round(average_score,2)), user=session.get('current_user'))


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
        review_count = db.execute("SELECT COUNT(rating) FROM public.reviews WHERE isbn_book = :isbn", {"isbn": isbn}).fetchone()[0]

        average_rating = db.execute("SELECT AVG(rating) FROM public.reviews WHERE isbn_book = :isbn", {"isbn": isbn}).fetchone()[0]

    return jsonify({
            "title": selected_book.title,
            "author": selected_book.author,
            "year": selected_book.year,
            "isbn": selected_book.isbn,
            "review_count": str(review_count),
            "average_rating": str(round(average_score,2))
    })
