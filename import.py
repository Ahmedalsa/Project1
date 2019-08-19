
#load  csv libraries
import csv
import os
#load psycopg2 libraries
import psycopg2

#load sqlalchemy libraries
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

#set up connection to the database

connection = create_engine('postgres://jrmqlumszscete:7a7a8b6d39ca502a1f037d56b887670a944ef7eeac3773d84447a0fa4f1f93b1@ec2-107-20-198-176.compute-1.amazonaws.com:5432/d7e9ku4tq19i8e')
sql = scoped_session(sessionmaker(bind=connection))

def main():
    sql.execute("""CREATE TABLE books (
                   id       SERIAL PRIMARY KEY,
                   isbn VARCHAR(50)   NOT NULL,
                   title VARCHAR(50)  NOT NULL,
                   author VARCHAR(50) NOT NULL,
                   year INT           NOT NULL
                  );""")
    f = open("books.csv")
    reader = csv.reader(f)
    next(reader, None)
    for isbn, title, author, year in reader:
        sql.execute(
            "INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
            {"isbn": isbn, "title": title, "author": author, "year": year}
        )
    sql.commit()

if __name__ == "__main__":
    main()
