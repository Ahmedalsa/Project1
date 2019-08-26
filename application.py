import os

from flask import Flask, session, render_template, request, redirect, url_for, login_required, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("postgres://jrmqlumszscete:7a7a8b6d39ca502a1f037d56b887670a944ef7eeac3773d84447a0fa4f1f93b1@ec2-107-20-198-176.compute-1.amazonaws.com:5432/d7e9ku4tq19i8e"))
db = scoped_session(sessionmaker(bind=engine))

class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(55))
    password = db.Column(db.String(55))


@app.route("/")
def index():
    return render_template("signup.html")

@app.route("/signup", method=['GET', 'POST'])
def signup():
    if request.method == 'POST':
            #Read entered values from new user
        username = request.form['username']
        password = request.form['password']
        #check if entered values  are valid
        register = user(username = username, password = password)
        db.add(register)
        db.commit()

        return redirect(url_for('/login'))

    return render_template("signup.html")



@app.route("/search", method=["GET", "POST"])
@login_required
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


@app.route("/login", method=["GET", "POST"])
@login_required
def login():
    if request.method == 'POST':

        session['username'] = request.form['username']
        session['email'] = request.form['email']
        session['id'] = request.form['id']
        return redirect(url_for('index'))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():

    # Forget any user id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


app.route("/book", method["GET", "POST"])
@login_required
def book(id):
    #getting the api from the website goodreads.
    isbn = db.execute("SELECT isbn FROM books WHERE id = :id", {"id": id}).fetchone()
    response = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "odIyXgoUO32BFSKOfJwaEA", "isbns": "9781632168146"})



@app.route("/api/<string:isbn>", method["GET", "POST"])
@login_required
def api(isbn):
    if request.method == 'GET':
        url = ''

        response = requests.get(url, )
        print(response.json())
