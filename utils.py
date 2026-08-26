from functools import wraps
from flask import session, flash, redirect, url_for

def logged_in(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if 'user_id' not in session:
            flash("You need to log in first.")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_func