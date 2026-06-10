from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from model import get_db_connection
from controllers.auth import login_required, admin_required

assets_bp = Blueprint('assets', __name__)

VALID_CATEGORIES = ['Laptop', 'Desktop', 'Monitor', 'Phone', 'Tablet', 'Printer', 'Networking', 'Other']
VALID_STATUSES   = ['Available', 'Assigned', 'Under Repair', 'Decommissioned']

def _validate_asset(asset_tag, name, category, status, assigned_to, purchase_date, warranty_expiry):
    errors = []

    if not asset_tag.strip():
        errors.append('Asset tag is required.')
    elif len(asset_tag) > 20:
        errors.append('Asset tag must be 20 characters or fewer.')

    if not name.strip():
        errors.append('Name is required.')
    elif len(name) > 100:
        errors.append('Name must be 100 characters or fewer.')

    if category not in VALID_CATEGORIES:
        errors.append('Please select a valid category.')

    if status not in VALID_STATUSES:
        errors.append('Please select a valid status.')

    # An asset marked as Assigned must have a user selected
    if status == 'Assigned' and not assigned_to:
        errors.append('An asset marked as Assigned must have a user assigned.')

    parsed_purchase = None
    parsed_warranty = None

    if purchase_date:
        try:
            parsed_purchase = datetime.strptime(purchase_date, '%Y-%m-%d')
        except ValueError:
            errors.append('Purchase date must be a valid date.')

    if warranty_expiry:
        try:
            parsed_warranty = datetime.strptime(warranty_expiry, '%Y-%m-%d')
        except ValueError:
            errors.append('Warranty expiry must be a valid date.')

    # Warranty expiry must come after the purchase date
    if parsed_purchase and parsed_warranty and parsed_warranty <= parsed_purchase:
        errors.append('Warranty expiry must be after the purchase date.')

    return errors

@assets_bp.route('/')
@login_required
def index():
    db = get_db_connection()
    # JOIN with users so we can display the assigned username instead of just the user_id
    assets = db.execute('''
        SELECT assets.*, users.username AS assigned_username
        FROM assets
        LEFT JOIN users ON assets.assigned_to = users.user_id
        ORDER BY assets.asset_tag
    ''').fetchall()
    db.close()
    return render_template('assets/index.html', assets=assets)

@assets_bp.route('/<int:asset_id>')
@login_required
def view(asset_id):
    db = get_db_connection()
    # JOIN with users to show the assigned username on the detail page
    asset = db.execute('''
        SELECT assets.*, users.username AS assigned_username
        FROM assets
        LEFT JOIN users ON assets.assigned_to = users.user_id
        WHERE assets.asset_id = ?
    ''', (asset_id,)).fetchone()
    db.close()

    # Return a 404 if the asset_id doesn't exist in the database
    if asset is None:
        return 'Asset not found', 404

    return render_template('assets/view.html', asset=asset)

@assets_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    db = get_db_connection()
    # Fetch users to populate the assigned_to dropdown in the form
    users = db.execute('SELECT user_id, username FROM users ORDER BY username').fetchall()

    if request.method == 'POST':
        asset_tag       = request.form['asset_tag']
        name            = request.form['name']
        category        = request.form['category']
        status          = request.form['status']
        # Optional fields default to None so the database stores NULL instead of an empty string
        assigned_to     = request.form['assigned_to'] or None
        purchase_date   = request.form['purchase_date'] or None
        warranty_expiry = request.form['warranty_expiry'] or None
        notes           = request.form['notes'] or None

        errors = _validate_asset(asset_tag, name, category, status, assigned_to, purchase_date, warranty_expiry)
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('assets.add'))

        db.execute('''
            INSERT INTO assets (asset_tag, name, category, status, assigned_to, purchase_date, warranty_expiry, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (asset_tag, name, category, status, assigned_to, purchase_date, warranty_expiry, notes))
        db.commit()
        db.close()

        flash('Asset added successfully.')
        return redirect(url_for('assets.index'))

    db.close()
    return render_template('assets/add.html', users=users)

@assets_bp.route('/<int:asset_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(asset_id):
    db = get_db_connection()
    asset = db.execute('SELECT * FROM assets WHERE asset_id = ?', (asset_id,)).fetchone()

    if asset is None:
        db.close()
        return 'Asset not found', 404

    # Fetch users to populate the assigned_to dropdown in the form
    users = db.execute('SELECT user_id, username FROM users ORDER BY username').fetchall()

    if request.method == 'POST':
        asset_tag       = request.form['asset_tag']
        name            = request.form['name']
        category        = request.form['category']
        status          = request.form['status']
        # Optional fields default to None so the database stores NULL instead of an empty string
        assigned_to     = request.form['assigned_to'] or None
        purchase_date   = request.form['purchase_date'] or None
        warranty_expiry = request.form['warranty_expiry'] or None
        notes           = request.form['notes'] or None

        errors = _validate_asset(asset_tag, name, category, status, assigned_to, purchase_date, warranty_expiry)
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('assets.edit', asset_id=asset_id))

        db.execute('''
            UPDATE assets
            SET asset_tag = ?, name = ?, category = ?, status = ?,
                assigned_to = ?, purchase_date = ?, warranty_expiry = ?, notes = ?
            WHERE asset_id = ?
        ''', (asset_tag, name, category, status, assigned_to, purchase_date, warranty_expiry, notes, asset_id))
        db.commit()
        db.close()

        flash('Asset updated successfully.')
        return redirect(url_for('assets.view', asset_id=asset_id))

    db.close()
    return render_template('assets/edit.html', asset=asset, users=users)

@assets_bp.route('/<int:asset_id>/delete', methods=['POST'])
@admin_required
def delete(asset_id):
    db = get_db_connection()
    asset = db.execute('SELECT * FROM assets WHERE asset_id = ?', (asset_id,)).fetchone()

    # Return 404 if the asset doesn't exist
    if asset is None:
        db.close()
        return 'Asset not found', 404

    db.execute('DELETE FROM assets WHERE asset_id = ?', (asset_id,))
    db.commit()
    db.close()

    flash('Asset deleted successfully.')
    # Redirect back to the full asset list after deletion
    return redirect(url_for('assets.index'))
