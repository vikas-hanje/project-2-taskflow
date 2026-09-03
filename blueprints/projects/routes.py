from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from db import connect_DB, get_owned_project
import uuid
from utils import logged_in

project_bp = Blueprint('project', __name__, url_prefix='/projects')

@project_bp.route('/', methods=['GET', 'POST'])
@logged_in
def index():
    user_id = session['user_id']
    
    # create new project
    if request.method == 'POST':
        project_name = request.form.get('name')
        
        if not project_name:
            flash("Project name is required.")
            return redirect(url_for('project.index'))
        
        new_project_id = str(uuid.uuid4())
        
        conn = connect_DB()
        cursor = conn.cursor()
        
        try:
            insert_query = "insert into projects(project_id, name, user_id) values(%s, %s, %s)"
            cursor.execute(insert_query, (new_project_id, project_name, user_id))
            conn.commit()
            flash(f"Project '{project_name}' created successfully.")
            
        finally:
            cursor.close()
            conn.close()
            
        return redirect(url_for('project.index'))
    
    # fetch and display projects
    conn = connect_DB()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("select * from projects where user_id = %s order by created_at desc", (user_id,))
        user_projects = cursor.fetchall()
    
    finally:
        cursor.close()
        conn.close()
        
    return render_template('projects/list.html', projects=user_projects)


# project details
@project_bp.route('/<string:project_id>')
@logged_in
def details(project_id):
    user_id = session['user_id']
    
    # CHANGED: ownership check now goes through the shared get_owned_project() helper
    # instead of a raw SELECT written out here
    project = get_owned_project(project_id, user_id)
    
    if not project:
        abort(404)
    
    conn = connect_DB()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("select * from tasks where project_id = %s order by created_at desc", (project_id,))
        tasks = cursor.fetchall()
            
    finally:
        cursor.close()
        conn.close()
        
    return render_template('projects/details.html', project=project, tasks=tasks)


@project_bp.route('/<string:project_id>/edit', methods=['GET', 'POST'])
@logged_in
def edit(project_id):
    user_id = session['user_id']
    
    if request.method == 'POST':
        new_name = request.form.get('name')
        
        if not new_name:
            flash("New name cannot be empty.")
            return redirect(url_for('project.edit', project_id=project_id))
        
        # CHANGED: replaced the manual "select ... where project_id = %s and user_id = %s"
        # existence check with the shared helper
        if not get_owned_project(project_id, user_id):
            abort(404)
        
        conn = connect_DB()
        cursor = conn.cursor()
        
        try:
            cursor.execute("update projects set name = %s where project_id = %s and user_id = %s", (new_name, project_id, user_id))
            conn.commit()
                
            flash("Project details updated successfully.")
            return redirect(url_for('project.details', project_id=project_id))
        
        finally:
            cursor.close()
            conn.close()
            
    # GET req: fetch project details to pre-fill the form
    # CHANGED: this replaces the raw SELECT entirely -- get_owned_project both verifies
    # ownership AND returns the row needed to pre-fill the form, so no separate query
    # is needed here at all anymore
    project = get_owned_project(project_id, user_id)
    
    if not project:
        abort(404)
        
    return render_template('projects/edit.html', project=project)


@project_bp.route('/<string:project_id>/delete', methods=['POST'])
@logged_in
def delete(project_id):
    user_id = session['user_id']
    
    # NOTE: left as-is deliberately -- this single DELETE already combines the
    # ownership check and the action into one atomic query (WHERE ... AND user_id = %s),
    # which is more efficient than calling get_owned_project() first and issuing a
    # second query. DELETE doesn't have the "matched but unchanged" ambiguity UPDATE
    # has, so rowcount == 0 here reliably means "didn't exist or wasn't yours."
    conn = connect_DB()
    cursor = conn.cursor()
    
    try:
        cursor.execute("delete from projects where project_id = %s and user_id = %s", (project_id, user_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            abort(404)
            
        flash("Project deleted successfully.")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('project.index'))
