import mysql.connector

def get_connection():
    conn = mysql.connector.connect(
        host="127.0.0.1",  
        user="root",
        password="your_password_here",  # Replace with your actual database password
        database="your_database"
    )
    return conn
