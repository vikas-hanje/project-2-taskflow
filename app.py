from flask import Flask, render_template
from utils import logged_in
from config import SECRET_KEY
# import blueprints
from blueprints.auth.routes import auth_bp
from blueprints.projects.routes import project_bp
from blueprints.tasks.routes import tasks_bp
from blueprints.api.routes import api_bp

app = Flask(__name__)

app.secret_key = SECRET_KEY

# register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(project_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(api_bp)


@app.route('/', methods = ['GET'])
@logged_in
def index():
    return render_template('projects/index.html')

if __name__ == '__main__':
    app.run(debug=True)
