from flask import Flask
from flask_migrate import Migrate
from models import db, ReturnsTable
from routes import main_blueprint
import json
from sqlalchemy import text  # Import the text function for SQL statements

def create_app():
    print("Starting application creation...")  
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///returns.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    Migrate(app, db)

    with app.app_context():
        print("Creating database tables...")  
        db.create_all()
        print("Database initialized")  
        
        # Check if tables exist
        tables = ReturnsTable.query.all()
        print(f"Found {len(tables)} existing tables")  
        for table in tables:
            print(f"Table ID: {table.id}, Name: {table.name}")  
        
        # # Migrate footnote columns if needed
        # migrate_footnote_columns(db)

    app.register_blueprint(main_blueprint)
    print("Application creation completed")  
    return app

# def migrate_footnote_columns(db):
#     """Add the footnote-related columns to the columns table if they don't exist"""
#     with db.engine.connect() as conn:
#         # Check if the columns already exist
#         inspector = db.inspect(db.engine)
#         column_names = [column['name'] for column in inspector.get_columns('columns')]
        
#         changes_made = False
        
#         # Add header_footnote column if it doesn't exist
#         if 'header_footnote' not in column_names:
#             print("Adding header_footnote column to columns table...")
#             # Use text() to create an executable SQL statement
#             conn.execute(text('ALTER TABLE columns ADD COLUMN header_footnote TEXT'))
#             changes_made = True
        
#         # Add cell_footnotes column if it doesn't exist
#         if 'cell_footnotes' not in column_names:
#             print("Adding cell_footnotes column to columns table...")
#             # SQLite doesn't directly support JSON type, but we can use TEXT
#             conn.execute(text('ALTER TABLE columns ADD COLUMN cell_footnotes TEXT'))
#             changes_made = True
        
#         if changes_made:
#             print("Footnote columns migration completed.")
#         else:
#             print("Footnote columns already exist.")

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
    drop_database_tables(app, db)


