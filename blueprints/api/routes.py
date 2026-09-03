from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
import jwt
from datetime import datetime, timedelta
from db import connect_DB, get_owned_project
from utils import token_required
from config import JWT_SECRET_KEY
import uuid

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required."}), 400
    
    email = data['email']
    password = data['password']
    
    conn = connect_DB()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("select * from users where email = %s", (email,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            # create token that expires in 1 hr
            payload = {
                'user_id': user['user_id'],
                'exp': datetime.utcnow() + timedelta(hours=1)
            }
            
            token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
            
            return jsonify({"token": token}), 200
        else:
            return jsonify({"error": "Invalid email or password."}), 401
        
    finally:
        cursor.close()
        conn.close()
        
@api_bp.route('/projects', methods=['GET'])
@token_required
def get_projects(current_user_id):
    conn = connect_DB()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # we use current_user_id passed by the decorator, not session
        cursor.execute("SELECT * FROM projects WHERE user_id = %s", (current_user_id,))
        projects = cursor.fetchall()
        
        return jsonify(projects), 200
        
    finally:
        cursor.close()
        conn.close()
        
# create project
@api_bp.route('/projects', methods=['POST'])
@token_required
def create_project(current_user_id):
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({"error": "Project name is required."}), 400
    
    project_id = str(uuid.uuid4())
    
    conn = connect_DB()
    cursor = conn.cursor()
    
    try:
        cursor.execute("insert into projects(project_id, name, user_id) values (%s, %s, %s)", (project_id, data['name'], current_user_id))
        conn.commit()
        return jsonify({"message": "Project created", "project_id": project_id}), 201
    
    finally:
        cursor.close()
        conn.close()

# single project
@api_bp.route('/projects/<string:project_id>', methods=['GET'])
@token_required
def get_project(current_user_id, project_id):
    project = get_owned_project(project_id, current_user_id)
    
    if not project:
        return jsonify({"error": "Project not found."}), 404
    
    return jsonify(project), 200

# update project
@api_bp.route('/projects/<string:project_id>', methods=['PUT'])
@token_required
def update_project(current_user_id, project_id):
    # 1. Verify ownership first
    if not get_owned_project(project_id, current_user_id):
        return jsonify({"error": "Project not found"}), 404
        
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"error": "New project name is required"}), 400

    # 2. Update without needing rowcount hacks, because ownership is already proven
    conn = connect_DB()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "update projects set name = %s where project_id = %s",
            (data['name'], project_id)
        )
        conn.commit()
        return jsonify({"message": "Project updated successfully"}), 200
    finally:
        cursor.close()
        conn.close()

# delete project
@api_bp.route('/projects/<string:project_id>', methods=['DELETE'])
@token_required
def delete_project(current_user_id, project_id):
    # CHANGED: ownership check + delete combined into one atomic query, matching
    # the pattern already used by delete_task's Layer 2 check and by the HTML
    # project.delete() route. Avoids a separate get_owned_project() call (and the
    # extra DB connection it opens), and removes the small gap between "verify"
    # and "act" that exists when they're two separate round-trips.
    conn = connect_DB()
    cursor = conn.cursor()
    try:
        cursor.execute("delete from projects where project_id = %s and user_id = %s", (project_id, current_user_id))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Project not found"}), 404

        return jsonify({"message": "Project deleted successfully"}), 200
    finally:
        cursor.close()
        conn.close()
        
# GET: List all tasks for a project
@api_bp.route('/projects/<string:project_id>/tasks', methods=['GET'])
@token_required
def get_tasks(current_user_id, project_id):
    # LAYER 1: Verify the project belongs to the user
    if not get_owned_project(project_id, current_user_id):
        return jsonify({"error": "Project not found"}), 404

    conn = connect_DB()
    cursor = conn.cursor(dictionary=True)
    try:
        # We don't need a user_id check here; the project check already proved authorization
        cursor.execute("SELECT * FROM tasks WHERE project_id = %s ORDER BY created_at DESC", (project_id,))
        tasks = cursor.fetchall()
        return jsonify(tasks), 200
    finally:
        cursor.close()
        conn.close()


