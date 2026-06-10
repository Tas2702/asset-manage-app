import functools
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from model import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db_connection()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        db.close()

        # Fail if user doesn't exist or password doesn't match the stored hash
        if user is None or not check_password_hash(user['password'], password):
            flash('Invalid username or password.')
            return redirect(url_for('auth.login'))

        # Clear any existing session data before storing the new user's details
        session.clear()
        session['user_id'] = user['user_id']
        session['username'] = user['username']
        session['role'] = user['role']
        return redirect(url_for('assets.index'))

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email    = request.form['email'].strip()
        password = request.form['password']

        # Validate username
        if len(username) < 3:
            flash('Username must be at least 3 characters.')
            return redirect(url_for('auth.register'))
        if len(username) > 50:
            flash('Username must be 50 characters or fewer.')
            return redirect(url_for('auth.register'))
        if not username.replace('_', '').isalnum():
            flash('Username can only contain letters, numbers, and underscores.')
            return redirect(url_for('auth.register'))

        # Validate email
        if '@' not in email or '.' not in email.split('@')[-1]:
            flash('Please enter a valid email address.')
            return redirect(url_for('auth.register'))

        # Validate password
        if len(password) < 6:
            flash('Password must be at least 6 characters.')
            return redirect(url_for('auth.register'))

        db = get_db_connection()
        # Check if the username or email is already taken
        existing = db.execute(
            'SELECT user_id FROM users WHERE username = ? OR email = ?', (username, email)
        ).fetchone()

        if existing:
            db.close()
            flash('A user with that username or email already exists.')
            return redirect(url_for('auth.register'))

        db.execute(
            'INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
            (username, email, generate_password_hash(password), 'user')
        )
        db.commit()
        db.close()

        flash('Account created successfully. Please log in.')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

# Decorator: blocks access to a route if the user is not logged in
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

# Decorator: blocks access to a route if the user is not an admin
def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            flash('You need admin access to view that page.')
            return redirect(url_for('assets.index'))
        return view(**kwargs)
    return wrapped_view