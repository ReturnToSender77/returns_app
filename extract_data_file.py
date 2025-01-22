import pandas as pd
from models import db, ReturnsTable, Column, DateColumn, TextColumn, NumberCell, DateCell, TextCell

def extract_data_file(file):
    """Process an uploaded file and store its data in the database.
    
    Args:
        file: Uploaded file object (CSV or Excel format)
        
    Returns:
        tuple: (ReturnsTable, pandas.DataFrame)
            - ReturnsTable: Database model instance containing the processed data
            - DataFrame: pandas DataFrame containing the file contents
            
    Raises:
        ValueError: If column type is not supported (numeric, datetime, or text)
    """

    # Read the file into a DataFrame
    filename = file.filename
    if filename.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    # Create a new ReturnsTable instance
    returns_table = ReturnsTable(name=filename)
    db.session.add(returns_table)
    db.session.commit()

    # Iterate over the DataFrame columns
    for column_name in df.columns:
        column_data = df[column_name]

        # Determine the column type, and assign the proper Column and Cell types
        if pd.api.types.is_numeric_dtype(column_data):
            column = Column(name=column_name, returns_table_id=returns_table.id)
            db.session.add(column)
            db.session.commit()
            for value in column_data:
                cell = NumberCell(value=value, column_id=column.id)
                db.session.add(cell)
        elif pd.api.types.is_datetime64_any_dtype(column_data):
            column = DateColumn(name=column_name, returns_table_id=returns_table.id)
            db.session.add(column)
            db.session.commit()
            for value in column_data:
                cell = DateCell(value=value, column_id=column.id)
                db.session.add(cell)
        elif pd.api.types.is_string_dtype(column_data):
            column = TextColumn(name=column_name, returns_table_id=returns_table.id)
            db.session.add(column)
            db.session.commit()
            for value in column_data:
                cell = TextCell(value=value, column_id=column.id)
                db.session.add(cell)
        else:
            raise ValueError(f"Unsupported column type for column: {column_name}")

    # Commit all changes to the database
    db.session.commit()

    return returns_table, df

