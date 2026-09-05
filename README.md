# TaskFlow

TaskFlow is a multi-user project and task manager. Users register an account, create projects, and track tasks within each project. It was built as a learning project to practice a full-stack Python and Flask application with session-based web authentication, a token-based REST API, and a MySQL database.

## Features

- User registration and login with hashed passwords
- Projects and tasks, scoped so each user only ever sees their own data
- Full create, read, update, and delete for both projects and tasks through the web interface
- A REST API under /api, authenticated separately through JWT bearer tokens
- Flash messages for feedback on actions, dismissing automatically after a few seconds

## Tech stack

- Python and Flask
- MySQL
- HTML and CSS, no frontend framework or build step
- PyJWT for API authentication
- python-dotenv for configuration

## Project structure

- app.py creates the Flask app and registers each blueprint
- blueprints holds the auth, projects, tasks, and api routes, each as its own blueprint
- templates holds the Jinja2 templates for the web interface
- static/css holds the stylesheet
- db.py handles the database connection and a couple of shared query helpers
- config.py loads settings from environment variables
- schema.sql defines the database schema

## Getting Started

Prerequisites: Python 3, a running MySQL server, and pip.

- Clone this repository to your local machine.
- Create and activate a virtual environment:

        python -m venv env
        source env/bin/activate 

    On Windows use:

        env\Scripts\activate

- Install the required dependencies:

        pip install -r requirements.txt

- Create a .env file in the root directory and add the following variables.

      SECRETE_KEY= # a secret key for signing Flask sessions
      JWT_SECRETE_KEY= # a separate secret key for signing API tokens
      DB_host= # the database host, usually localhost
      DB_user= # the MySQL username
      DB_password= # the MySQL password
      DB_database= # set to Taskflow_DB

- Set up your database by running the queries found in schema.sql.
- Start the Flask server:

        python app.py
        
- Open your browser and navigate to (http://127.0.0.1:5000).

## Using the API

The API lives under /api and is separate from the web interface. It does not use session cookies. Log in through POST /api/login with an email and password to receive a JWT token, then send that token on every following request as an Authorization header in the form Bearer followed by the token.

Main endpoints:

- POST /api/login
- GET /api/projects
- POST /api/projects
- GET /api/projects/project_id
- PUT /api/projects/project_id
- DELETE /api/projects/project_id
- POST /api/projects/project_id/tasks
- GET /api/projects/project_id/tasks
- GET /api/projects/project_id/tasks/task_id
- PUT /api/projects/project_id/tasks/task_id
- DELETE /api/projects/project_id/tasks/task_id