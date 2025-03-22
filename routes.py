from flask import Blueprint, render_template, request, jsonify, send_file
from models import db, ReturnsTable, Column, DateCell, FactivaArticle, DateColumn, TextColumn, TextCell
from utils import extract_data_file, convert_ReturnsTable_to_html
from parse_html_articles import parse_html_articles  
import tempfile
from chron import create_excel_from_table_data


main_blueprint = Blueprint('main', __name__)

@main_blueprint.route("/")
def index():
    tables = ReturnsTable.query.all()
    # Remove default table HTML so the client-side can load the saved table if any.
    return render_template("returnstable.html", returns_tables=tables, table_html="")

@main_blueprint.route("/get_table/<int:table_id>")
def get_table(table_id):
    try:
        returns_table = ReturnsTable.query.get(table_id)
        # Ensure the table exists
        if returns_table is None:
            return jsonify({'error': f"Table {table_id} not found"}), 404

        # Ensure the table has columns
        if not returns_table.columns:
            return jsonify({'table_html': '<table id="returnsTable" class="display"><thead><tr><th>No data available</th></tr></thead><tbody><tr><td>This table is empty</td></tr></tbody></table>'})
        
        # Use a fresh session to ensure we get the latest data
        db.session.refresh(returns_table)
        table_html = convert_ReturnsTable_to_html(returns_table)
        return jsonify({'table_html': table_html})
    except Exception as e:
        print(f"Error getting table {table_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main_blueprint.route("/", methods=["POST"])
def upload_and_display():
    if request.method == 'POST':
        try:
            uploaded_file = request.files.get('file')
            
            if not uploaded_file or uploaded_file.filename == '':
                tables = ReturnsTable.query.all()
                return render_template("returnstable.html", returns_tables=tables, error="No file selected.")

            filename = uploaded_file.filename
            if not (filename.endswith('.xlsx') or filename.endswith('.xls') or filename.endswith('.csv') or filename.endswith('.xlsm')):
                tables = ReturnsTable.query.all()
                return render_template("returnstable.html", returns_tables=tables, error="Please upload a correct file type.")

            # Start a new session for the upload
            db.session.begin()
            
            # Get the returns table and dataframe
            
            returns_table, df = extract_data_file(uploaded_file, db)
            
            # Ensure the returns_table is attached to the current session
            returns_table = db.session.merge(returns_table)
            
            print(f"Created new table: ID={returns_table.id}, Name={returns_table.name}")
            # Instead of df.to_html(...), unify the final HTML structure:
            table_html = convert_ReturnsTable_to_html(returns_table)
            
            # Get fresh list of tables
            tables = ReturnsTable.query.all()
            
            # Commit the session
            db.session.commit()
            
            # Get fresh debug info
            debug_info_html = render_template(
                'debug_info.html',
                returns_tables=tables,
                error=None
            )
            
            # Debug prints
            print(f"Tables after upload: {[f'{t.id}: {t.name}' for t in tables]}")
            table_data = [{
                'id': table.id,
                'name': f"{table.name} - Uploaded: {table.upload_time.strftime('%Y-%m-%d %H:%M:%S') if table.upload_time else 'N/A'}"
            } for table in tables]
            print(f"Sending table data: {table_data}")
            
            # Instead of returning the entire index.html, return JSON
            return jsonify({
                'table_html': table_html,
                'tables': table_data,
                'debug_info_html': debug_info_html,
                'selected_table_id': returns_table.id,
                'error': None
            })
            
        except Exception as e:
            print(f"Error in upload: {str(e)}")
            db.session.rollback()
            return jsonify({
                'table_html': '',
                'tables': [],
                'error': str(e)
            }), 500

    tables = ReturnsTable.query.all()
    # Updated template name from "index.html" to "returnstable.html"
    return render_template("returnstable.html", returns_tables=tables)

@main_blueprint.route("/chron", methods=["GET", "POST"])
def chron():
    """
    Handle the Chronology page - displays tables and enables Excel export
    GET: Renders the chron.html template with returns tables
    POST: Handles Factiva article uploads
    """
    if request.method == "POST":
        try:
            returns_table_id = request.form.get("returns_table_id")
            if not returns_table_id:
                return jsonify({"error": "No returns_table_id provided"}), 400
            returns_table_id = int(returns_table_id)
            
            factiva_files = request.files.getlist("factiva_files")
            total_articles_uploaded = 0
            
            for f in factiva_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
                    f.save(tmp.name)
                    articles = parse_html_articles(tmp.name)  
                    for art in articles:
                        new_article = FactivaArticle(
                            returns_table_id=returns_table_id,
                            headline=art["headline"],
                            author=art["author"],
                            word_count=art["word_count"],
                            publish_date=art["publish_date"],
                            source=art["source"],
                            content=art["content"]
                        )
                        db.session.add(new_article)
                        total_articles_uploaded += 1
            db.session.commit()
            
            # Query all factiva articles for the given table
            factiva_articles = FactivaArticle.query.filter_by(returns_table_id=returns_table_id).all()
            factiva_articles_data = [{"headline": article.headline, "author": article.author} 
                                     for article in factiva_articles]
            response = {
                "message": f"Factiva articles uploaded successfully ({total_articles_uploaded} articles added)",
                "factiva_articles": factiva_articles_data
            }
            return jsonify(response)
        except Exception as e:
            print("Error during Factiva processing:", str(e))
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    # GET request handling:
    returns_tables = ReturnsTable.query.all()
    return render_template("chron.html", returns_tables=returns_tables)

@main_blueprint.route("/factiva")
def factiva():
    """
    Handle the Factiva page - displays returns tables and factiva articles
    """
    returns_tables = ReturnsTable.query.all()
    
    # We don't fetch articles here - they'll be fetched via AJAX
    return render_template("factiva.html", returns_tables=returns_tables)

@main_blueprint.route("/factiva/upload", methods=["POST"])
def upload_factiva():
    """
    Handle Factiva article uploads from the factiva page
    """
    try:
        returns_table_id = request.form.get("returns_table_id")
        if not returns_table_id:
            return jsonify({"error": "No returns_table_id provided"}), 400
        returns_table_id = int(returns_table_id)
        
        factiva_files = request.files.getlist("factiva_files")
        if not factiva_files or len(factiva_files) == 0:
            return jsonify({"error": "No files provided"}), 400
            
        total_articles_uploaded = 0
        
        for f in factiva_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
                f.save(tmp.name)
                articles = parse_html_articles(tmp.name)  
                for art in articles:
                    new_article = FactivaArticle(
                        returns_table_id=returns_table_id,
                        headline=art["headline"],
                        author=art["author"],
                        word_count=art["word_count"],
                        publish_date=art["publish_date"],
                        source=art["source"],
                        content=art["content"]
                    )
                    db.session.add(new_article)
                    total_articles_uploaded += 1
        db.session.commit()
        
        # Query all factiva articles for the given table
        factiva_articles = FactivaArticle.query.filter_by(returns_table_id=returns_table_id).all()
        factiva_articles_data = [{"headline": article.headline, "author": article.author} 
                                for article in factiva_articles]
        response = {
            "message": f"Factiva articles uploaded successfully ({total_articles_uploaded} articles added)",
            "factiva_articles": factiva_articles_data
        }
        return jsonify(response)
    except Exception as e:
        print("Error during Factiva processing:", str(e))
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@main_blueprint.route("/get_column/<int:col_id>")
def get_column(col_id):
    try:
        column = Column.query.get_or_404(col_id)
        # For a simple example, display column details
        html = f"<h2>Column: {column.name}</h2>"
        # Optionally include more info about the column
        return jsonify({"html": html})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_blueprint.route("/get_columns/<int:table_id>")
def get_columns(table_id):
    try:
        returns_table = ReturnsTable.query.get_or_404(table_id)
        # Build a list of columns for the selected ReturnsTable
        options = [{'id': col.id, 'name': col.name} for col in returns_table.columns]
        return jsonify({'columns': options})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_blueprint.route("/update_datecell_acd", methods=["POST"])
def update_datecell_acd():
    try:
        data = request.get_json()
        cell_id = data.get("cell_id")
        acd_value = data.get("acd")
        if cell_id is None or acd_value is None:
            return jsonify({"error": "Missing cell_id or acd value"}), 400

        date_cell = db.session.query(DateCell).get(cell_id)
        if not date_cell:
            return jsonify({"error": "DateCell not found"}), 404

        date_cell.acd = int(acd_value)
        db.session.commit()
        return jsonify({"message": "ACD updated successfully", "acd": date_cell.acd})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@main_blueprint.route("/get_factiva_articles/<int:table_id>")
def get_factiva_articles(table_id):
    try:
        articles = FactivaArticle.query.filter_by(returns_table_id=table_id).all()
        articles_data = [{"headline": article.headline, "author": article.author} for article in articles]
        return jsonify({'factiva_articles': articles_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# New route to get full factiva article metadata
@main_blueprint.route("/get_factiva_metadata/<int:table_id>")
def get_factiva_metadata(table_id):
    try:
        articles = FactivaArticle.query.filter_by(returns_table_id=table_id).all()
        
        # Include all available metadata fields
        articles_data = [{
            "id": article.id,
            "headline": article.headline,
            "author": article.author,
            "word_count": article.word_count,
            "publish_date": article.publish_date.isoformat() if article.publish_date else None,
            "source": article.source,
            # Truncate content for preview
            "content_preview": article.content[:100] + "..." if article.content and len(article.content) > 100 else article.content
        } for article in articles]
        
        # Get available columns for the table
        columns = [
            {"id": "headline", "name": "Headline"},
            {"id": "author", "name": "Author"},
            {"id": "word_count", "name": "Word Count"},
            {"id": "publish_date", "name": "Publish Date"},
            {"id": "source", "name": "Source"},
            {"id": "content_preview", "name": "Content Preview"}
        ]
        
        return jsonify({
            'articles': articles_data,
            'columns': columns
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# New route to merge factiva data with returns table
@main_blueprint.route("/merge_factiva_data", methods=["POST"])
def merge_factiva_data():
    """
    Merge selected Factiva article fields into a returns table as new columns.
    
    This function performs a left merge between the date column in a ReturnsTable
    and the publish dates of FactivaArticles associated with that table.
    
    The merge process:
    1. Finds the DateColumn in the selected ReturnsTable
    2. Gets all FactivaArticles related to the ReturnsTable
    3. Indexes articles by their publish date for efficient lookup
    4. For each DateCell in the DateColumn, finds articles with matching publish dates
    5. Creates new TextColumns for each selected field (headline, author, etc.)
    6. For each date cell, creates a corresponding text cell with article data
       - If multiple articles match a date, uses the first one
       - If no articles match, creates an empty cell to maintain alignment
    
    POST Parameters:
        - table_id: ID of the ReturnsTable
        - selected_columns: List of article fields to include (headline, author, etc.)
    
    Returns:
        JSON with success/error message and details about the merge operation
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        table_id = data.get('table_id')
        selected_columns = data.get('selected_columns', [])
        
        print(f"MERGE REQUEST RECEIVED: table_id={table_id}, columns={selected_columns}")
        
        if not table_id or not selected_columns:
            return jsonify({"error": "Missing required fields (table_id or selected_columns)"}), 400
        
        # Phase 1: Data Collection - Get the returns table and its date column
        returns_table = ReturnsTable.query.get(table_id)
        if not returns_table:
            print(f"ERROR: Returns table not found with ID {table_id}")
            return jsonify({"error": f"Returns table not found with ID {table_id}"}), 404
        
        print(f"Processing table: {returns_table.name} (ID: {returns_table.id})")
        
        # Find the date column in the returns table (each table should have exactly one)
        date_column = None
        for col in returns_table.columns:
            if isinstance(col, DateColumn):
                date_column = col
                print(f"Found date column: {col.name}")
                break
                
        if not date_column:
            return jsonify({"error": "No date column found in returns table"}), 400
        
        # Get all factiva articles for this table using the foreign key relationship
        articles = FactivaArticle.query.filter_by(returns_table_id=table_id).all()
        if not articles:
            print(f"ERROR: No Factiva articles found for table ID {table_id}")
            return jsonify({"error": "No Factiva articles found for this table"}), 400
            
        print(f"Found {len(articles)} Factiva articles for table ID {table_id}")
        
        # Phase 2: Date Matching - Create a lookup dictionary of articles by date
        # This makes it efficient to find articles that match a specific date
        articles_by_date = {}
        for article in articles:
            # Skip articles without publish dates
            if not article.publish_date:
                continue
                
            # Use only the date part (ignore time) for matching
            article_date = article.publish_date.date()
            if article_date not in articles_by_date:
                articles_by_date[article_date] = []
            articles_by_date[article_date].append(article)
        
        print(f"Indexed articles by {len(articles_by_date)} unique dates")
        
        # Track statistics for the merge operation
        matches_made = 0
        new_columns_created = []
        
        # Map each date cell to matching articles (if any)
        # This is the core of the left join operation
        date_cell_articles = {}  # Maps DateCell ID -> list of articles with matching dates
        
        # For each cell in the date column, find articles with matching publish date
        for cell in date_column.cells:
            if not isinstance(cell, DateCell) or not cell.value:
                continue
                
            cell_date = cell.value.date()  # Get just the date part
            
            # LEFT JOIN: Find articles with matching publish date
            if cell_date in articles_by_date:
                date_cell_articles[cell.id] = articles_by_date[cell_date]
                matches_made += 1
        
        print(f"Found {matches_made} date cells with matching articles")
        
        # Phase 3: Column Creation - Create new columns with the selected article fields
        for column_id in selected_columns:
            # Skip invalid column types
            if column_id not in ["headline", "author", "word_count", "publish_date", "source", "content_preview"]:
                continue
                
            # Create a new text column for this field
            new_column = TextColumn(
                name=f"Factiva: {column_id.replace('_', ' ').title()}",
                returns_table_id=table_id
            )
            db.session.add(new_column)
            db.session.flush()  # Get the new column ID before creating cells
            new_columns_created.append(new_column)
            
            print(f"Created new column: {new_column.name}")
            
            # Phase 4: Cell Creation - For each date cell, create a corresponding text cell
            cell_count = 0
            for date_cell in date_column.cells:
                # LEFT JOIN: For dates with no matching articles, create empty cells
                # This maintains alignment between the date column and factiva data
                if date_cell.id not in date_cell_articles:
                    empty_cell = TextCell(value="", column_id=new_column.id)
                    db.session.add(empty_cell)
                    continue
                
                # If multiple articles match this date, we use the first one
                # In a more advanced implementation, you might want to include data from all matches
                article = date_cell_articles[date_cell.id][0]
                
                # Extract the selected field from the article
                if column_id == "headline":
                    value = article.headline
                elif column_id == "author":
                    value = article.author
                elif column_id == "word_count":
                    value = str(article.word_count) if article.word_count else ""
                elif column_id == "publish_date":
                    value = article.publish_date.strftime("%Y-%m-%d") if article.publish_date else ""
                elif column_id == "source":
                    value = article.source
                elif column_id == "content_preview":
                    value = article.content[:100] + "..." if article.content and len(article.content) > 100 else article.content
                else:
                    value = ""
                
                # Create the new cell with the article data
                new_cell = TextCell(
                    value=value,
                    column_id=new_column.id
                )
                db.session.add(new_cell)
                cell_count += 1
            
            print(f"Added {cell_count} cells to column {new_column.name}")
        
        # Save all changes to the database
        db.session.commit()
        
        print(f"MERGE SUCCESSFUL: Created {len(new_columns_created)} columns with {matches_made} matches")
        
        return jsonify({
            "success": True,
            "message": f"Merged data successfully. Created {len(new_columns_created)} new columns with {matches_made} date matches.",
            "columns_created": [col.name for col in new_columns_created]
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print("=============== MERGE ERROR ================")
        traceback.print_exc()
        print("==========================================")
        print(f"Error merging factiva data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@main_blueprint.route("/save_footnote", methods=["POST"])
def save_footnote():
    """
    Save a footnote for a cell or header using the new column-based approach
    """
    try:
        data = request.json
        if not data or 'element_id' not in data or 'footnote' not in data or 'table_id' not in data:
            return jsonify({"error": "Missing required fields"}), 400
            
        element_id = data.get('element_id')
        footnote_text = data.get('footnote')
        table_id = data.get('table_id')
        
        print(f"Saving footnote - element: {element_id}, table: {table_id}, text: {footnote_text[:20]}...")
        
        # Parse the element_id to get element information
        # Format: {table_type}_{element_type}_{col_index} or {table_type}_{element_type}_{row_index}_{col_index}
        parts = element_id.split('_')
        
        if len(parts) < 3:
            return jsonify({"error": f"Invalid element_id format: {element_id}"}), 400
        
        table_type = parts[0]  # 'returns' or 'chron'
        element_type = parts[1]  # 'header' or 'cell'
        
        # Handle different formats for headers vs cells
        if element_type == 'header':
            if len(parts) != 3:
                return jsonify({"error": f"Invalid header element_id: {element_id}"}), 400
            col_index = int(parts[2])
            row_index = 0  # 0 indicates header
        elif element_type == 'cell':
            if len(parts) != 4:
                return jsonify({"error": f"Invalid cell element_id: {element_id}"}), 400
            row_index = int(parts[2]) + 1  # Add 1 because 0 is reserved for header
            col_index = int(parts[3])
        else:
            return jsonify({"error": f"Unknown element type: {element_type}"}), 400
        
        # Get the returns table
        returns_table = ReturnsTable.query.get(table_id)
        if not returns_table:
            return jsonify({"error": f"Returns table with ID {table_id} not found"}), 404
        
        # Get the column by index - note this depends on column order being stable
        columns = sorted(returns_table.columns, key=lambda c: c.id)
        if col_index >= len(columns):
            return jsonify({"error": f"Column index {col_index} out of range"}), 400
            
        column = columns[col_index]
        print(f"Found column: {column.name} (ID: {column.id})")
        
        # Set the footnote
        try:
            column.set_footnote(row_index, footnote_text)
            db.session.commit()
            print(f"Footnote saved successfully")
        except Exception as e:
            db.session.rollback()
            print(f"Error in set_footnote: {str(e)}")
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        
        return jsonify({
            "success": True, 
            "message": f"Footnote saved for {element_id}", 
            "action": "updated"
        })
            
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        print(f"Error saving footnote: {str(e)}")
        return jsonify({"error": str(e)}), 500

@main_blueprint.route("/get_footnotes/<int:table_id>", methods=["GET"])
def get_footnotes(table_id):
    """
    Get all footnotes for a returns table using the new column-based approach
    """
    try:
        returns_table = ReturnsTable.query.get(table_id)
        if not returns_table:
            return jsonify({"error": f"Returns table with ID {table_id} not found"}), 404
            
        footnotes_data = {}
        
        # Get all columns for this table
        columns = sorted(returns_table.columns, key=lambda c: c.id)
        
        # Collect footnotes from each column
        for col_idx, column in enumerate(columns):
            # Header footnote
            header_footnote = column.get_footnote(0)
            if header_footnote:
                # Format: returns_header_colIndex or chron_header_colIndex
                footnotes_data[f"returns_header_{col_idx}"] = header_footnote
                footnotes_data[f"chron_header_{col_idx}"] = header_footnote
            
            # Cell footnotes
            if column.cell_footnotes:
                for cell_idx_str, footnote in column.cell_footnotes.items():
                    cell_idx = int(cell_idx_str)
                    # Format: returns_cell_rowIndex_colIndex or chron_cell_rowIndex_colIndex
                    footnotes_data[f"returns_cell_{cell_idx}_{col_idx}"] = footnote
                    footnotes_data[f"chron_cell_{cell_idx}_{col_idx}"] = footnote
        
        return jsonify({
            "success": True,
            "footnotes": footnotes_data
        })
    except Exception as e:
        print(f"Error getting footnotes: {str(e)}")
        return jsonify({"error": str(e)}), 500

@main_blueprint.route("/export_styled_excel", methods=["POST"])
def export_styled_excel():
    """
    Generate a styled Excel file from table data
    
    Expects JSON with:
    - title: String with the Excel title
    - data: Array of arrays representing table data (first row is headers)
    
    Returns:
    - Excel file as attachment
    """
    try:
        data = request.json
        if not data or 'data' not in data:
            return jsonify({"error": "No data provided"}), 400
            
        table_data = data.get('data', [])
        title = data.get('title', 'Returns Data Chronology')
        footnotes = data.get('footnotes', {})  # Get footnotes if provided
        
        # Generate Excel file with footnotes
        excel_file = create_excel_from_table_data(table_data, title, footnotes=footnotes)
        
        # Return as downloadable file
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name="styled_export.xlsx"
        )
        
    except Exception as e:
        print(f"Error generating styled Excel: {str(e)}")
        return jsonify({"error": str(e)}), 500
