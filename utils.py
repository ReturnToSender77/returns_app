import pandas as pd
from models import db, ReturnsTable, Column, DateColumn, TextColumn, NumberCell, DateCell, TextCell, FactivaColumn, FactivaCell

def extract_data_file(file, database) -> tuple[ReturnsTable, pd.DataFrame]:
    """Extract file data and store it in the database.

    This function takes an uploaded file (CSV or Excel), reads it into a pandas DataFrame,
    creates the corresponding ReturnsTable and Column models, and stores the data.
    It automatically detects and converts column types (date, numeric, and text).

    If a table with the same filename already exists, it will be deleted.

    Args:
        file: Uploaded file object (CSV or Excel format).
        database: Database instance to use for storing the data.

    Returns:
        tuple: (ReturnsTable, pandas.DataFrame)
            - ReturnsTable: Database model instance representing the processed data.
            - DataFrame: pandas DataFrame containing the file contents.

    Raises:
        ValueError: If a column type is not supported (only numeric, datetime, or text).
        Exception: If any other error occurs during file reading or data processing.
    """
    try:
        filename = file.filename
        
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
    # Include the table name in a data attribute on the table tag
    html = f"<table id='returnsTable' class='display' data-table-name='{returns_table.name}'>"
    html += "<thead><tr>"
    for col in returns_table.columns:
        html += f"<th>{col.name}</th>"
    html += "</tr></thead><tbody>"
    
    if returns_table.columns:
        num_rows = len(returns_table.columns[0].cells)
        for i in range(num_rows):
            has_acd = False
            row_cells = []
            for col in returns_table.columns:
                cell = col.cells[i] if i < len(col.cells) else None
                
                if cell is None:
                    cell_html = "<td></td>"
                elif isinstance(col, FactivaColumn) and isinstance(cell, FactivaCell):
                    # Special handling for Factiva cells - show article count
                    article_count = cell.article_count
                    display_text = cell.display_text
                    
                    # Add metadata attributes for potential JavaScript interactions
                    cell_html = (
                        f"<td class='factiva-cell' data-cell-type='factiva' "
                        f"data-cell-id='{cell.id}' data-article-count='{article_count}'>"
                        f"{display_text}"
                        "</td>"
                    )
                elif cell.discriminator == "date_cell":
                    if cell.acd == 1:
                        has_acd = True
                    cell_html = (
                        f"<td data-cell-type='date' data-cell-id='{cell.id}' data-acd='{cell.acd}'>"
                        f"{cell.value.strftime('%Y-%m-%d') if cell.value else ''}"
                        "</td>"
                    )
                else:
                    cell_html = f"<td>{cell.value}</td>"
                row_cells.append(cell_html)
            row_class = " class='acd-row'" if has_acd else ""
            html += f"<tr{row_class}>" + "".join(row_cells) + "</tr>"
    html += "</tbody></table>"
    return html

