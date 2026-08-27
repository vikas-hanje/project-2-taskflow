from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import connect_DB
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