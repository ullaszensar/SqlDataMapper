# Installation Guide for SQL Analyzer & Rewriter

Follow these steps to set up and run the SQL Analyzer & Rewriter application.

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

## Installation Steps

1. Clone or download this repository to your local machine.

2. Install the required packages using pip:

```bash
pip install streamlit pandas openpyxl sqlparse
```

3. Run the Streamlit application:

```bash
streamlit run app.py
```

The application should now be running and accessible at http://localhost:8501 in your web browser.

## Usage

1. Prepare your SQL queries in a text file or be ready to paste them into the application.

2. Prepare an Excel mapping file with the following columns:
   - **FieldSQL**: The original field name in the SQL query
   - **Map_Field**: The new field name to replace with
   - **tableName**: (Optional) The table name to add to the field

3. Launch the application and follow the on-screen instructions:
   - Input your SQL queries
   - Upload your Excel mapping file
   - Process the queries to get the rewritten SQL

4. Review the results and download the rewritten SQL query if needed.

## Troubleshooting

- If you encounter any issues with Excel file format, ensure it's saved as .xlsx or .xls
- For field mapping issues, check that your Excel file contains all the required columns
- If a field isn't being replaced, verify that the exact field name appears in your SQL query

## Dependencies

This application relies on the following Python packages:
- streamlit
- pandas
- openpyxl
- sqlparse