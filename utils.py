from functools import wraps
from flask import session, flash, redirect, url_for, request, jsonify
import jwt
from config import JWT_SECRET_KEY


def logged_in(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if 'user_id' not in session:
            flash("You need to log in first.")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_func

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        #check for standard bearer token
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
            
        if not token:
            return jsonify({"error": "Authorization token is missing"}), 401
        
        try:
            #decode the token
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            
            #extract the user_id
            current_user_id = payload['user_id']
            
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token. Authentication failed."}), 401
        
        # pass the extracted user_id to wrapped route
        return f(current_user_id, *args, **kwargs)
    
    return decorated
