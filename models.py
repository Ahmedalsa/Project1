from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

#defining a python class that has the attributes of the database
class Book(db.Model):
    __tablename__ = "books" # links with the table in our database
    isbn = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)

class Reviews(db.Model):
    __tablename__= "reviews"
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey("users.id"))
    book = db.Column(db.String, db.ForeignKey("books.sbn"))
    rating= db.Column(db.Integer)
    comment=db.Column(db.String)
