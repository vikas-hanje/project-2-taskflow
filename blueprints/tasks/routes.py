from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
import uuid
from db import connect_DB, get_owned_project
from utils import logged_in

tasks_bp = Blueprint('task', __name__)

@tasks_bp.route('/projects/<string:project_id>/tasks', methods=['POST'])
@logged_in
def index(project_id):
    user_id = session['user_id']
    
    # CHANGED: project-ownership check now via the shared helper instead of a raw SELECT
    if not get_owned_project(project_id, user_id):
        abort(404)
    
    title = request.form.get('title')
    status = request.form.get('status')
    priority = request.form.get('priority')
    due_date = request.form.get('due_date') or None
    
    if not title:
        flash("Task title is required.")
        return redirect(url_for('project.details', project_id=project_id))
    
    task_id = str(uuid.uuid4())
    
    conn = connect_DB()
    cursor = conn.cursor()
    
    try:
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
    
    # CHANGED: Layer 1 (project ownership) now via the shared helper
    if not get_owned_project(project_id, user_id):
        abort(404)
    
    conn = connect_DB()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Layer 2 stays as its own query here -- get_owned_project only knows about
        # projects, and this route specifically needs the *task* row itself (not just
        # confirmation it exists) so the edit form can be pre-filled with its current values.
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
    
    # CHANGED: Layer 1 (project ownership) via the shared helper
    if not get_owned_project(project_id, user_id):
        abort(404)
    
    conn = connect_DB()
    cursor = conn.cursor()
    
    try:
        # CHANGED: Layer 2 (task belongs to this project) is now combined directly into
        # the DELETE's WHERE clause instead of a separate existence-check SELECT beforehand --
        # same reasoning as project delete() above. rowcount == 0 reliably means the task
        # either doesn't exist or doesn't belong to this project.
        cursor.execute("DELETE FROM tasks WHERE task_id = %s AND project_id = %s", (task_id, project_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            abort(404)
            
        flash("Task deleted successfully.")
        
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('project.details', project_id=project_id))
