from flask import Flask, redirect, url_for
from model import init_db

class Config:
    # Secret key is used by Flask to securely sign session cookies.
    # e.g. os.environ.get('SECRET_KEY') for security.
    SECRET_KEY = 'your-secret-key-change-this-in-production'
 
    
    DEBUG = True
 

    DATABASE = 'asset_manage_app.db'

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
 
    # Load settings from the Config class defined above
    app.config.from_object(Config)

    from controllers.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from controllers.assets import assets_bp
    app.register_blueprint(assets_bp, url_prefix='/assets')

    from controllers.users import users_bp
    app.register_blueprint(users_bp, url_prefix='/users')

    from controllers.departments import departments_bp
    app.register_blueprint(departments_bp, url_prefix='/departments')
  
    init_db()

    @app.route('/')
    def index():
        return redirect(url_for('assets.index'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()
 

