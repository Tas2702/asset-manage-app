import sqlite3
import os
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'asset_manage_app.db')
SCHEMA = os.path.join(BASE_DIR, 'schema.sql')

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
 
    connection.row_factory = sqlite3.Row
 
    connection.execute("PRAGMA foreign_keys = ON")
 
    return connection

def init_db():
    connection = get_db_connection()
    with open(SCHEMA, 'r') as schema_file:
        connection.executescript(schema_file.read())

    _hash_seed_passwords(connection)
 
    connection.commit()
    connection.close()
 
    print("Database initialised successfully.")

def _hash_seed_passwords(connection):
    # Fetch all users from the database
    users = connection.execute("SELECT user_id, password FROM users").fetchall()
 
    for user in users:
        plain_password = user['password']
 
        # Only hash the password if it hasn't been hashed already
        # Hashed passwords begin with 'pbkdf2' or 'scrypt'
        already_hashed = (
            plain_password.startswith('pbkdf2') or
            plain_password.startswith('scrypt')
        )
 
        if not already_hashed:
            hashed_password = generate_password_hash(plain_password)
 
            connection.execute(
                "UPDATE users SET password = ? WHERE user_id = ?",
                (hashed_password, user['user_id'])
            )
 
    print("Seed passwords hashed successfully.")
 