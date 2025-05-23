import sqlparse
import re
import pandas as pd
from typing import List, Dict, Any

class SQLQueryAnalyzer:
    """
    Comprehensive SQL query analyzer that extracts detailed information
    about tables, fields, joins, CRUD operations, and temporary tables.
    """
    
    def __init__(self):
        self.crud_patterns = {
            'SELECT': r'(?i)^\s*SELECT\b',
            'INSERT': r'(?i)^\s*INSERT\b',
            'UPDATE': r'(?i)^\s*UPDATE\b',
            'DELETE': r'(?i)^\s*DELETE\b',
            'CREATE': r'(?i)^\s*CREATE\b',
            'DROP': r'(?i)^\s*DROP\b',
            'ALTER': r'(?i)^\s*ALTER\b'
        }
        
        self.join_patterns = {
            'INNER JOIN': r'(?i)\bINNER\s+JOIN\b',
            'LEFT JOIN': r'(?i)\bLEFT\s+(?:OUTER\s+)?JOIN\b',
            'RIGHT JOIN': r'(?i)\bRIGHT\s+(?:OUTER\s+)?JOIN\b',
            'FULL JOIN': r'(?i)\bFULL\s+(?:OUTER\s+)?JOIN\b',
            'CROSS JOIN': r'(?i)\bCROSS\s+JOIN\b',
            'JOIN': r'(?i)\bJOIN\b'
        }
    
    def analyze_query(self, sql_query: str) -> Dict[str, Any]:
        """
        Analyze a single SQL query and extract comprehensive information.
        
        Args:
            sql_query (str): The SQL query to analyze
            
        Returns:
            Dict containing detailed analysis results
        """
        # Clean and normalize the query
        query = sql_query.strip()
        
        analysis = {
            'query': query,
            'crud_operation': self._detect_crud_operation(query),
            'tables_used': self._extract_tables(query),
            'fields_selected': self._extract_select_fields(query),
            'temp_tables': self._extract_temp_tables(query),
            'join_info': self._analyze_joins(query),
            'where_conditions': self._extract_where_conditions(query),
            'subqueries': self._detect_subqueries(query),
            'functions_used': self._extract_functions(query),
            'query_complexity': self._assess_complexity(query)
        }
        
        return analysis
    
    def analyze_multiple_queries(self, sql_content: str) -> List[Dict[str, Any]]:
        """
        Analyze multiple SQL queries from a string.
        
        Args:
            sql_content (str): String containing one or more SQL queries
            
        Returns:
            List of analysis results for each query
        """
        # Parse multiple queries
        parsed_queries = sqlparse.parse(sql_content)
        results = []
        
        for i, parsed_query in enumerate(parsed_queries):
            query_str = str(parsed_query).strip()
            if query_str:  # Skip empty queries
                analysis = self.analyze_query(query_str)
                analysis['query_number'] = i + 1
                results.append(analysis)
        
        return results
    
    def _detect_crud_operation(self, query: str) -> str:
        """Detect the type of CRUD operation."""
        for operation, pattern in self.crud_patterns.items():
            if re.search(pattern, query):
                return operation
        return 'UNKNOWN'
    
    def _extract_tables(self, query: str) -> List[str]:
        """Extract all table names from the query."""
        tables = []
        
        # FROM clause tables
        from_pattern = r'(?i)FROM\s+([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)?)'
        from_matches = re.findall(from_pattern, query)
        tables.extend(from_matches)
        
        # JOIN clause tables
        join_pattern = r'(?i)JOIN\s+([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)?)'
        join_matches = re.findall(join_pattern, query)
        tables.extend(join_matches)
        
        # INSERT INTO tables
        insert_pattern = r'(?i)INSERT\s+INTO\s+([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)?)'
        insert_matches = re.findall(insert_pattern, query)
        tables.extend(insert_matches)
        
        # UPDATE tables
        update_pattern = r'(?i)UPDATE\s+([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)?)'
        update_matches = re.findall(update_pattern, query)
        tables.extend(update_matches)
        
        # DELETE FROM tables
        delete_pattern = r'(?i)DELETE\s+FROM\s+([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)?)'
        delete_matches = re.findall(delete_pattern, query)
        tables.extend(delete_matches)
        
        # Remove duplicates and clean
        return list(set([table.strip('"`[]') for table in tables if table]))
    
    def _extract_select_fields(self, query: str) -> List[str]:
        """Extract fields from SELECT clause."""
        select_pattern = r'(?i)SELECT\s+(.*?)\s+FROM'
        select_match = re.search(select_pattern, query, re.DOTALL)
        
        if not select_match:
            return []
        
        select_clause = select_match.group(1)
        
        # Handle SELECT *
        if '*' in select_clause:
            return ['*']
        
        # Split by commas and clean
        fields = []
        field_parts = [f.strip() for f in select_clause.split(',')]
        
        for field in field_parts:
            # Remove aliases (AS keyword)
            if ' AS ' in field.upper():
                field = field.split(' AS ')[0].strip()
            
            # Extract field name from table.field format
            if '.' in field:
                field = field.split('.')[-1].strip()
            
            # Remove function wrappers
            field = re.sub(r'[a-zA-Z0-9_]+\((.*?)\)', r'\1', field)
            
            fields.append(field.strip('"`[]'))
        
        return [f for f in fields if f]
    
    def _extract_temp_tables(self, query: str) -> List[str]:
        """Extract temporary table names."""
        temp_tables = []
        
        # Common temporary table patterns
        temp_patterns = [
            r'(?i)CREATE\s+(?:TEMP|TEMPORARY)\s+TABLE\s+([a-zA-Z0-9_#@]+)',
            r'(?i)WITH\s+([a-zA-Z0-9_#@]+)\s+AS\s*\(',
            r'(?i)#([a-zA-Z0-9_]+)',  # SQL Server temp tables
            r'(?i)@@([a-zA-Z0-9_]+)'  # MySQL temp tables
        ]
        
        for pattern in temp_patterns:
            matches = re.findall(pattern, query)
            temp_tables.extend(matches)
        
        return list(set(temp_tables))
    
    def _analyze_joins(self, query: str) -> Dict[str, Any]:
        """Analyze JOIN operations in the query."""
        join_info = {
            'has_joins': False,
            'join_types': [],
            'join_count': 0,
            'joined_tables': []
        }
        
        for join_type, pattern in self.join_patterns.items():
            matches = re.findall(pattern, query)
            if matches:
                join_info['has_joins'] = True
                join_info['join_types'].append(join_type)
                join_info['join_count'] += len(matches)
        
        # Extract tables involved in joins
        join_table_pattern = r'(?i)JOIN\s+([a-zA-Z0-9_]+)'
        joined_tables = re.findall(join_table_pattern, query)
        join_info['joined_tables'] = list(set(joined_tables))
        
        return join_info
    
    def _extract_where_conditions(self, query: str) -> List[str]:
        """Extract WHERE clause conditions."""
        where_pattern = r'(?i)WHERE\s+(.*?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|\s+HAVING|$)'
        where_match = re.search(where_pattern, query, re.DOTALL)
        
        if not where_match:
            return []
        
        where_clause = where_match.group(1).strip()
        
        # Split by AND/OR but keep it simple for now
        conditions = re.split(r'(?i)\s+(?:AND|OR)\s+', where_clause)
        return [cond.strip() for cond in conditions if cond.strip()]
    
    def _detect_subqueries(self, query: str) -> int:
        """Count the number of subqueries."""
        # Count SELECT statements that are not the main one
        select_count = len(re.findall(r'(?i)\bSELECT\b', query))
        return max(0, select_count - 1)
    
    def _extract_functions(self, query: str) -> List[str]:
        """Extract SQL functions used in the query."""
        function_pattern = r'([A-Z_]+)\s*\('
        functions = re.findall(function_pattern, query.upper())
        
        # Filter out common keywords that aren't functions
        sql_keywords = {'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP'}
        functions = [f for f in functions if f not in sql_keywords]
        
        return list(set(functions))
    
    def _assess_complexity(self, query: str) -> str:
        """Assess the complexity of the query."""
        complexity_score = 0
        
        # Add points for various complexity factors
        if re.search(r'(?i)\bJOIN\b', query):
            complexity_score += 2
        if re.search(r'(?i)\bSUBQUERY\b', query) or self._detect_subqueries(query) > 0:
            complexity_score += 3
        if re.search(r'(?i)\bUNION\b', query):
            complexity_score += 2
        if re.search(r'(?i)\bGROUP\s+BY\b', query):
            complexity_score += 1
        if re.search(r'(?i)\bORDER\s+BY\b', query):
            complexity_score += 1
        if re.search(r'(?i)\bHAVING\b', query):
            complexity_score += 2
        
        # Count number of tables
        table_count = len(self._extract_tables(query))
        complexity_score += table_count
        
        if complexity_score <= 2:
            return 'Simple'
        elif complexity_score <= 5:
            return 'Medium'
        else:
            return 'Complex'

def create_analysis_dataframe(analysis_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert analysis results to a pandas DataFrame for display.
    
    Args:
        analysis_results: List of analysis dictionaries
        
    Returns:
        DataFrame with analysis results
    """
    df_data = []
    
    for result in analysis_results:
        row = {
            'Query #': result.get('query_number', ''),
            'CRUD Operation': result.get('crud_operation', ''),
            'Tables Used': ', '.join(result.get('tables_used', [])),
            'Selected Fields': ', '.join(result.get('fields_selected', [])),
            'Temporary Tables': ', '.join(result.get('temp_tables', [])),
            'Has Joins': 'Yes' if result.get('join_info', {}).get('has_joins', False) else 'No',
            'Join Types': ', '.join(result.get('join_info', {}).get('join_types', [])),
            'Join Count': result.get('join_info', {}).get('join_count', 0),
            'Subqueries': result.get('subqueries', 0),
            'Functions Used': ', '.join(result.get('functions_used', [])),
            'Complexity': result.get('query_complexity', ''),
            'Where Conditions': len(result.get('where_conditions', []))
        }
        df_data.append(row)
    
    return pd.DataFrame(df_data)