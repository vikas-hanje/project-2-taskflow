from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from db import connect_DB

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for('auth.register'))
        
        conn = connect_DB()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("select * from users where email = %s", (email,))
            existing_email = cursor.fetchone()
        
            if existing_email:
                flash("Email already registered! Please log in.")
                return redirect(url_for('auth.login'))
            
            # BUG FIX: was querying "where email = %s" with the username value --
            # that column/value mismatch meant this check never actually matched anything,
            # so duplicate usernames were silently allowed through.
            cursor.execute("select * from users where username = %s", (username,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # FIX: message now correctly describes what was actually checked
                flash("Username already taken. Please choose another.")
                return redirect(url_for('auth.register'))

            new_user_id = str(uuid.uuid4())
            hashed_password = generate_password_hash(password)
            
            insert_query = "insert into users(user_id, username, email, password_hash) values (%s, %s, %s, %s)"
            cursor.execute(insert_query, (new_user_id, username, email, hashed_password))
            
            conn.commit()      
            
            flash("Registration successful. You can now log in.")
            return redirect(url_for('auth.login'))
        
        finally:
            cursor.close()
            conn.close()

    return render_template('auth/register.html')
        
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = connect_DB()
        cursor = conn.cursor(dictionary=True)
        
        try:
        
            cursor.execute("select * from users  where email = %s", (email,))
            user = cursor.fetchone()
            
            # verify user creds
            if user and check_password_hash(user['password_hash'], password):
                
                # store session variables
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                
                return redirect(url_for('index'))
            else:
                flash("Invalid email or password")
                return redirect(url_for('auth.login'))
            
        finally:
            cursor.close()
            conn.close()
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))