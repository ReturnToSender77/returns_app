import openpyxl
from openpyxl.styles import Alignment, Border, Side, Font, NamedStyle
from openpyxl.utils import get_column_letter
import io

def format_excel_table(worksheet, data, title="Returns Data Chronology", footnotes=None, include_col_numbers=False):
    """
    Format the Excel worksheet with styling and apply footnotes
    
    Args:
        worksheet: openpyxl worksheet object
        data: 2D array of data (first row is headers)
        title: Title for the Excel file
        footnotes: Dictionary of footnotes
        include_col_numbers: Whether to include column numbers in the output
        
    Returns:
        Formatted worksheet
    """
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    
    # Process footnotes dictionary - convert from element_id format to simpler format
    processed_footnotes = {}
    if footnotes:
        for element_id, text in footnotes.items():
            if not text:  # Skip empty footnotes
                continue
                
            parts = element_id.split('_')
            if len(parts) < 3:
                continue
                
            # Only use chron table footnotes
            if parts[0] != 'chron':
                continue
                
            element_type = parts[1]  # header or cell
            
            if element_type == 'header':
                if len(parts) >= 3:
                    col_idx = int(parts[2])
                    processed_footnotes[f"header_{col_idx}"] = text
            elif element_type == 'cell' and len(parts) >= 4:
                row_idx = int(parts[2])
                col_idx = int(parts[3])
                processed_footnotes[f"cell_{row_idx}_{col_idx}"] = text
    
    # Create superscript style - fix: use vertAlign instead of superscript
    superscript = NamedStyle(name="superscript")
    superscript.font = Font(vertAlign="superscript", size=7)
    worksheet.parent.add_named_style(superscript)
    
    # Get number of original columns and calculate total columns with spacers
    orig_cols = len(data[0]) if data and len(data) > 0 else 0
    total_cols = orig_cols * 2 - 1 if orig_cols > 0 else 1  # Columns + spacers between them
    
    # Add title row, merged across all columns
    worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=total_cols)
    worksheet.cell(row=1, column=1, value=title)
    worksheet.cell(1, 1).font = Font(size=14, bold=True)
    worksheet.cell(1, 1).alignment = Alignment(horizontal='center')
    
    # Define styles
    header_font = Font(bold=True)
    bottom_border = Border(bottom=Side(style='medium'))
    
    # Starting from row 3, leaving row 2 empty
    current_row = 3
    
    # Track all footnotes to add at the bottom of the document
    all_footnotes = {}
    footnote_counter = 1
    
    # Add headers with spacing
    if data and len(data) > 0:
        headers = data[0]
        for i, header in enumerate(headers):
            # Calculate actual column (with spacers)
            col_idx = i * 2 + 1
            
            # Check if this header has a footnote
            header_id = f"header_{i}"
            if header_id in processed_footnotes and processed_footnotes[header_id]:
                # Add header with footnote marker
                cell = worksheet.cell(row=current_row, column=col_idx, value=f"{header}")
                # Add superscript footnote number in next cell
                footnote_cell = worksheet.cell(row=current_row, column=col_idx+1, value=f"{footnote_counter}")
                footnote_cell.style = "superscript"
                
                # Track the footnote
                all_footnotes[footnote_counter] = processed_footnotes[header_id]
                footnote_counter += 1
            else:
                # Add header without footnote
                cell = worksheet.cell(row=current_row, column=col_idx, value=header)
            
            cell.font = header_font
            cell.border = bottom_border
            
            # Make column wider
            col_letter = get_column_letter(col_idx)
            worksheet.column_dimensions[col_letter].width = max(len(str(header)) + 2, 12)
            
            # For spacer columns
            if i < len(headers) - 1:
                spacer_col = get_column_letter(col_idx + 1)
                worksheet.column_dimensions[spacer_col].width = 3
    
    # Add column numbers if requested
    if include_col_numbers:
        current_row += 1
        for i in range(len(headers)):
            col_idx = i * 2 + 1
            cell = worksheet.cell(row=current_row, column=col_idx, value=f"({i+1})")
            cell.font = Font(italic=True, size=9)
            cell.alignment = Alignment(horizontal='center')
        
        current_row += 1
    else:
        current_row += 1
    
    # Add data rows
    if data and len(data) > 1:
        for row_idx, row_data in enumerate(data[1:]):
            for i, cell_value in enumerate(row_data):
                col_idx = i * 2 + 1
                
                # Check if this cell has a footnote
                cell_id = f"cell_{row_idx}_{i}"
                if cell_id in processed_footnotes and processed_footnotes[cell_id]:
                    # Add cell value
                    worksheet.cell(row=current_row, column=col_idx, value=cell_value)
                    
                    # Add superscript footnote number in next cell
                    footnote_cell = worksheet.cell(row=current_row, column=col_idx+1, value=f"{footnote_counter}")
                    footnote_cell.style = "superscript"
                    
                    # Track the footnote
                    all_footnotes[footnote_counter] = processed_footnotes[cell_id]
                    footnote_counter += 1
                else:
                    # Add cell without footnote
                    worksheet.cell(row=current_row, column=col_idx, value=cell_value)
            
            current_row += 1
    
    # Add footnotes at the bottom
    if all_footnotes:
        current_row += 2  # Add some space
        worksheet.cell(row=current_row, column=1, value="Footnotes:").font = Font(bold=True)
        current_row += 1
        
        for num, text in all_footnotes.items():
            # Create a footnote that spans multiple columns for better readability
            note_cell = worksheet.cell(row=current_row, column=1, value=f"{num}. {text}")
            worksheet.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=min(5, total_cols))
            note_cell.alignment = Alignment(wrap_text=True)
            current_row += 1
    
    return worksheet

def create_excel_from_table_data(table_data, title="Returns Data Chronology", footnotes=None):
    """
    Create a styled Excel file from table data
    
    Args:
        table_data: 2D array of data (first row is headers)
        title: Title for the Excel file
        footnotes: Dictionary of footnotes
        
    Returns:
        BytesIO object containing the Excel file
    """
    # Create workbook and sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Chronology"
    
    if footnotes is None:
        footnotes = {}
    
    # Format the table with the data and footnotes
    format_excel_table(ws, table_data, title, footnotes)
    
    # Create a BytesIO object to save the workbook
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return output
