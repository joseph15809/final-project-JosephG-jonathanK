import os
import time
import mysql.connector
import pandas as pd
from mysql.connector import Error
from dotenv import load_dotenv
import logging
from typing import Optional

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class DatabaseConnectionError(Exception):
    """Custom exception for database connection failures."""
    pass


def get_db_connection(
    max_retries: int = 12,  # 12 retries = 1 minute total (12 * 5 seconds)
    retry_delay: int = 5,  # 5 seconds between retries
) -> mysql.connector.MySQLConnection:
    """Create database connection with retry mechanism."""
    connection: Optional[mysql.connector.MySQLConnection] = None
    attempt = 1
    last_error = None

    while attempt <= max_retries:
        try:
            connection = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST"),
                port=int(os.getenv('MYSQL_PORT')),
                user=os.getenv("MYSQL_USER"),
                password=os.getenv("MYSQL_PASSWORD"),
                database=os.getenv("MYSQL_DATABASE"),
                ssl_ca=os.getenv('MYSQL_SSL_CA'),  # Path to CA certificate file
                ssl_verify_identity=True
            )

            # Test the connection
            connection.ping(reconnect=True, attempts=1, delay=0)
            logger.info("Database connection established successfully")
            return connection

        except Error as err:
            last_error = err
            logger.warning(
                f"Connection attempt {attempt}/{max_retries} failed: {err}. "
                f"Retrying in {retry_delay} seconds..."
            )

            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

            if attempt == max_retries:
                break

            time.sleep(retry_delay)
            attempt += 1

    raise DatabaseConnectionError(
        f"Failed to connect to database after {max_retries} attempts. "
        f"Last error: {last_error}"
    )
    

async def setup_database():
    """Creates users, devices, wardrobe, and sessions tables."""

    # Define table schemas
    table_schemas = {
        "users": """
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(100) NOT NULL,
                location VARCHAR(100) NOT NULL
            )
        """,
        "devices": """
            CREATE TABLE IF NOT EXISTS devices (
                device_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) DEFAULT NULL,
                user_id INT DEFAULT NULL,
                mac_address VARCHAR(30) UNIQUE NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """,
        "temperature": """
            CREATE TABLE IF NOT EXISTS temperature(
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT DEFAULT NULL,
                mac_address VARCHAR(20) NOT NULL,
                value FLOAT NOT NULL,
                unit VARCHAR(10) NOT NULL,
                timestamp DATETIME NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY(mac_address) REFERENCES devices(mac_address) ON DELETE CASCADE
            )
        """,
        "wardrobe": """
            CREATE TABLE IF NOT EXISTS wardrobe (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                user_id INT NOT NULL,
                type VARCHAR(100) NOT NULL,
                color VARCHAR(100) NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """,
        "sessions": """
            CREATE TABLE IF NOT EXISTS sessions (
                id VARCHAR(36) PRIMARY KEY,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """,
    }

    # Connect to the database
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        if not connection:
            raise Exception("Database connection failed")

        cursor = connection.cursor()

        # Create tables
        for table_name, table_query in table_schemas.items():
            cursor.execute(table_query)
            logger.info(f"Table '{table_name}' checked/created successfully.")

        connection.commit()  # Commit all changes

    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise  # Rethrow exception to avoid silent failure

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            logger.info("Database connection closed")


