from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from model import get_db_connection
from controllers.auth import admin_required, login_required

users_bp = Blueprint('users', __name__)

VALID_ROLES = ['admin', 'user']

def _validate_user(username, email, password, require_password=True):
    errors = []

    if len(username) < 3:
        errors.append('Username must be at least 3 characters.')
    elif len(username) > 50:
        errors.append('Username must be 50 characters or fewer.')
    elif not username.replace('_', '').isalnum():
        errors.append('Username can only contain letters, numbers, and underscores.')

    if '@' not in email or '.' not in email.split('@')[-1]:
        errors.append('Please enter a valid email address.')

    # Password is required when adding, optional when editing
    if require_password and len(password) < 6:
        errors.append('Password must be at least 6 characters.')
    elif not require_password and password and len(password) < 6:
        errors.append('New password must be at least 6 characters.')

    return errors

@users_bp.route('/')
@login_required
def index():
    db = get_db_connection()
    # JOIN with departments to show the department name instead of just the ID
    users = db.execute('''
        SELECT users.*, departments.name AS department_name
        FROM users
        LEFT JOIN departments ON users.department_id = departments.department_id
        ORDER BY users.username
    ''').fetchall()
    db.close()
    return render_template('users/index.html', users=users)

@users_bp.route('/<int:user_id>')
@login_required
def view(user_id):
    db = get_db_connection()
    # JOIN with departments to show the department name on the detail page
    user = db.execute('''
        SELECT users.*, departments.name AS department_name
        FROM users
        LEFT JOIN departments ON users.department_id = departments.department_id
        WHERE users.user_id = ?
    ''', (user_id,)).fetchone()

    if user is None:
        db.close()
        return 'User not found', 404

    # Fetch all assets currently assigned to this user
    assets = db.execute(
        'SELECT * FROM assets WHERE assigned_to = ? ORDER BY asset_tag', (user_id,)
    ).fetchall()
    db.close()

    return render_template('users/view.html', user=user, assets=assets)

@users_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    db = get_db_connection()
    # Fetch departments to populate the dropdown in the form
    departments = db.execute('SELECT * FROM departments ORDER BY name').fetchall()

    if request.method == 'POST':
        username      = request.form['username'].strip()
        email         = request.form['email'].strip()
        role          = request.form['role']
        raw_password  = request.form['password']
        department_id = request.form['department_id'] or None

        errors = _validate_user(username, email, raw_password, require_password=True)
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('users.add'))

        # Hash the password before storing it in the database
        password = generate_password_hash(raw_password)

        # Check if the username or email is already taken
        existing = db.execute(
            'SELECT user_id FROM users WHERE username = ? OR email = ?', (username, email)
        ).fetchone()

        if existing:
            db.close()
            flash('A user with that username or email already exists.')
            return redirect(url_for('users.add'))

        db.execute(
            'INSERT INTO users (username, email, password, role, department_id) VALUES (?, ?, ?, ?, ?)',
            (username, email, password, role, department_id)
        )
        db.commit()
        db.close()

        flash('User added successfully.')
        return redirect(url_for('users.index'))

    db.close()
    return render_template('users/add.html', departments=departments)

@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(user_id):
    db = get_db_connection()
    user = db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()

    if user is None:
        db.close()
        return 'User not found', 404

    # Fetch departments to populate the dropdown in the form
    departments = db.execute('SELECT * FROM departments ORDER BY name').fetchall()

    if request.method == 'POST':
        username      = request.form['username'].strip()
        email         = request.form['email'].strip()
        role          = request.form['role']
        raw_password  = request.form['password']
        department_id = request.form['department_id'] or None

        errors = _validate_user(username, email, raw_password, require_password=False)
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('users.edit', user_id=user_id))

        # Check if the new username or email is already taken by a different user
        existing = db.execute(
            'SELECT user_id FROM users WHERE (username = ? OR email = ?) AND user_id != ?',
            (username, email, user_id)
        ).fetchone()

        if existing:
            db.close()
            flash('A user with that username or email already exists.')
            return redirect(url_for('users.edit', user_id=user_id))

        # Only update the password if a new one was provided
        if raw_password:
            password = generate_password_hash(raw_password)
            db.execute(
                'UPDATE users SET username = ?, email = ?, password = ?, role = ?, department_id = ? WHERE user_id = ?',
                (username, email, password, role, department_id, user_id)
            )
        else:
            db.execute(
                'UPDATE users SET username = ?, email = ?, role = ?, department_id = ? WHERE user_id = ?',
                (username, email, role, department_id, user_id)
            )

        db.commit()
        db.close()

        flash('User updated successfully.')
        return redirect(url_for('users.view', user_id=user_id))

    db.close()
    return render_template('users/edit.html', user=user, departments=departments)

@users_bp.route('/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete(user_id):
    db = get_db_connection()
    user = db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()

    if user is None:
        db.close()
        return 'User not found', 404

    # Prevent the admin from deleting their own account
    if user_id == session.get('user_id'):
        db.close()
        flash('You cannot delete your own account.')
        return redirect(url_for('users.index'))

    db.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    db.commit()
    db.close()

    flash('User deleted successfully.')
    # Redirect back to the full user list after deletion
    return redirect(url_for('users.index'))
