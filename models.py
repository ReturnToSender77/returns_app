from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from sqlalchemy.orm.attributes import flag_modified

# Instantiate the database
db = SQLAlchemy()

# JSON serialization helper for SQLite
class JsonEncodedDict(db.TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""
    impl = db.Text
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return '{}'
        return json.dumps(value)
        
    def process_result_value(self, value, dialect):
        if value is None:
            return {}
        return json.loads(value)

class ReturnsTable(db.Model):
    __tablename__ = 'returns_tables'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)  # Need to fix this
    
    # Note cascade delete to columns
    columns = db.relationship('Column', backref='returns_table', 
                            lazy=True, cascade='all, delete-orphan',
                            passive_deletes=True)
    
    # Factiva articles relationship
    factiva_articles = db.relationship('FactivaArticle', backref='returns_table',
                                       lazy=True, cascade='all, delete-orphan')
    
    # Removed footnotes relationship

    def __repr__(self):
        column_names = [column.name for column in self.columns]
        return f"<ReturnsTable(name={self.name}, columns={column_names})>"

# Remove Footnote model

class FactivaArticle(db.Model):
    __tablename__ = 'factiva_articles'
    
    id = db.Column(db.Integer, primary_key=True)
    returns_table_id = db.Column(db.Integer, 
                                 db.ForeignKey('returns_tables.id', ondelete='CASCADE'),
                                 nullable=False)
    headline = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=True) 
    word_count = db.Column(db.Integer, nullable=True)  # changed to Integer
    publish_date = db.Column(db.DateTime, nullable=True)  # changed to DateTime
    source = db.Column(db.String, nullable=True)
    content = db.Column(db.Text, nullable=True)
    
    # Add cell_id to link articles to specific FactivaCell
    cell_id = db.Column(db.Integer, db.ForeignKey('factiva_cells.id', ondelete='SET NULL'), nullable=True)
    
    def __repr__(self):
        return f"<FactivaArticle(headline={self.headline}, author={self.author})>"

# COLUMN TABLES
class Column(db.Model):
    __tablename__ = 'columns'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    discriminator = db.Column(db.String(50))  

    # Add footnote-related fields
    header_footnote = db.Column(db.Text, nullable=True)  # Footnote for the column header
    # Use the custom type for JSON in SQLite
    cell_footnotes = db.Column(JsonEncodedDict, nullable=True)

    # Add cascade delete to cells
    cells = db.relationship('BaseCell', backref='column', 
                          lazy=True, cascade='all, delete-orphan',
                          passive_deletes=True)
    
    returns_table_id = db.Column(db.Integer, db.ForeignKey('returns_tables.id', 
                               ondelete='CASCADE'), nullable=False)

    __mapper_args__ = {
        'polymorphic_on': discriminator,
        'polymorphic_identity': 'column',
        'with_polymorphic': '*', # To allow querying of all column types
        'confirm_deleted_rows': False
    }

    def __repr__(self):
        return f"<Column(name={self.name})>"
    
    def set_footnote(self, cell_index, text):
        """
        Set a footnote for a cell at the given index
        cell_index = 0 means column header
        cell_index > 0 means the (index-1)th cell
        """
        if cell_index == 0:
            self.header_footnote = text
        else:
            if self.cell_footnotes is None:
                self.cell_footnotes = {}
            
            cell_idx_str = str(cell_index-1)
            
            if text:
                # Create a new dict to trigger SQLAlchemy change detection
                self.cell_footnotes[cell_idx_str] = text
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(self, 'cell_footnotes')
            elif cell_idx_str in self.cell_footnotes:
                # Create a new dict to trigger SQLAlchemy change detection
                del self.cell_footnotes[cell_idx_str]
                flag_modified(self, 'cell_footnotes')
    
    def get_footnote(self, cell_index):
        """
        Get the footnote for a cell at the given index
        cell_index = 0 means column header
        cell_index > 0 means the (index-1)th cell
        """
        if cell_index == 0:
            return self.header_footnote or ""
        
        if not self.cell_footnotes:
            return ""
        
        return self.cell_footnotes.get(str(cell_index-1), "")

class DateColumn(Column):
    __mapper_args__ = {
        'polymorphic_identity': 'datecolumn'
    }

    def __repr__(self):
        return f"<DateColumn(name={self.name})>"

class TextColumn(Column):
    __mapper_args__ = {
        'polymorphic_identity': 'textcolumn'
    }
    def __repr__(self):
        return f"<TextColumn(name={self.name})>"

class FactivaColumn(Column):
    __mapper_args__ = {
        'polymorphic_identity': 'factivacolumn'
    }
    
    def __repr__(self):
        return f"<FactivaColumn(name={self.name})>"

# CELL TABLES
class BaseCell(db.Model):
    __tablename__ = 'base_cells'
    id = db.Column(db.Integer, primary_key=True)
    color = db.Column(db.String(50))
    format = db.Column(db.String(10))
    column_id = db.Column(db.Integer, db.ForeignKey('columns.id'), nullable=False)
    discriminator = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_on': discriminator,
        'polymorphic_identity': 'base_cell',
        'confirm_deleted_rows': False
    }

class NumberCell(BaseCell):
    __tablename__ = 'number_cells'
    id = db.Column(db.Integer, db.ForeignKey('base_cells.id'), primary_key=True)

    value = db.Column(db.Float)

    __mapper_args__ = {
        'polymorphic_identity': 'number_cell',
        'confirm_deleted_rows': False
    }

class DateCell(BaseCell):
    __tablename__ = 'date_cells'
    id = db.Column(db.Integer, db.ForeignKey('base_cells.id'), primary_key=True)

    value = db.Column(db.DateTime)
    acd = db.Column(db.Integer, default=0)  # 1 indicates an alleged corrective disclosure; 0 otherwise

    __mapper_args__ = {
        'polymorphic_identity': 'date_cell',
        'confirm_deleted_rows': False
    }

class TextCell(BaseCell):
    __tablename__ = 'text_cells'
    id = db.Column(db.Integer, db.ForeignKey('base_cells.id'), primary_key=True)

    value = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'text_cell',
        'confirm_deleted_rows': False
    }

class FactivaCell(BaseCell):
    __tablename__ = 'factiva_cells'
    id = db.Column(db.Integer, db.ForeignKey('base_cells.id'), primary_key=True)
    
    # Date for which this cell holds articles
    date_value = db.Column(db.DateTime, nullable=True)
    
    # Relationship to the articles associated with this cell
    articles = db.relationship('FactivaArticle', backref='cell', lazy=True)
    
    # Store summary information for display purposes
    article_count = db.Column(db.Integer, default=0)
    
    # Store a representative footnote for Excel export (only one footnote will be shown)
    representative_footnote = db.Column(db.Text, nullable=True)
    
    __mapper_args__ = {
        'polymorphic_identity': 'factiva_cell',
        'confirm_deleted_rows': False
    }
    
    @property
    def display_text(self):
        """Returns text to display in the cell"""
        if self.article_count == 0:
            return "No articles"
        elif self.article_count == 1:
            return "1 Article"
        else:
            return f"{self.article_count} Articles"
    
    def add_article(self, article):
        """Add an article to this cell and update the count"""
        article.cell_id = self.id
        self.article_count += 1
        
    def set_representative_footnote(self):
        """Set a representative footnote based on article information"""
        if not self.articles:
            self.representative_footnote = None
            return
            
        sources = set()
        for article in self.articles:
            if article.source:
                sources.add(article.source)
                
        if sources:
            self.representative_footnote = f"Sources: {', '.join(sorted(sources))}"
        else:
            self.representative_footnote = None
