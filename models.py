from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Instantiate the database
db = SQLAlchemy()

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

    def __repr__(self):
        column_names = [column.name for column in self.columns]
        return f"<ReturnsTable(name={self.name}, columns={column_names})>"

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
    
    def __repr__(self):
        return f"<FactivaArticle(headline={self.headline}, author={self.author})>"

# COLUMN TABLES
class Column(db.Model):
    __tablename__ = 'columns'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    discriminator = db.Column(db.String(50))  

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
