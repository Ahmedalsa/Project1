
#load  csv libraries
import csv
import os
#load psycopg2 libraries
import psycopg2

#load sqlalchemy libraries
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

#set up connection to the database

connection = create_engine(os.getenv("DATABASE_URL"))
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
