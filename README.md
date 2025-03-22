# Returns Data Analysis & Chronology Tool

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-1.4+-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Overview

A sophisticated web application for financial returns data analysis and chronology creation. This tool allows you to:

- Upload and display returns tables from various file formats (Excel, CSV)
- Import Factiva articles and merge them with returns data
- Create customized chronological tables with drag-and-drop functionality
- Add detailed footnotes to chronology tables
- Export to styled Excel documents with proper formatting and annotations

## 🚀 Installation

### Prerequisites
- Python 3.9+
- pip

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/returns-data-chronology.git
   cd returns-data-chronology
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install required packages**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python main.py
   ```

5. **Run the application**
   ```bash
   flask run
   ```

6. **Open your browser**
   Navigate to `http://127.0.0.1:5000/`

## 🔍 Features

### Data Management
- **Returns Table Upload**: Import data from Excel, CSV, or XLSM files
- **Data Visualization**: View uploaded tables with proper formatting
- **Factiva Integration**: Import Factiva articles and link them to returns data

### Chronology Creation
- **Dual Table Interface**: Work with source data and chronology side-by-side
- **Column Selection**: Choose specific columns for your chronology
- **Drag & Drop**: Rearrange columns intuitively
- **Footnotes**: Add detailed footnotes to column headers and individual cells

### Export Options
- **Basic Excel Export**: Quick export to standard Excel format
- **Styled Excel Export**: Professional-looking exports with formatting and footnotes

## 🧩 Components

### Main Pages

| Page | Route | Description |
|------|-------|-------------|
| **Home** | `/` | Upload and view returns tables |
| **Chronology** | `/chron` | Create and export chronological tables |
| **Factiva** | `/factiva` | Upload and manage Factiva articles |

### Key JavaScript Modules

- **chron_tables.js**: Manages dual table functionality, column manipulation, and exports
- **chron_popup.js**: Handles footnote creation and management
- **factiva_merge.js**: Controls Factiva article integration
- **popup.js**: General UI popup functionality

### Backend Components

- **routes.py**: API endpoints and request handling
- **models.py**: Database models with SQLAlchemy
- **chron.py**: Excel export and formatting logic
- **utils.py**: Helper functions for data processing
- **parse_html_articles.py**: Factiva article parsing

## 🔧 Usage Guide

### Creating a Chronology

1. **Upload Returns Data**:
   - Go to the home page and upload your data file
   - The system will parse and display your data

2. **Navigate to Chronology Page**:
   - Select your returns table from the dropdown
   - The left panel shows your source data

3. **Build Your Chronology**:
   - Click on column headers in the left panel to add them to your chronology
   - Drag columns to reorder them in the right panel
   - Remove unwanted columns using the ✕ button

4. **Add Footnotes**:
   - Click on cells or headers in the chronology table (right panel)
   - Enter footnote text in the popup
   - Save to add footnotes (indicated by *)

5. **Export Your Chronology**:
   - Enter a title for your Excel export
   - Click "Export Chron" for a styled export with footnotes
   - Alternatively, use "Export to Excel" for a basic export

### Working with Factiva Articles

1. **Upload Factiva Articles**:
   - Navigate to the Factiva page or use the Factiva section on the Chronology page
   - Select your returns table
   - Upload Factiva HTML files

2. **Merge with Returns Data**:
   - Select which fields you want to include (Headline, Author, etc.)
   - Click "Merge Selected Fields"
   - The system will match articles to dates in your returns table

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/get_table/<id>` | GET | Retrieve a specific returns table |
| `/save_footnote` | POST | Save a footnote for a cell or header |
| `/get_footnotes/<id>` | GET | Get all footnotes for a table |
| `/export_styled_excel` | POST | Generate a styled Excel export |
| `/merge_factiva_data` | POST | Merge Factiva articles with returns data |

## 📁 Database Structure

The application uses SQLite with the following main tables:

- **returns_tables**: Stores uploaded returns tables
- **columns**: Tracks columns with polymorphic types (DateColumn, TextColumn)
- **base_cells**: Stores cell data with polymorphic types
- **factiva_articles**: Contains imported Factiva articles

Footnotes are stored directly with columns using:
- `header_footnote`: For column header footnotes
- `cell_footnotes`: JSON field mapping cell indices to footnote text

## 🛠️ Technical Details

### JSON Handling in SQLite

The application includes a custom `JsonEncodedDict` class that properly serializes and deserializes JSON data for SQLite storage:

```python
class JsonEncodedDict(db.TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""
    impl = db.Text
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return '{}'
        return json.dumps(value)
        
    def process_result_value(self, value, dialect):
        if value is None:
            return {}
        return json.loads(value)
```

### Excel Formatting

The `chron.py` module handles Excel export with advanced formatting:

- Custom cell styles and borders
- Merged cells for titles
- Superscript footnote markers
- Automatic column width adjustment
- Footnote section with explanations

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Contributors

- Your Name - Initial work

## 🙏 Acknowledgments

- OpenAI for assistance with development
- Factiva for article data formatting standards
