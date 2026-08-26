from flask import Flask, render_template, redirect, request, session, url_for, flash
import os
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from blueprints.auth.routes import auth_bp
from utils import logged_in

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv('SECRETE_KEY')

app.register_blueprint(auth_bp)

@app.route('/', methods = ['GET'])
@logged_in
def index():
    return render_template('projects/index.html')

if __name__ == '__main__':
    app.run(debug=True)