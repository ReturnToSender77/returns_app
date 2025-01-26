from flask import Blueprint, render_template, request, jsonify
from models import db, ReturnsTable
from utils import extract_data_file, convert_table_to_html
import logging

main_blueprint = Blueprint('main', __name__)

@main_blueprint.route("/")
def index():
    try:
        tables = ReturnsTable.query.all()
        table_html = ""
        if tables:
            # Render the first existing table as a DataTable
            first_table = tables[0]
            db.session.refresh(first_table)
            table_html = convert_table_to_html(first_table)
        
        return render_template("index.html", returns_tables=tables, table_html=table_html)
    except Exception as e:
        return render_template("index.html", error=str(e))

@main_blueprint.route("/get_table/<int:table_id>")
def get_table(table_id):
    try:
        returns_table = ReturnsTable.query.get_or_404(table_id)
        # Ensure the table has columns
        if not returns_table.columns:
            return jsonify({'table_html': '<table id="returnsTable" class="display"><thead><tr><th>No data available</th></tr></thead><tbody><tr><td>This table is empty</td></tr></tbody></table>'})
        
        # Use a fresh session to ensure we get the latest data
        db.session.refresh(returns_table)
        table_html = convert_table_to_html(returns_table)
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
                return render_template("index.html", returns_tables=tables, error="No file selected.")

            filename = uploaded_file.filename
            if not (filename.endswith('.xlsx') or filename.endswith('.xls') or filename.endswith('.csv') or filename.endswith('.xlsm')):
                tables = ReturnsTable.query.all()
                return render_template("index.html", returns_tables=tables, error="Please upload a correct file type.")

            # Start a new session for the upload
            db.session.begin()
            
            # Get the returns table and dataframe
            returns_table, df = extract_data_file(uploaded_file)
            
            # Ensure the returns_table is attached to the current session
            returns_table = db.session.merge(returns_table)
            
            print(f"Created new table: ID={returns_table.id}, Name={returns_table.name}")
            # Instead of df.to_html(...), unify the final HTML structure:
            table_html = convert_table_to_html(returns_table)
            
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
            table_data = [{'id': table.id, 'name': table.name} for table in tables]
            print(f"Sending table data: {table_data}")
            
            # Instead of returning the entire index.html, return JSON
            return jsonify({
                'table_html': table_html,
                'tables': table_data,
                'debug_info_html': debug_info_html,
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
    return render_template("index.html", returns_tables=tables)
