import pandas as pd

def parse_excel_mapping(excel_file):
    """
    Parse Excel file with mapping information.
    
    Expected columns:
    - Source Table: The original table name
    - Target Table: The table name to map to
    - Source Field: The original field name
    - Target Field: The field name to map to
    
    Args:
        excel_file: Uploaded Excel file object
        
    Returns:
        pandas.DataFrame: DataFrame with mapping information
    """
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file)
        
        # Verify required columns exist
        required_columns = ['Source Table', 'Target Table', 'Source Field', 'Target Field']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            # Try to be flexible with column names
            column_mapping = {}
            
            for req_col in required_columns:
                for col in df.columns:
                    # Try to match columns case-insensitively and with variations
                    if req_col.lower().replace(' ', '') in col.lower().replace(' ', ''):
                        column_mapping[col] = req_col
                        break
            
            # If we found matches for missing columns, rename them
            if column_mapping:
                df = df.rename(columns=column_mapping)
                
                # Check again for required columns
                missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Required columns missing from Excel file: {', '.join(missing_columns)}")
        
        # Drop rows where both source and target tables are NaN
        df = df.dropna(subset=['Source Table', 'Target Table'], how='all')
        
        # Fill NaN values in Source Field and Target Field with empty strings
        df['Source Field'] = df['Source Field'].fillna('')
        df['Target Field'] = df['Target Field'].fillna('')
        
        return df
    
    except Exception as e:
        raise Exception(f"Error parsing Excel file: {str(e)}")
