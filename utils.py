import pandas as pd
from models import db, ReturnsTable, Column, DateColumn, TextColumn, NumberCell, DateCell, TextCell

def extract_data_file(file, database) -> tuple[ReturnsTable, pd.DataFrame]:
    """This function takes an uploaded file (CSV or Excel), reads it into a pandas DataFrame,
    creates corresponding ReturnsTable and Column models, and stores all the data.
    It handles automatic type detection (date, numerical, text) and data conversion for different column types.
    
    Args:
        DataFrame: pandas DataFrame containing the original file contents
        ValueError: If column type is not supported (must be numeric, datetime, or text)
        Exception: If there are any errors during file reading or data processing
    Notes:
        - If a table with the same filename already exists, it will be deleted
        - Column types are automatically detected and mapped to appropriate database models:
            * Datetime columns -> DateColumn with DateCell entries
            * Numeric columns -> Column with NumberCell entries  
            * Text/other columns -> TextColumn with TextCell entries
        - Null values are handled appropriately for each column type
        - The database session is not committed in this function, caller must handle db.commit
        Process an uploaded file and store its data in the database.
    
    Args:
        file: Uploaded file object (CSV or Excel format)
        database: Database instance to store the data
        
    Returns:
        tuple: (ReturnsTable, pandas.DataFrame)
            - ReturnsTable: Database model instance containing the processed data
            - DataFrame: pandas DataFrame containing the file contents
            
    Raises:
        ValueError: If column type is not supported (numeric, datetime, or text)
    """
    try:
        filename = file.filename
        
        # Check if a table with this name already exists
        existing_table = ReturnsTable.query.filter_by(name=filename).first()
        if existing_table:
            print(f"Deleting existing table: {filename}")
            database.session.delete(existing_table)
            database.session.flush()

        # Read the file into a DataFrame
        if filename.endswith('.csv'):
            df = pd.read_csv(file, na_values=['NA','N/A','na','n/a'])
        else:
            df = pd.read_excel(file, na_values=['NA','N/A','na','n/a'])

        # Create a new ReturnsTable instance
        returns_table = ReturnsTable(name=filename)
        database.session.add(returns_table)
        database.session.flush()

        # Process columns
        for column_name in df.columns:
            column_data = df[column_name]
            
            # Date columns
            if pd.api.types.is_datetime64_any_dtype(column_data) or isinstance(column_data.iloc[0], pd.Timestamp):
                column = DateColumn(name=column_name, returns_table_id=returns_table.id)
                database.session.add(column)
                database.session.flush()
                cells = []
                for value in column_data:
                    cell = DateCell(value=pd.to_datetime(value), column_id=column.id)
                    cells.append(cell)
            # Numeric columns
            elif pd.api.types.is_numeric_dtype(column_data) and not isinstance(column_data.iloc[0], pd.Timestamp):
                column = Column(name=column_name, returns_table_id=returns_table.id)
                database.session.add(column)
                database.session.flush()
                cells = []
                for value in column_data:
                    cell = NumberCell(value=float(value) if pd.notnull(value) else None, column_id=column.id)
                    cells.append(cell)
            # Text columns 
            else:
                column = TextColumn(name=column_name, returns_table_id=returns_table.id)
                database.session.add(column)
                database.session.flush()
                cells = []
                for value in column_data:
                    if pd.isna(value):
                        cell = TextCell(value="N/A", column_id=column.id)
                    else:
                        cell = TextCell(value=str(value), column_id=column.id)
                    cells.append(cell)
            
            database.session.bulk_save_objects(cells)
                

        # Don't commit here, let the caller handle the commit
        database.session.flush()
        return returns_table, df

    except Exception as e:
        print(f"Error in extract_data_file: {str(e)}")
        raise

def convert_ReturnsTable_to_html(returns_table):
    """Convert a ReturnsTable instance to HTML table format."""
    # Get all columns and verify they exist and have cells
    columns = list(returns_table.columns)  # Convert to list to force load
    
    # Handle empty table
    if not columns:
        return '<table id="returnsTable" class="display"><thead><tr><th>No data available</th></tr></thead><tbody><tr><td>This table is empty</td></tr></tbody></table>'
    
    # Check if all columns have zero cells
    if all(len(col.cells) == 0 for col in columns):
        return '<table id="returnsTable" class="display"><thead><tr><th>No data available</th></tr></thead><tbody><tr><td>This table has no data</td></tr></tbody></table>'
    
    # Create a dictionary to store column data
    data = {column.name: [] for column in columns}
    
    # Fill in the data
    for column in columns:
        cells = list(column.cells)  # Convert to list to force load
        values = [cell.value for cell in cells if cell is not None]
        data[column.name] = values
    
    # Convert to DataFrame and then to HTML
    df = pd.DataFrame(data)
    if df.empty:
        return '<table id="returnsTable" class="display"><thead><tr><th>No data available</th></tr></thead><tbody><tr><td>No data found</td></tr></tbody></table>'
    
    html = df.to_html(
        index=False,
        table_id='returnsTable',
        classes=['display'],
        na_rep='N/A',   # Display None as "N/A"
        header=True
    )
    
    # Ensure thead is present (html tag for DataTable) 
    if '<thead>' not in html:
        html = html.replace('<tr>', '<thead><tr>', 1)
        html = html.replace('</tr>', '</tr></thead>', 1)
    
    return html

