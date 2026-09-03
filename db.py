import mysql.connector
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE


def connect_DB():
    connection = mysql.connector.connect(
        host = DB_HOST,
        user = DB_USER,
        password = DB_PASSWORD,
        database = DB_DATABASE
    )
    return connection

def get_owned_project(project_id, user_id):
    conn = connect_DB()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("select * from projects where project_id = %s and user_id = %s", (project_id, user_id))
        return cursor.fetchone()
    
    finally:
        cursor.close()
        conn.close()
