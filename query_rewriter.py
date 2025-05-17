import sqlparse
import re
import pandas as pd
from sql_analyzer import extract_field_with_table

def rewrite_query(sql_query, mapping_df):
    """
    Rewrite SQL queries based on field mappings from Excel.
    
    Args:
        sql_query (str): Original SQL query or multiple queries
        mapping_df (pandas.DataFrame): DataFrame with field mapping information
        
    Returns:
        str: Rewritten SQL query or queries
    """
    # Parse the SQL queries
    parsed_queries = sqlparse.parse(sql_query)
    
    if not parsed_queries:
        raise ValueError("Failed to parse SQL query")
    
    rewritten_queries = []
    
    # Process each query separately
    for parsed_query in parsed_queries:
        # Get the SQL statement as a string for regex operations
        sql_str = str(parsed_query)
        
        # Replace fields based on the mapping DataFrame
        for _, row in mapping_df.iterrows():
            field_sql = row['FieldSQL']
            map_field = row['Map_Field']
            table_name = row['tableName']
            
            # Convert pandas Series values to Python native types
            field_sql_str = str(field_sql) if not pd.isna(field_sql) else ""
            map_field_str = str(map_field) if not pd.isna(map_field) else ""
            table_name_str = str(table_name) if not pd.isna(table_name) else ""
            
            if not field_sql_str or not map_field_str or field_sql_str == "nan" or map_field_str == "nan":
                continue  # Skip rows with missing required values
            
            # Pattern to match the field (can be standalone or within a function)
            field_pattern = r'(?<![a-zA-Z0-9_])' + re.escape(field_sql_str) + r'(?![a-zA-Z0-9_])'
            
            # If table name is provided, prepare the replacement with table name
            if table_name_str and table_name_str != "nan":
                replacement = f"{table_name_str}.{map_field_str}"
            else:
                replacement = map_field_str
                
            # Replace all occurrences of the field with the mapped field
            sql_str = re.sub(field_pattern, replacement, sql_str)
            
            # Handle fields inside functions
            func_pattern = r'(\w+\()' + re.escape(field_sql_str) + r'(\))'
            if table_name_str and table_name_str != "nan":
                func_replacement = f"\\1{table_name_str}.{map_field_str}\\2"
            else:
                func_replacement = f"\\1{map_field_str}\\2"
            sql_str = re.sub(func_pattern, func_replacement, sql_str)
            
            # Handle aliased fields in SELECT clause
            # Look for "field_sql AS alias" pattern
            alias_pattern = re.escape(field_sql_str) + r'\s+(?i)AS\s+([a-zA-Z0-9_]+)'
            alias_matches = re.findall(alias_pattern, sql_str)
            
            for alias in alias_matches:
                old_pattern = f"{field_sql_str} AS {alias}"
                if table_name_str and table_name_str != "nan":
                    new_pattern = f"{table_name_str}.{map_field_str} AS {alias}"
                else:
                    new_pattern = f"{map_field_str} AS {alias}"
                sql_str = sql_str.replace(old_pattern, new_pattern)
        
        # Format the SQL query for better readability
        rewritten_query = sqlparse.format(sql_str, reindent=True, keyword_case='upper')
        rewritten_queries.append(rewritten_query)
    
    # Join multiple queries with semicolons
    return '\n\n'.join(rewritten_queries)

def process_multiple_queries(sql_queries, mapping_df):
    """
    Process multiple SQL queries from a string.
    
    Args:
        sql_queries (str): String containing one or more SQL queries
        mapping_df (pandas.DataFrame): DataFrame with field mapping information
        
    Returns:
        str: Rewritten SQL queries
    """
    return rewrite_query(sql_queries, mapping_df)
