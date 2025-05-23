import streamlit as st
import pandas as pd
import io
import re
from sql_analyzer import extract_tables_and_fields
from excel_handler import parse_excel_mapping
from query_rewriter import rewrite_query, process_multiple_queries
from sql_query_analyzer import SQLQueryAnalyzer, create_analysis_dataframe

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
    if 'query_analysis' not in st.session_state:
        st.session_state.query_analysis = None
    
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
                st.session_state.query_analysis = None
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
                    st.session_state.query_analysis = None
    
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
    
    # Add SQL Analysis button if query is available
    if st.session_state.query_text:
        if st.button("Analyze SQL Queries"):
            try:
                # Initialize the analyzer
                analyzer = SQLQueryAnalyzer()
                
                # Analyze the queries
                analysis_results = analyzer.analyze_multiple_queries(st.session_state.query_text)
                st.session_state.query_analysis = analysis_results
                st.session_state.error_message = ""
                
            except Exception as e:
                st.session_state.error_message = f"Error analyzing queries: {str(e)}"
                st.error(st.session_state.error_message)

    # Process button if both query and Excel data are available
    if st.session_state.query_text and st.session_state.excel_data is not None:
        if st.button("Process and Rewrite SQL Query"):
            try:
                # Track field replacements
                field_replacements = []
                
                # Store original query
                original_query = st.session_state.query_text
                
                # Also perform query analysis if not already done
                if not st.session_state.query_analysis:
                    analyzer = SQLQueryAnalyzer()
                    analysis_results = analyzer.analyze_multiple_queries(st.session_state.query_text)
                    st.session_state.query_analysis = analysis_results
                
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
                    
                    # Convert pandas Series values to Python native types
                    field_sql_str = str(field_sql) if pd.notna(field_sql) else ""
                    map_field_str = str(map_field) if pd.notna(map_field) else ""
                    table_name_str = str(table_name) if pd.notna(table_name) else ""
                    
                    # Check if this field appears in the original query
                    if field_sql_str and map_field_str:
                        pattern = r'(?<![a-zA-Z0-9_])' + re.escape(field_sql_str) + r'(?![a-zA-Z0-9_])'
                        if re.search(pattern, original_query):
                            # Determine the replacement text
                            if table_name_str and table_name_str != "nan":
                                replacement = f"{table_name_str}.{map_field_str}"
                            else:
                                replacement = map_field_str
                            
                            # Add to the list of replacements
                            field_replacements.append({
                                'Original Field': field_sql_str,
                                'Replaced With': replacement
                            })
                
                st.session_state.rewritten_query = rewritten_query
                st.session_state.field_replacements = field_replacements
                st.session_state.error_message = ""
                
            except Exception as e:
                st.session_state.error_message = f"Error rewriting query: {str(e)}"
                st.error(st.session_state.error_message)
    
    # Display SQL Analysis Results if available
    if st.session_state.query_analysis:
        st.subheader("SQL Query Analysis")
        
        # Convert analysis to DataFrame
        analysis_df = create_analysis_dataframe(st.session_state.query_analysis)
        
        # Display the analysis table
        st.dataframe(analysis_df, use_container_width=True, hide_index=True)
        
        # Add download button for analysis
        csv_data = analysis_df.to_csv(index=False)
        st.download_button(
            label="Download Analysis as CSV",
            data=csv_data,
            file_name="sql_query_analysis.csv",
            mime="text/csv"
        )
    
    # Display results in a table format if available
    if st.session_state.rewritten_query and st.session_state.field_replacements:
        st.subheader("Query Rewriting Results")
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["Comparison Table", "Original Query", "New Query", "Detailed Analysis"])
        
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
        
        with tab4:
            st.markdown("### Detailed SQL Analysis")
            if st.session_state.query_analysis:
                analysis_df = create_analysis_dataframe(st.session_state.query_analysis)
                st.dataframe(analysis_df, use_container_width=True, hide_index=True)
            else:
                st.info("Run SQL analysis to see detailed query information.")
    
    # Display error message if there is one
    if st.session_state.error_message:
        st.error(st.session_state.error_message)

if __name__ == "__main__":
    main()
