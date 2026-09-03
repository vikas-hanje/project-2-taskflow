import os
from dotenv import load_dotenv

load_dotenv()

# Flask session-signing key (used for cookie-based browser sessions)
SECRET_KEY = os.getenv('SECRETE_KEY')

# JWT-signing key for the API's token-based auth -- deliberately a separate value
# from SECRET_KEY above, since sessions and JWTs are two independent trust mechanisms
JWT_SECRET_KEY = os.getenv('JWT_SECRETE_KEY')

# Database connection settings
DB_HOST = os.getenv('DB_host')
DB_USER = os.getenv('DB_user')
DB_PASSWORD = os.getenv('DB_password')
DB_DATABASE = os.getenv('DB_database')
