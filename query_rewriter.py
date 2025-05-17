import sqlparse
import re
from sql_analyzer import extract_field_with_table

def rewrite_query(sql_query, table_mappings, mapping_df):
    """
    Rewrite a SQL query based on the provided table mappings and field mappings.
    
    Args:
        sql_query (str): Original SQL query
        table_mappings (dict): Dictionary mapping source tables to target tables
        mapping_df (pandas.DataFrame): DataFrame with field mapping information
        
    Returns:
        str: Rewritten SQL query
    """
    # Create a field mapping dictionary based on the mapping DataFrame
    field_mappings = {}
    
    for _, row in mapping_df.iterrows():
        source_table = row['Source Table']
        source_field = row['Source Field']
        target_field = row['Target Field']
        
        if source_table and source_field and target_field:
            if source_table not in field_mappings:
                field_mappings[source_table] = {}
            
            field_mappings[source_table][source_field] = target_field
    
    # Parse the SQL query
    parsed = sqlparse.parse(sql_query)
    
    if not parsed:
        raise ValueError("Failed to parse SQL query")
    
    # Get the SQL statement as a string for regex operations
    sql_str = str(parsed[0])
    
    # 1. Replace table names in FROM and JOIN clauses
    for source_table, target_table in table_mappings.items():
        if not target_table:  # Skip if no mapping is provided
            continue
        
        # FROM clause pattern
        from_pattern = r'(?i)FROM\s+([`"\[]?)' + re.escape(source_table) + r'([`"\]]?)'
        sql_str = re.sub(from_pattern, f'FROM \\1{target_table}\\2', sql_str)
        
        # JOIN clause pattern
        join_pattern = r'(?i)JOIN\s+([`"\[]?)' + re.escape(source_table) + r'([`"\]]?)'
        sql_str = re.sub(join_pattern, f'JOIN \\1{target_table}\\2', sql_str)
        
        # Table alias pattern - find instances of "source_table AS alias"
        alias_pattern = r'(?i)([`"\[]?)' + re.escape(source_table) + r'([`"\]]?)\s+AS\s+([a-zA-Z0-9_]+)'
        alias_matches = re.findall(alias_pattern, sql_str)
        
        # Keep track of aliases for this table
        table_aliases = []
        for match in alias_matches:
            table_aliases.append(match[2])  # The alias is in the third group
            # Replace the table name in the "table AS alias" pattern
            pattern = r'(?i)' + re.escape(match[0]) + re.escape(source_table) + re.escape(match[1]) + r'\s+AS\s+' + re.escape(match[2])
            sql_str = re.sub(pattern, f'{match[0]}{target_table}{match[1]} AS {match[2]}', sql_str)
    
    # 2. Extract table.field pairs for replacement
    table_field_pairs = extract_field_with_table(sql_query)
    
    # 3. Replace fields in SELECT, WHERE, GROUP BY, etc.
    for source_table, source_field in table_field_pairs:
        # Get the target table
        target_table = table_mappings.get(source_table)
        
        if not target_table:
            continue  # Skip if no table mapping
        
        # Get the target field
        target_field = None
        if source_table in field_mappings and source_field in field_mappings[source_table]:
            target_field = field_mappings[source_table][source_field]
        else:
            target_field = source_field  # Keep the same field name if no mapping
        
        # Replace table.field instances
        table_field_pattern = r'([`"\[]?)' + re.escape(source_table) + r'([`"\]]?)\.([`"\[]?)' + re.escape(source_field) + r'([`"\]]?)'
        sql_str = re.sub(table_field_pattern, f'\\1{target_table}\\2.\\3{target_field}\\4', sql_str)
    
    # 4. Handle SELECT clause fields more carefully
    select_pattern = r'(?i)SELECT\s+(.*?)\s+FROM'
    select_match = re.search(select_pattern, sql_str, re.DOTALL)
    
    if select_match:
        select_clause = select_match.group(1)
        new_select_clause = select_clause
        
        # Split the select clause by commas
        fields = [f.strip() for f in select_clause.split(',')]
        
        for i, field in enumerate(fields):
            # Check if this is an aliased field
            as_match = re.search(r'(?i)(.*?)\s+AS\s+([a-zA-Z0-9_]+)$', field)
            
            if as_match:
                field_expr = as_match.group(1).strip()
                alias = as_match.group(2).strip()
                
                # Try to extract the table and field from field_expr
                table_field_match = re.search(r'([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)', field_expr)
                
                if table_field_match:
                    source_table = table_field_match.group(1)
                    source_field = table_field_match.group(2)
                    
                    target_table = table_mappings.get(source_table)
                    if target_table:
                        target_field = None
                        if source_table in field_mappings and source_field in field_mappings[source_table]:
                            target_field = field_mappings[source_table][source_field]
                        else:
                            target_field = source_field
                        
                        # Replace the field expression but keep the alias
                        field_expr = field_expr.replace(f"{source_table}.{source_field}", f"{target_table}.{target_field}")
                        fields[i] = f"{field_expr} AS {alias}"
        
        # Join the fields back together
        new_select_clause = ', '.join(fields)
        
        # Replace the select clause in the query
        sql_str = re.sub(select_pattern, f'SELECT {new_select_clause} FROM', sql_str, flags=re.IGNORECASE | re.DOTALL)
    
    # 5. Format the SQL query for better readability
    rewritten_query = sqlparse.format(sql_str, reindent=True, keyword_case='upper')
    
    return rewritten_query
