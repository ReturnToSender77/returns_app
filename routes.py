from flask import Blueprint, render_template, request
from models import db
from utils import extract_data_file  # Suppose we put the extraction logic in utils.py

main_blueprint = Blueprint('main', __name__)

@main_blueprint.route("/")
def index():
    return render_template("index.html")

@main_blueprint.route("/", methods=["POST"])
def upload_and_display():
    if request.method == 'POST':
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
        returns_table, df = extract_data_file(uploaded_file, db.session)

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

    # If GET request, just render the page with no table
    return render_template("index.html", table_html=None)
