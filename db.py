import mysql.connector
import os
from dotenv import load_dotenv

def connect_DB():
    connection = mysql.connector.connect(
        host = os.getenv("DB_host"),
        user = os.getenv("DB_user"),
        password = os.getenv("DB_password"),
        database = os.getenv("DB_database")
    )
    return connection