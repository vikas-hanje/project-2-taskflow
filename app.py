from flask import Flask, render_template, redirect, request, session, url_for, flash, abort
import os
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from utils import logged_in
# import blueprints
from blueprints.auth.routes import auth_bp
from blueprints.projects.routes import project_bp
from blueprints.tasks.routes import tasks_bp

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv('SECRETE_KEY')

# register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(project_bp)
app.register_blueprint(tasks_bp)


@app.route('/', methods = ['GET'])
@logged_in
def index():
    return render_template('projects/index.html')

if __name__ == '__main__':
    app.run(debug=True)