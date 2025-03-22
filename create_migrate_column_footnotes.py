from app import create_app, db
from models import Column
from sqlalchemy import Column as SqlColumn, Text, JSON

def migrate_column_footnotes():
    """Add the footnote-related columns to the columns table"""
    app = create_app()
    with app.app_context():
        # Check if the columns already exist
        inspector = db.inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('columns')]
        
        changes_made = False
        
        # Add header_footnote column if it doesn't exist
        if 'header_footnote' not in columns:
            print("Adding header_footnote column to columns table...")
            db.engine.execute('ALTER TABLE columns ADD COLUMN header_footnote TEXT')
            changes_made = True
        
        # Add cell_footnotes column if it doesn't exist
        if 'cell_footnotes' not in columns:
            print("Adding cell_footnotes column to columns table...")
            # SQLite doesn't directly support JSON type, but we can use TEXT
            db.engine.execute('ALTER TABLE columns ADD COLUMN cell_footnotes TEXT')
            changes_made = True
        
        if changes_made:
            print("Migration complete.")
        else:
            print("No changes needed. Columns already exist.")

if __name__ == "__main__":
    migrate_column_footnotes()
