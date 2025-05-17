import sqlparse
import re

def extract_tables_and_fields(sql_query):
    """
    Extract tables and fields from a SQL query.
    
    Args:
        sql_query (str): The SQL query to analyze
        
    Returns:
        tuple: (list of tables, list of fields)
    """
    # Parse the SQL query
    parsed = sqlparse.parse(sql_query)
    
    if not parsed:
        raise ValueError("Failed to parse SQL query")
    
    stmt = parsed[0]
    
    # Initialize lists to store tables and fields
    tables = []
    fields = []
    
    # Extract tables from FROM and JOIN clauses
    from_seen = False
    for token in stmt.tokens:
        # Extract tables from FROM clauses
        if token.ttype is sqlparse.tokens.Keyword and token.value.upper() == 'FROM':
            from_seen = True
            continue
        
        if from_seen and token.ttype is not sqlparse.tokens.Whitespace:
            if isinstance(token, sqlparse.sql.Identifier):
                tables.append(token.get_real_name())
                from_seen = False
            elif isinstance(token, sqlparse.sql.IdentifierList):
                for identifier in token.get_identifiers():
                    tables.append(identifier.get_real_name())
                from_seen = False
    
    # Extract tables from JOIN clauses using regex
    join_pattern = r'(?i)JOIN\s+([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)?)'
    join_tables = re.findall(join_pattern, sql_query)
    tables.extend(join_tables)
    
    # Extract fields from SELECT clause
    select_pattern = r'(?i)SELECT\s+(.*?)\s+FROM'
    select_match = re.search(select_pattern, sql_query, re.DOTALL)
    
    if select_match:
        select_clause = select_match.group(1)
        # Remove any whitespace and split by commas
        field_list = [f.strip() for f in select_clause.split(',')]
        
        for field in field_list:
            # Handle aliased fields
            if ' AS ' in field.upper():
                field = field.split(' AS ')[0].strip()
            
            # Extract the field name (remove table prefix if present)
            if '.' in field:
                field_name = field.split('.')[-1].strip()
                fields.append(field_name)
            else:
                fields.append(field.strip())
                
            # Remove any functions around fields
            field_name_pattern = r'(?i)[a-zA-Z0-9_]+\(([a-zA-Z0-9_\.]+)\)'
            func_match = re.search(field_name_pattern, field)
            if func_match:
                inner_field = func_match.group(1)
                if '.' in inner_field:
                    inner_field = inner_field.split('.')[-1]
                fields.append(inner_field)
    
    # Remove duplicates and clean the lists
    tables = list(set([table.strip('"`[]') for table in tables if table]))
    fields = list(set([field.strip('"`[]') for field in fields if field and field != '*']))
    
    return tables, fields

def extract_field_with_table(sql_query):
    """
    Extract fields with their associated tables from a SQL query.
    
    Args:
        sql_query (str): The SQL query to analyze
        
    Returns:
        list: List of (table, field) tuples
    """
    table_field_pairs = []
    
    # Find all table.field patterns
    table_field_pattern = r'([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)'
    matches = re.findall(table_field_pattern, sql_query)
    
    for table, field in matches:
        table_field_pairs.append((table.strip('"`[]'), field.strip('"`[]')))
    
    return table_field_pairs
