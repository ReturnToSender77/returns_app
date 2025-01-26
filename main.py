from flask import Flask
from flask_migrate import Migrate
from models import db, ReturnsTable  # Add ReturnsTable import
from routes import main_blueprint

def create_app():
    print("Starting application creation...")  # Debug print
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///returns.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    Migrate(app, db)

    with app.app_context():
        print("Creating database tables...")  # Debug print
        db.create_all()
        print("Database initialized")  # Debug print
        
        # Check if tables exist
        tables = ReturnsTable.query.all()
        print(f"Found {len(tables)} existing tables")  # Debug print
        for table in tables:
            print(f"Table ID: {table.id}, Name: {table.name}")  # Debug print

    app.register_blueprint(main_blueprint)
    print("Application creation completed")  # Debug print
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
    app.run(debug=True, use_reloader=True)
    drop_database_tables(app, db)  # Comment out or remove this