# POST: Create a new task
@api_bp.route('/projects/<string:project_id>/tasks', methods=['POST'])
@token_required
def create_task(current_user_id, project_id):
    if not get_owned_project(project_id, current_user_id):
        return jsonify({"error": "Project not found"}), 404

    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({"error": "Task title is required"}), 400

    task_id = str(uuid.uuid4())
    status = data.get('status', 'To Do')
    priority = data.get('priority', 'Medium')
    due_date = data.get('due_date') # Can be None

    conn = connect_DB()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO tasks (task_id, project_id, title, status, priority, due_date) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (task_id, project_id, data['title'], status, priority, due_date)
        )
        conn.commit()
        return jsonify({"message": "Task created", "task_id": task_id}), 201
    finally:
        cursor.close()
        conn.close()


# GET: Fetch a single task
@api_bp.route('/projects/<string:project_id>/tasks/<string:task_id>', methods=['GET'])
@token_required
def get_task(current_user_id, project_id, task_id):
    if not get_owned_project(project_id, current_user_id):
        return jsonify({"error": "Project not found"}), 404

    conn = connect_DB()
    cursor = conn.cursor(dictionary=True)
    try:
        # LAYER 2: Ensure the task actually belongs to this specific project
        cursor.execute("SELECT * FROM tasks WHERE task_id = %s AND project_id = %s", (task_id, project_id))
        task = cursor.fetchone()
        
        if not task:
            return jsonify({"error": "Task not found"}), 404
            
        return jsonify(task), 200
    finally:
        cursor.close()
        conn.close()


# PUT: Update a task
@api_bp.route('/projects/<string:project_id>/tasks/<string:task_id>', methods=['PUT'])
@token_required
def update_task(current_user_id, project_id, task_id):
    if not get_owned_project(project_id, current_user_id):
        return jsonify({"error": "Project not found"}), 404

    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({"error": "Task title is required"}), 400

    conn = connect_DB()
    cursor = conn.cursor(dictionary=True)
    try:
        # FIX: fetch the existing task first, for two reasons:
        # 1. Existence (Layer 2) is now proven BEFORE the UPDATE runs, so we no longer
        #    rely on rowcount == 0 afterward -- which was ambiguous (a real, owned task
        #    with no actual data changes also reports rowcount 0, and would have been
        #    incorrectly reported as "not found").
        # 2. status/priority are NOT NULL columns. data.get(...) returns None for any
        #    field the client's JSON body omits (a legitimate partial update). Without
        #    a fallback, that None would get written straight into a NOT NULL column
        #    and MySQL would reject the query outright, crashing this route with an
        #    unhandled 500 instead of a clean response.
        cursor.execute("SELECT * FROM tasks WHERE task_id = %s AND project_id = %s", (task_id, project_id))
        existing_task = cursor.fetchone()

        if not existing_task:
            return jsonify({"error": "Task not found"}), 404

        title = data['title']
        status = data.get('status', existing_task['status'])
        priority = data.get('priority', existing_task['priority'])
        due_date = data.get('due_date', existing_task['due_date'])

        cursor.execute(
            """UPDATE tasks 
               SET title = %s, status = %s, priority = %s, due_date = %s 
               WHERE task_id = %s AND project_id = %s""",
            (title, status, priority, due_date, task_id, project_id)
        )
        conn.commit()

        return jsonify({"message": "Task updated successfully"}), 200
    finally:
        cursor.close()
        conn.close()


# DELETE: delete a task
@api_bp.route('/projects/<string:project_id>/tasks/<string:task_id>', methods=['DELETE'])
@token_required
def delete_task(current_user_id, project_id, task_id):
    if not get_owned_project(project_id, current_user_id):
        return jsonify({"error": "Project not found"}), 404

    conn = connect_DB()
    cursor = conn.cursor()
    try:
        # Again, the WHERE clause safely targets only a task within this project
        cursor.execute("DELETE FROM tasks WHERE task_id = %s AND project_id = %s", (task_id, project_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Task not found"}), 404
            
        return jsonify({"message": "Task deleted successfully"}), 200
    finally:
        cursor.close()
        conn.close()