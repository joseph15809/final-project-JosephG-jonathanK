import os
import mysql.connector
import pandas as pd
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE")
        )
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None


def create_tables():
    connection = get_db_connection()
    if not connection:
        return
    
    cursor = connection.cursor()
   
    # cursor.execute("DROP TABLE IF EXISTS temperature")
    # cursor.execute("DROP TABLE IF EXISTS humidity")
    # cursor.execute("DROP TABLE IF EXISTS light")
     # user table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user(
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL,
        password VARCHAR(100) NOT NULL,
        location VARCHAR(100) NOT NULL
        )
    """)

    # device table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS device(
            device_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            user_id INT NOT NULL,
            timestamp DATETIME NOT NULL
        )
    """)

    # wardrobe table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wardrobe(
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        user_id INT NOT NULL,
        type VARCHAR(100) NOT NULL,
        color VARCHAR(100) NOT NULL,
        size VARCHAR(100) NOT NULL
        )
    """)

    connection.commit()
    cursor.close()
    connection.close()