async def add_user(name: str, email: str, password: str, location: str) -> int:
    """Insert a new user into the database and return the user ID."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO users (name, email, password, location) VALUES (%s, %s, %s, %s)",
            (name, email, password, location)
        )
        connection.commit()

        # Get the user_id of the newly created user
        cursor.execute("SELECT LAST_INSERT_ID()")
        user_id = cursor.fetchone()[0]

        return user_id  # Return the newly created user ID

    except Exception as e:
        if connection:
            connection.rollback()  # Rollback on failure
        raise Exception(f"Failed to insert user: {e}")

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()       


async def add_clothes(name: str, user_id: int, type: str, color: str):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO wardrobe (name, user_id, type, color) VALUES (%s, %s, %s, %s)",
            (name, user_id, type, color)
        )
        connection.commit()

    except Exception as e:
        if connection:
            connection.rollback()  # Rollback on failure
        raise Exception(f"Failed to insert item: {e}")

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def remove_clothes(clothes_id: int, user_id: int):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM wardrobe WHERE id=%s AND user_id=%s",
            (clothes_id, user_id)
        )
        connection.commit()

    except Exception as e:
        if connection:
            connection.rollback()  # Rollback on failure
        raise Exception(f"Failed to delete item: {e}")

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()              


async def get_user_clothes(user_id: int):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM wardrobe WHERE user_id = %s", (user_id,))
        data = cursor.fetchall()
        wardrobe_data = []
        for item in data:
            wardrobe_data.append({
                "id":item[0],
                "name": item[1],
                "type": item[3],
                "color": item[4]
            })

        return wardrobe_data
    except Exception as e:
        connection.rollback()
        raise Exception(f"Failed to get clothes: {e}")
    finally:
        cursor.close()
        connection.close()   


async def update_clothes(clothes_id, name, clothes_type, color):
    "Updates users clothes info"
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query =  "UPDATE wardrobe SET name = %s, type = %s, color = %s WHERE id = %s"
        cursor.execute(query, (name, clothes_type, color, clothes_id))
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise Exception(f"Failed to update clothes: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def remove_user_device(device_id, mac_address):
    "deletes device from db"
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM devices WHERE device_id=%s AND mac_address=%s",
            (device_id, mac_address)
        )
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise Exception(f"Failed to remove device: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def update_user_device(name, mac_address, device_id):
    "update device info"
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "UPDATE devices SET name = %s, mac_address = %s WHERE device_id = %s"
        cursor.execute(query, (name, mac_address, device_id))
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise Exception(f"Failed to remove device: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close() 


async def get_user_by_email(email: str) -> Optional[dict]:
    """Retrieve user from database by email."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def get_user_by_id(user_id: int) -> Optional[dict]:
    """
    Retrieve user from database by ID.

    Args:
        user_id: The ID of the user to retrieve

    Returns:
        Optional[dict]: User data if found, None otherwise
    """
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def create_session(user_id: int, session_id: str) -> bool:
    """Create a new session in the database."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO sessions (id, user_id) VALUES (%s, %s)", (session_id, user_id)
        )
        connection.commit()
        return True
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def get_session(session_id: str) -> Optional[dict]:
    """Retrieve session from database."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT *
            FROM sessions s
            WHERE s.id = %s
        """,
            (session_id,),
        )
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def delete_session(session_id: str) -> bool:
    """Delete a session from the database."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
        connection.commit()
        return True
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def add_temperature(mac_address: str, value: float, unit: str, timestamp: str) -> int:
    """Insert a new user into the database and return the user ID."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO temperature (mac_address, value, unit, timestamp) VALUES (%s, %s, %s, %s)",
            (mac_address, value, unit, timestamp)
        )
        connection.commit()

        # Get the user_id of the newly created user
        cursor.execute("SELECT LAST_INSERT_ID()")
        user_id = cursor.fetchone()[0]

        return user_id  # Return the newly created user ID

    except Exception as e:
        if connection:
            connection.rollback()  # Rollback on failure
        raise Exception(f"Failed to insert user: {e}")

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()   


async def update_user(user_id, name, location, new_hashed_password=None):
    """Updates users info"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        if new_hashed_password:
            query = "UPDATE users SET name = %s, location = %s, password = %s WHERE user_id = %s"
            cursor.execute(query, (name, location, new_hashed_password, user_id))
        else:
            query = "UPDATE users SET name = %s, location = %s WHERE user_id = %s"
            cursor.execute(query, (name, location, user_id))
        connection.commit()
    except Exception as e:
        if connection:
            connection.rollback()
        raise Exception(f"Failed to get user location: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def get_users_location(user_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT location FROM users WHERE user_id = %s", (user_id,))
        return cursor.fetchone()
    
    except Exception as e:
        if connection:
            connection.rollback()
        raise Exception(f"Failed to get user location: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def clear_database():
    """Deletes all data from all tables."""
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE sessions;")
        cursor.execute("TRUNCATE TABLE wardrobe;")
        cursor.execute("TRUNCATE TABLE devices;")
        cursor.execute("TRUNCATE TABLE users;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        connection.commit()
        print("Database cleared successfully.")

    except Exception as e:
        connection.rollback()
        print(f"Failed to clear database: {e}")

    finally:
        cursor.close()
        connection.close()


def delete_all_tables():
    """Deletes all tables from the database."""
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Disable foreign key checks to avoid constraint issues
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

        # Retrieve all table names
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]

        
        print(f"Dropping table: wardrobe")
        cursor.execute(f"DROP TABLE IF EXISTS wardrobe;")

        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        connection.commit()
        print("All tables deleted successfully.")

    except Error as e:
        print(f"Error deleting tables: {e}")
        connection.rollback()

    finally:
        cursor.close()
        connection.close()