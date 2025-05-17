# SQL Analyzer & Rewriter

A Streamlit application that processes SQL queries, extracts fields, and replaces them using Excel mapping data.

## Features

- Process multiple SQL queries from a single file
- Map SQL fields to new fields using Excel data
- Add table names to fields based on mapping
- View side-by-side comparison of original and rewritten queries
- Download rewritten SQL queries

## Installation

1. Clone this repository
2. Install the required packages:

```bash
pip install streamlit pandas openpyxl sqlparse
```

3. Run the Streamlit application:

```bash
streamlit run app.py
```

## Usage

### Excel Mapping File Format

The Excel mapping file should have three columns:

1. **FieldSQL**: The original field name in the SQL query
2. **Map_Field**: The new field name to replace with
3. **tableName**: (Optional) The table name to add to the field

Example Excel mapping:

| FieldSQL | Map_Field | tableName |
|----------|-----------|-----------|
| id       | customer_id | customers |
| name     | full_name | customers |
| address  | mailing_address |  |

### Steps to Use:

1. Input SQL Query:
   - Either type/paste SQL queries directly in the text area
   - Or upload a SQL file containing one or more queries

2. Import Mapping Data:
   - Upload an Excel file with the required column format

3. Process the SQL Query:
   - Click "Process and Rewrite SQL Query" to generate the results

4. View Results:
   - See the comparison table with original fields and their replacements
   - View original and rewritten queries side by side
   - Download the rewritten query as a SQL file

## Example

### Original SQL:
```sql
SELECT id, name, address FROM users WHERE id > 10;
```

### Excel Mapping:
| FieldSQL | Map_Field | tableName |
|----------|-----------|-----------|
| id       | user_id   | users     |
| name     | full_name | users     |
| address  | location  |           |

### Rewritten SQL:
```sql
SELECT users.user_id, users.full_name, location FROM users WHERE users.user_id > 10;
```

## Dependencies

- Streamlit
- Pandas
- SQLParse
- OpenPyXL