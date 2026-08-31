from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
import uuid
from db import connect_DB
from utils import logged_in

tasks_bp = Blueprint('task', __name__)

@tasks_bp.route('/projects/<string:project_id>/tasks', methods=['POST'])
@logged_in
def index(project_id):
    user_id = session['user_id']
    
    conn = connect_DB()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("select * from projects where project_id = %s and user_id = %s", (project_id, user_id))
        project = cursor.fetchone()
        
        if not project:
            abort(404)
            
        title = request.form.get('title')
        status = request.form.get('status')
        priority = request.form.get('priority')
        due_date = request.form.get('due_date') or None
        
        if not title:
            flash("Task title is required.")
            return redirect(url_for('project.details', project_id=project_id))
        
        task_id = str(uuid.uuid4())
        
        cursor.execute(
            "insert into tasks (task_id, project_id, title, status, priority, due_date) values (%s, %s, %s, %s, %s, %s)",
            (task_id, project_id, title, status, priority, due_date)
        )
        conn.commit()
        
        flash("Task added successfully.")
        
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('project.details', project_id=project_id))


@tasks_bp.route('/projects/<string:project_id>/tasks/<string:task_id>/edit', methods=['GET', 'POST'])
@logged_in
def edit(project_id, task_id):
    user_id = session['user_id']
    conn = connect_DB()
    cursor = conn.cursor(dictionary=True)  # FIX: added dictionary=True
    
    try:
        cursor.execute("SELECT project_id FROM projects WHERE project_id = %s AND user_id = %s", (project_id, user_id))
        if not cursor.fetchone():
            abort(404)

        cursor.execute("SELECT * FROM tasks WHERE task_id = %s AND project_id = %s", (task_id, project_id))
        task = cursor.fetchone()
        if not task:
            abort(404)
            
        if request.method == 'POST':
            title = request.form.get('title')
            status = request.form.get('status')
            priority = request.form.get('priority')
            due_date = request.form.get('due_date') or None
            
            if not title:
                flash("Task title is required.")
                return redirect(url_for('task.edit', project_id=project_id, task_id=task_id))
            
            # FIX: "task_is" -> "task_id" -- SQL column-name typo, threw a DB error on every save
            cursor.execute(
                "update tasks set title = %s, status = %s, priority = %s, due_date = %s where task_id = %s and project_id = %s",
                (title, status, priority, due_date, task_id, project_id)
            )
            conn.commit()
            
            flash("Task updated successfully.")
            return redirect(url_for('project.details', project_id=project_id))
        
    finally:
        cursor.close()
        conn.close()
    
    return render_template('projects/edit-task.html', project_id=project_id, task=task)


@tasks_bp.route('/projects/<string:project_id>/tasks/<string:task_id>/delete', methods=['POST'])
@logged_in
def delete(project_id, task_id):
    user_id = session['user_id']
    
    conn = connect_DB()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT project_id FROM projects WHERE project_id = %s AND user_id = %s", (project_id, user_id))
        if not cursor.fetchone():
            abort(404)

        cursor.execute("SELECT * FROM tasks WHERE task_id = %s AND project_id = %s", (task_id, project_id))
        if not cursor.fetchone():
            abort(404)
        
        cursor.execute("DELETE FROM tasks WHERE task_id = %s AND project_id = %s", (task_id, project_id))
        conn.commit()
            
        flash("Task deleted successfully.")
        
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('project.details', project_id=project_id))