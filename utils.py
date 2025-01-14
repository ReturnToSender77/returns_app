import pandas as pd
from models import ReturnsTable, Column, DateColumn, Cell

def extract_data_file(file, db_session):
    """Convert uploaded file to ReturnsTable and store in database
    
    Args:
        file: FileStorage object from Flask request
        db_session: SQLAlchemy database session
    Returns:
        tuple: (ReturnsTable, pd.DataFrame)
    """
    # Read file based on extension
    filename = file.filename
    if filename.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    
    # Create ReturnsTable instance
    returns_table = ReturnsTable(name=filename)
    
    # Process each column
    for col_name in df.columns:
        values = df[col_name]
        
        if pd.api.types.is_datetime64_any_dtype(values): # Check if column is date
            column = DateColumn(name=col_name)
            
            # Create cells for dates
            for i, date_val in enumerate(values):
                if i < 6:
                    print(date_val)
                cell = Cell(
                    value=date_val.strftime('%Y-%m-%d'),
                    format='date'
                )

                column.cells.append(cell)
                
        else: # Regular Column for non-date data
            column = Column(name=col_name)
            
            # Create cells for values
            for i, val in enumerate(values):
                if i < 6:
                    print(val)
                cell = Cell(
                    value=val,
                    format='text'
                )
                column.cells.append(cell)
        
        # Link column to returns table
        column.returns_table = returns_table
    
    return returns_table, df

