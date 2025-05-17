import streamlit as st
import pandas as pd
import io
import re
from sql_analyzer import extract_tables_and_fields
from excel_handler import parse_excel_mapping
from query_rewriter import rewrite_query, process_multiple_queries

def main():
    st.set_page_config(page_title="SQL Analyzer & Rewriter", page_icon="📊", layout="wide")
    
    st.title("SQL Analyzer & Rewriter")
    st.markdown("""
    This application processes SQL queries, extracts fields, and replaces them using Excel mapping data.
    The mapping Excel file should have three columns: "FieldSQL", "Map_Field", and "tableName".
    """)
    
    # Initialize session state variables if they don't exist
    if 'query_text' not in st.session_state:
        st.session_state.query_text = ""
    if 'excel_data' not in st.session_state:
        st.session_state.excel_data = None
    if 'extracted_fields' not in st.session_state:
        st.session_state.extracted_fields = []
    if 'rewritten_query' not in st.session_state:
        st.session_state.rewritten_query = ""
    if 'error_message' not in st.session_state:
        st.session_state.error_message = ""
    if 'field_replacements' not in st.session_state:
        st.session_state.field_replacements = []
    
    # Create a two-column layout for input
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Step 1: Input SQL Query")
        
        # Option to input SQL query via text area or file upload
        input_method = st.radio("Select input method:", ("Text Input", "File Upload"))
        
        if input_method == "Text Input":
            query_text = st.text_area("Enter your SQL query (multiple queries separated by semicolons are supported):", 
                                     height=200, value=st.session_state.query_text)
            if query_text != st.session_state.query_text:
                st.session_state.query_text = query_text
                # Reset downstream data when query changes
                st.session_state.extracted_fields = []
                st.session_state.rewritten_query = ""
                st.session_state.error_message = ""
                st.session_state.field_replacements = []
        else:
            uploaded_file = st.file_uploader("Upload a SQL file", type=["sql", "txt"])
            if uploaded_file is not None:
                # Read the file contents
                query_text = uploaded_file.getvalue().decode("utf-8")
                if query_text != st.session_state.query_text:
                    st.session_state.query_text = query_text
                    # Reset downstream data when query changes
                    st.session_state.extracted_fields = []
                    st.session_state.rewritten_query = ""
                    st.session_state.error_message = ""
                    st.session_state.field_replacements = []
    
    with col2:
        st.subheader("Step 2: Import Mapping Data")
        
        uploaded_excel = st.file_uploader("Upload Excel mapping file", type=["xlsx", "xls"])
        
        if uploaded_excel is not None:
            try:
                # Parse the Excel file
                excel_data = parse_excel_mapping(uploaded_excel)
                st.session_state.excel_data = excel_data
                st.session_state.error_message = ""
                
                # Display a preview of the Excel data
                st.subheader("Excel Mapping Preview")
                st.dataframe(excel_data, height=200)
            except Exception as e:
                st.session_state.error_message = f"Error parsing Excel file: {str(e)}"
                st.error(st.session_state.error_message)
    
    # Process button if both query and Excel data are available
    if st.session_state.query_text and st.session_state.excel_data is not None:
        if st.button("Process and Rewrite SQL Query"):
            try:
                # Track field replacements
                field_replacements = []
                
                # Store original query
                original_query = st.session_state.query_text
                
                # Process the rewriting
                rewritten_query = process_multiple_queries(
                    st.session_state.query_text,
                    st.session_state.excel_data
                )
                
                # Identify which fields were replaced
                for _, row in st.session_state.excel_data.iterrows():
                    field_sql = row['FieldSQL']
                    map_field = row['Map_Field']
                    table_name = row['tableName']
                    
                    # Check if this field appears in the original query
                    pattern = r'(?<![a-zA-Z0-9_])' + re.escape(field_sql) + r'(?![a-zA-Z0-9_])'
                    if re.search(pattern, original_query):
                        if table_name:
                            replacement = f"{table_name}.{map_field}"
                        else:
                            replacement = map_field
                        
                        field_replacements.append({
                            'Original Field': field_sql,
                            'Replaced With': replacement
                        })
                
                st.session_state.rewritten_query = rewritten_query
                st.session_state.field_replacements = field_replacements
                st.session_state.error_message = ""
                
            except Exception as e:
                st.session_state.error_message = f"Error rewriting query: {str(e)}"
                st.error(st.session_state.error_message)
    
    # Display results in a table format if available
    if st.session_state.rewritten_query and st.session_state.field_replacements:
        st.subheader("Results")
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Comparison Table", "Original Query", "New Query"])
        
        with tab1:
            st.markdown("### Field Replacements")
            if st.session_state.field_replacements:
                st.table(pd.DataFrame(st.session_state.field_replacements))
            else:
                st.info("No field replacements were made.")
                
            # Display original and new queries side by side
            st.markdown("### Query Comparison")
            col_orig, col_new = st.columns(2)
            
            with col_orig:
                st.markdown("**Original Query:**")
                st.code(st.session_state.query_text, language="sql")
                
            with col_new:
                st.markdown("**Rewritten Query:**")
                st.code(st.session_state.rewritten_query, language="sql")
        
        with tab2:
            st.markdown("### Original SQL Query")
            st.code(st.session_state.query_text, language="sql")
            
        with tab3:
            st.markdown("### Rewritten SQL Query")
            st.code(st.session_state.rewritten_query, language="sql")
            
            # Add button to download the rewritten query
            if st.download_button(
                label="Download Rewritten Query",
                data=st.session_state.rewritten_query,
                file_name="rewritten_query.sql",
                mime="text/plain"
            ):
                st.success("Query downloaded successfully!")
    
    # Display error message if there is one
    if st.session_state.error_message:
        st.error(st.session_state.error_message)

if __name__ == "__main__":
    main()
