from flask import Blueprint, render_template, request, jsonify
from models import db, ReturnsTable, Column, DateCell, FactivaArticle
from utils import extract_data_file, convert_ReturnsTable_to_html
from parse_html_articles import parse_html_articles  
import tempfile


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
    Handle the uploading and processing of Factiva articles.
    This function handles both POST and GET requests:
    POST:
    - Expects a form with 'returns_table_id' and a list of 'factiva_files'.
    - Parses and saves the articles from the uploaded Factiva files into the database.
    - Returns a JSON response with a success message and the list of uploaded articles.
    GET:
    - Queries and renders the 'chron.html' template with columns, returns tables, and factiva articles.
    Returns:
        - For POST requests:
            - JSON response with a success message and the list of uploaded articles.
            - JSON response with an error message and status code 400 if 'returns_table_id' is not provided.
            - JSON response with an error message and status code 500 if an exception occurs during processing.
        - For GET requests:
            - Renders the 'chron.html' template with columns, returns tables, and factiva articles.
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
    columns = Column.query.all()
    returns_tables = ReturnsTable.query.all()
    factiva_articles = []
    return render_template("chron.html", columns=columns, returns_tables=returns_tables, factiva_articles=factiva_articles)

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
