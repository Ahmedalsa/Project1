import os, json

from flask import Flask, session, render_template, request, redirect, url_for, jsonify, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
from jinja2 import Template
from decorators import login_required


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


app.route("/book/<isbn>/", methods=["GET", "POST"])
@login_required
def book(isbn):
    if request.method == "POST":
        current = session["user_id"]
        comment = request.form.get("comment")
        book_rating = request.form.get("rating")
        #search book id using the isbn number.
        selected_book = db.execute("SELECT id FROM books WHERE isbn = :isbn", {"isbn": isbn})
        #save as a variable.
        bookid = selected_book.fetchone()
        bookid = bookid[0]

        book_reviews = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id",
         {"user_id": current, "book_id": bookid})

        if book_reviews.rowcount == 1:
             flash('Cannot Add more than 1 review', 'warning')
             return redirect("/book/" + isbn)

        #to be save in the database.
        rating = int(rating)

        db.execute("INSERT INTO reviews (user_id, book_id, review, rating) VALUES (:user_id, :book_id, :review, :rating)",
                {"user_id": current, "book_id": bookid, "comment": comment, "rating": rating})
        db.commit()

        flash('submitted', 'info')
        return redirect("/book/" + isbn)

    else:
        selected_isbn = db.execute("SELECT isbn, title, author, year FROM books WHERE isbn = :isbn", {"isbn": isbn})
        bookinfo = selected_isbn.fetchall()

        #read API key from goodreads.
        key = os.getenv("GOODREADS_KEY")
        #getting the api from the website goodreads.com
        response = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
        json_response = response.json()
        #pass json response to bookinfo.
        json_response = json_response['books'][0]
        bookinfo.append(json_response)

        #Searhing through books by id through isbns.
        selected_id = db.execute("SELECT id FROM books WHERE isbn = :isbn", {"isbn": isbn})

        #save user's book as a variable.
        user_book = selected_id.fetchone()
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
    return render_template("book.html", bookinfo=bookinfo, reviews=reviews)


@app.route("/api/<string:isbn>", methods=["GET", "POST"])
@login_required
def api(isbn):

    sql_string = "SELECT users.username, comment, rating, \
                        to_char(time, 'DD Mon YY - HH24:MI:SS') as time \
                        FROM users \
                        INNER JOIN reviews \
                        ON users.id = reviews.user_id \
                        WHERE book_id = :book \
                        ORDER BY time"

    selected_book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if selected_book is None:
        #return unprocessable entity error.
        return jsonify({"success": "False"}), 422


    return jsonify({
    "title": selected_book.title,
    "author": selected_book.author,
    "year": selected_book.year,
    "isbn": selected_book.isbn,
    "review_count": books_list['work_ratings_count'],
    "average_score": books_list['average_rating']
})
