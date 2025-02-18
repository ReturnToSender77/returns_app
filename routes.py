from flask import Blueprint, render_template, request, jsonify
import os
from datetime import datetime
from models import db, ReturnsTable, Column, FactivaArticle  # Import Column for the new route
from utils import extract_data_file, convert_ReturnsTable_to_html
from parse_html_articles import parse_html_articles

main_blueprint = Blueprint('main', __name__)

@main_blueprint.route("/")
def index():
    tables = ReturnsTable.query.all()
    table_html = ""
    if tables:
        # Render the first existing table as a DataTable
        first_table = tables[0]
        db.session.refresh(first_table)
        table_html = convert_ReturnsTable_to_html(first_table)
    
    # Updated template name from "index.html" to "returnstable.html"
    return render_template("returnstable.html", returns_tables=tables, table_html=table_html)

@main_blueprint.route("/get_table/<int:table_id>")
def get_table(table_id):
    try:
        returns_table = ReturnsTable.query.get_or_404(table_id)
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

@main_blueprint.route("/chron", methods=["GET", "POST"])
def chron():
    if request.method == "POST":
        try:
            # Use selected ReturnsTable ID provided from the form
            parent_id = request.form.get("returns_table_id")
            if not parent_id:
                return jsonify({'error': "No ReturnsTable selected for linking factiva articles."}), 400
            returns_table = ReturnsTable.query.get(parent_id)
            if not returns_table:
                return jsonify({'error': "Selected ReturnsTable does not exist."}), 400

            factiva_files = request.files.getlist('factiva_files')
            if not factiva_files or all(f.filename == '' for f in factiva_files):
                return jsonify({'error': "No files selected."}), 400

            upload_folder = os.path.join(os.getcwd(), "uploads", "factiva")
            os.makedirs(upload_folder, exist_ok=True)
            uploaded_paths = []

            for factiva_file in factiva_files:
                if not factiva_file.filename.endswith('.html'):
                    continue  # Skip non-html files
                file_path = os.path.join(upload_folder, factiva_file.filename)
                factiva_file.save(file_path)
                uploaded_paths.append(file_path)
                
                # Parse articles from the saved file and attach them to the selected ReturnsTable
                articles_data = parse_html_articles(file_path)
                for article in articles_data:
                    new_article = FactivaArticle(
                        returns_table_id=returns_table.id,
                        article_id=article["id"],
                        headline=article["headline"],
                        author=article["author"],
                        word_count=article["word_count"],
                        publish_date=article["publish_date"],
                        source=article["source"],
                        content=article["content"]
                    )
                    db.session.add(new_article)
            if not uploaded_paths:
                return jsonify({'error': "No valid HTML files uploaded."}), 400

            db.session.commit()

            articles = FactivaArticle.query.filter_by(returns_table_id=returns_table.id)\
                                            .order_by(FactivaArticle.id.asc()).all()
            serialized = [{
                'headline': art.headline,
                'author': art.author,
                'word_count': art.word_count,
                'publish_date': art.publish_date,
                'source': art.source
            } for art in articles]

            return jsonify({
                'message': "Factiva articles uploaded.",
                'factiva_articles': serialized
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # GET: Render Chron page normally
    columns = Column.query.all()
    returns_tables = ReturnsTable.query.all()  # Existing ReturnsTables
    # Query Factiva articles from all Factiva uploads
    factiva_articles = FactivaArticle.query.order_by(FactivaArticle.id.asc()).all()
    return render_template("chron.html",
                           columns=columns,
                           returns_tables=returns_tables,
                           factiva_articles=factiva_articles)
