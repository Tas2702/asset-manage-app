from flask import Blueprint, render_template, request, redirect, url_for, flash
from model import get_db_connection
from controllers.auth import login_required, admin_required

departments_bp = Blueprint('departments', __name__)

def _validate_department(name, location):
    errors = []

    if not name.strip():
        errors.append('Department name is required.')
    elif len(name) > 100:
        errors.append('Department name must be 100 characters or fewer.')

    if not location.strip():
        errors.append('Location is required.')
    elif len(location) > 100:
        errors.append('Location must be 100 characters or fewer.')

    return errors

@departments_bp.route('/')
@login_required
def index():
    db = get_db_connection()
    departments = db.execute('SELECT * FROM departments ORDER BY name').fetchall()
    db.close()
    return render_template('departments/index.html', departments=departments)

@departments_bp.route('/<int:department_id>')
@login_required
def view(department_id):
    db = get_db_connection()
    department = db.execute(
        'SELECT * FROM departments WHERE department_id = ?', (department_id,)
    ).fetchone()

    if department is None:
        db.close()
        return 'Department not found', 404

    # Fetch all users belonging to this department
    users = db.execute(
        'SELECT * FROM users WHERE department_id = ? ORDER BY username', (department_id,)
    ).fetchall()
    db.close()

    return render_template('departments/view.html', department=department, users=users)

@departments_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    if request.method == 'POST':
        name     = request.form['name'].strip()
        location = request.form['location'].strip()

        errors = _validate_department(name, location)
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('departments.add'))

        db = get_db_connection()
        # Check if a department with this name already exists
        existing = db.execute(
            'SELECT department_id FROM departments WHERE name = ?', (name,)
        ).fetchone()

        if existing:
            db.close()
            flash('A department with that name already exists.')
            return redirect(url_for('departments.add'))

        db.execute(
            'INSERT INTO departments (name, location) VALUES (?, ?)', (name, location)
        )
        db.commit()
        db.close()

        flash('Department added successfully.')
        return redirect(url_for('departments.index'))

    return render_template('departments/add.html')

@departments_bp.route('/<int:department_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(department_id):
    db = get_db_connection()
    department = db.execute(
        'SELECT * FROM departments WHERE department_id = ?', (department_id,)
    ).fetchone()

    if department is None:
        db.close()
        return 'Department not found', 404

    if request.method == 'POST':
        name     = request.form['name'].strip()
        location = request.form['location'].strip()

        errors = _validate_department(name, location)
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('departments.edit', department_id=department_id))

        # Check if the name is already taken by a different department
        existing = db.execute(
            'SELECT department_id FROM departments WHERE name = ? AND department_id != ?',
            (name, department_id)
        ).fetchone()

        if existing:
            db.close()
            flash('A department with that name already exists.')
            return redirect(url_for('departments.edit', department_id=department_id))

        db.execute(
            'UPDATE departments SET name = ?, location = ? WHERE department_id = ?',
            (name, location, department_id)
        )
        db.commit()
        db.close()

        flash('Department updated successfully.')
        return redirect(url_for('departments.view', department_id=department_id))

    db.close()
    return render_template('departments/edit.html', department=department)

@departments_bp.route('/<int:department_id>/delete', methods=['POST'])
@admin_required
def delete(department_id):
    db = get_db_connection()
    department = db.execute(
        'SELECT * FROM departments WHERE department_id = ?', (department_id,)
    ).fetchone()

    if department is None:
        db.close()
        return 'Department not found', 404

    # Check if any users still belong to this department before deleting
    members = db.execute(
        'SELECT user_id FROM users WHERE department_id = ?', (department_id,)
    ).fetchall()

    if members:
        db.close()
        flash('Cannot delete a department that still has users assigned to it.')
        return redirect(url_for('departments.view', department_id=department_id))

    db.execute('DELETE FROM departments WHERE department_id = ?', (department_id,))
    db.commit()
    db.close()

    flash('Department deleted successfully.')
    return redirect(url_for('departments.index'))
