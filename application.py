import os

from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


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


@app.route("/")
def index():
    return render_template("signup.html")

@app.route("/signup", method=['POST'])
def signup():
    #Read entered values from new user
    username = request.form['username']
    password = request.form['password']
    return render_template("signup.html")
    #check if entered values  are valid
    if username and password:
        return json.dumps({'html':'<span>All values entered are valid</span>'})
    else:
        return json.dumps({'html':'<span>Please enter required fields</span>'})
        cursor = engine.cursor()


@app.route("/search", method=['POST'])
def search():
    name = request.form.get("username")
    if(name):
        try:
            engine = connection.connect()
            sql_string = "SELECT isbn, title, author FROM books"
            engine.execute(sql_string)
            for row in engine.fetchall():
                print(row)

        except("Could not connect to database.")


    else:
        return render_template("signup.html")


@app.route("/login", method=["GET", "POST"])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error = 'Username or password is incorrect. Please try again.'
        else:
            return redirect(url_for('/'))
    return render_template("login.html", error=error)
