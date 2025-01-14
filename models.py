from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # Define db here, but don't bind to 'app' yet

class Column(db.Model):
    __tablename__ = 'column'  # you may rename to 'columns' if you like

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    # Polymorphic discriminator
    discriminator = db.Column(db.String(50))  

    # Relationship fields
    cells = db.relationship('Cell', backref='column', lazy=True)
    returns_table_id = db.Column(db.Integer, db.ForeignKey('returns_table.id'), nullable=False)

    __mapper_args__ = {
        'polymorphic_on': discriminator,        # Tells SQLAlchemy which field indicates the subclass
        'polymorphic_identity': 'column',       # Identity for the base class
        'with_polymorphic': '*'                 # Load all subclasses in queries if needed
    }

    def __repr__(self):
        return f"<Column(name={self.name})>"
    
class DateColumn(Column):
    # NOTE: We do NOT specify a separate __tablename__ here 
    # because single-table inheritance means child rows go in the same table as the parent.

    # Child-specific field
    acds = db.Column(db.String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'datecolumn'  # Unique ID for this subclass
    }

    def __repr__(self):
        return f"<DateColumn(name={self.name}, acds={self.acds})>"
    
class ReturnsTable(db.Model):
    __tablename__ = 'returns_table'  # or 'returns_tables'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    
    # The relationship will store both Column and DateColumn 
    # because they're in the same polymorphic hierarchy
    columns = db.relationship('Column', backref='returns_table', lazy=True)

    def __repr__(self):
        column_names = [column.name for column in self.columns]
        return f"<ReturnsTable(name={self.name}, columns={column_names})>"

class Cell(db.Model):
    __tablename__ = 'cell'
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.PickleType, nullable=True)
    color = db.Column(db.String(50), nullable=True)
    format = db.Column(db.String(10), nullable=True)
    column_id = db.Column(db.Integer, db.ForeignKey('column.id'), nullable=False)

    def __repr__(self):
        return f"<Cell(value={self.value}, color={self.color}, format={self.format})>"