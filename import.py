
#load  csv libraries
import csv
#load psycopg2 libraries
import psycopg2
import sys
import logging


#set up connection to the database

conn = psycopg2.connect(
           host='ec2-107-20-198-176.compute-1.amazonaws.com',
           database='d7e9ku4tq19i8e',
           user='jrmqlumszscete',
           password='7a7a8b6d39ca502a1f037d56b887670a944ef7eeac3773d84447a0fa4f1f93b1')


#use cursor object to execute commands in psycopg2

cursor = conn.cursor()

reader = csv.reader(open('books.csv', 'r'))


cursor.execute('''CREATE TABLE books
           (id SERIAL PRIMARY KEY,
           isbn CHAR(100) NOT NULL,
           title CHAR(100) NOT NULL,
           author CHAR(100) NOT NULL,
           year INT NOT NULL
           );''')


for line in file:
    my_list = line.split(',')
    string = ''
    for value in my_list:
        string = string + "'" + value + "',"
        sql_string = string[:-1]
    last_query = "INSERT INTO books (isbn, title, author, year) VALUES"+"("+sql_string+");"
    cursor.execute(last_query)
    conn.commit()

        #close the connection
cursor.close()
conn.close()
