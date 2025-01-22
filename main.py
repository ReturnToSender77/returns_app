# from my_flask_app_returns import create_app
from flask import Flask
from flask_migrate import Migrate
from models import db
from routes import main_blueprint

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///returns.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    Migrate(app, db)

    with app.app_context():
        db.create_all()

    app.register_blueprint(main_blueprint)

    return app

def drop_database_tables(app, database):
    """ Drop all tables in the database; useful for development
    Args:
        app: Flask app instance
        db: SQLAlchemy db instance
    """
    with app.app_context():
        database.drop_all()

    print("All returns database tables dropped.")

# Create and run app - also reset the database; useful for development
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
    drop_database_tables(app, db)
    
        
