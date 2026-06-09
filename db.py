import mysql.connector

def get_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root123",  #  we can change this
        database="placement_db"
    )
    return conn