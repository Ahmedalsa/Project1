
#load  csv libraries
import csv
#load psycopg2 libraries
import psycopg2

#set up connection to the database

conn = psycopg2.connect("dbname='d7e9ku4tq19i8e' user='jrmqlumszscete' host='ec2-107-20-198-176.compute-1.amazonaws.com' password='7a7a8b6d39ca502a1f037d56b887670a944ef7eeac3773d84447a0fa4f1f93b1'")


#use cursor object to execute commands in psycopg2

cursor = conn.cursor()

cursor.execute('''CREATE TABLE data
           (ID INT PRIMARY KEY        NOT NULL,
           isbn CHAR(50) ,
           title CHAR(50) ,
           author CHAR(50) ,
           year INT
           );''')

reader = csv.readr(open('books.csv', 'r'))

for i, row in enumerate(reader):
    print(i, row)
    if i == 0: continue

    cur.execute('''
        INSERT INTO "data" (
            "isbn", "title", "author", "year"
        ) values %s''', [tuple(row)]
    )
    conn.commit()
    cur.close()
