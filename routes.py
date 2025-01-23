from flask import Blueprint, render_template, request, jsonify
from models import db, ReturnsTable
from utils import extract_data_file, convert_table_to_html
import logging

main_blueprint = Blueprint('main', __name__)

@main_blueprint.route("/")
def index():
    try:
        tables = ReturnsTable.query.all()
        print(f"Found {len(tables)} tables in database")  # Debug print
        for table in tables:
            print(f"Table ID: {table.id}, Name: {table.name}")  # Debug print
        return render_template("index.html", returns_tables=tables)
    except Exception as e:
        print(f"Error in index route: {str(e)}")  # Debug print
        return render_template("index.html", error=str(e))

@main_blueprint.route("/get_table/<int:table_id>")
def get_table(table_id):
    returns_table = ReturnsTable.query.get_or_404(table_id)
    table_html = convert_table_to_html(returns_table)
    return jsonify({'table_html': table_html})

@main_blueprint.route("/", methods=["POST"])
def upload_and_display():
    if request.method == 'POST':
        try:
            # Grab the file from the form
            uploaded_file = request.files.get('file')
            
            # Basic checks
            if not uploaded_file or uploaded_file.filename == '':
                return render_template("index.html", table_html="<p>No file selected.</p>")

            # Optionally ensure it's an Excel or CSV file
            filename = uploaded_file.filename
            if not (filename.endswith('.xlsx') or filename.endswith('.xls') or filename.endswith('.csv') or filename.endswith('.xlsm')):
                return render_template("index.html", table_html="<p>Please upload a correct file type. Accepted file types: .xlsx, .xls, .xlsm, or .csv file.</p>")

            # Read the file
            returns_table, df = extract_data_file(uploaded_file)
            print(f"Created new table: ID={returns_table.id}, Name={returns_table.name}")  # Debug print

            # Update the database
            db.session.add(returns_table)
            for column in returns_table.columns:
                db.session.add(column)
                for cell in column.cells:
                    db.session.add(cell)
            
            db.session.commit()

            # Convert DataFrame to HTML
            table_html = df.to_html(index=False)

            # Render template with table
            return render_template("index.html", table_html=table_html)
        except Exception as e:
            print(f"Error in upload: {str(e)}")  # Debug print
            return render_template("index.html", error=str(e))

    # If GET request, just render the page with no table
    return render_template("index.html", table_html=None)
