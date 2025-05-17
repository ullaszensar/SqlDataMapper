import streamlit as st
import pandas as pd
import io
from sql_analyzer import extract_tables_and_fields
from excel_handler import parse_excel_mapping
from query_rewriter import rewrite_query

def main():
    st.set_page_config(page_title="SQL Analyzer & Rewriter", page_icon="📊", layout="wide")
    
    st.title("SQL Analyzer & Rewriter")
    st.markdown("""
    This application analyzes SQL queries, extracts tables and fields, maps them using Excel reference data, 
    and generates rewritten queries based on the mapping.
    """)
    
    # Initialize session state variables if they don't exist
    if 'query_text' not in st.session_state:
        st.session_state.query_text = ""
    if 'excel_data' not in st.session_state:
        st.session_state.excel_data = None
    if 'extracted_tables' not in st.session_state:
        st.session_state.extracted_tables = []
    if 'extracted_fields' not in st.session_state:
        st.session_state.extracted_fields = []
    if 'mappings' not in st.session_state:
        st.session_state.mappings = {}
    if 'rewritten_query' not in st.session_state:
        st.session_state.rewritten_query = ""
    if 'error_message' not in st.session_state:
        st.session_state.error_message = ""
    
    # Create a two-column layout for input
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Step 1: Input SQL Query")
        
        # Option to input SQL query via text area or file upload
        input_method = st.radio("Select input method:", ("Text Input", "File Upload"))
        
        if input_method == "Text Input":
            query_text = st.text_area("Enter your SQL query:", height=200, value=st.session_state.query_text)
            if query_text != st.session_state.query_text:
                st.session_state.query_text = query_text
                # Reset downstream data when query changes
                st.session_state.extracted_tables = []
                st.session_state.extracted_fields = []
                st.session_state.rewritten_query = ""
                st.session_state.error_message = ""
        else:
            uploaded_file = st.file_uploader("Upload a SQL file", type=["sql", "txt"])
            if uploaded_file is not None:
                # Read the file contents
                query_text = uploaded_file.getvalue().decode("utf-8")
                if query_text != st.session_state.query_text:
                    st.session_state.query_text = query_text
                    # Reset downstream data when query changes
                    st.session_state.extracted_tables = []
                    st.session_state.extracted_fields = []
                    st.session_state.rewritten_query = ""
                    st.session_state.error_message = ""
        
        if st.button("Extract Tables & Fields") and st.session_state.query_text:
            try:
                tables, fields = extract_tables_and_fields(st.session_state.query_text)
                st.session_state.extracted_tables = tables
                st.session_state.extracted_fields = fields
                st.session_state.error_message = ""
            except Exception as e:
                st.session_state.error_message = f"Error extracting tables and fields: {str(e)}"
                st.error(st.session_state.error_message)
    
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
    
    # Display extracted tables and fields if available
    if st.session_state.extracted_tables and st.session_state.extracted_fields:
        st.subheader("Step 3: Extracted SQL Components")
        
        col_tables, col_fields = st.columns(2)
        
        with col_tables:
            st.markdown("### Tables")
            for table in st.session_state.extracted_tables:
                st.write(f"- {table}")
        
        with col_fields:
            st.markdown("### Fields")
            for field in st.session_state.extracted_fields:
                st.write(f"- {field}")
    
    # Display mapping interface if both SQL components and Excel data are available
    if st.session_state.extracted_tables and st.session_state.excel_data is not None:
        st.subheader("Step 4: Map Tables and Fields")
        
        mapping_complete = True
        
        # Initialize mappings dictionary if it doesn't exist for all tables
        for table in st.session_state.extracted_tables:
            if table not in st.session_state.mappings:
                st.session_state.mappings[table] = None
        
        # Create table mappings
        st.markdown("### Table Mappings")
        for table in st.session_state.extracted_tables:
            available_targets = st.session_state.excel_data['Target Table'].unique().tolist()
            available_targets = [target for target in available_targets if pd.notna(target)]
            available_targets.insert(0, "")  # Add empty option
            
            col_label, col_select = st.columns([1, 3])
            with col_label:
                st.write(f"{table} →")
            with col_select:
                selected_mapping = st.selectbox(
                    f"Select target for {table}",
                    available_targets,
                    index=0 if st.session_state.mappings[table] is None else 
                           available_targets.index(st.session_state.mappings[table]),
                    label_visibility="collapsed",
                    key=f"mapping_{table}"
                )
                
                st.session_state.mappings[table] = selected_mapping if selected_mapping else None
                
                if st.session_state.mappings[table] is None:
                    mapping_complete = False
        
        # Display button to generate rewritten query
        if mapping_complete:
            if st.button("Generate Rewritten Query"):
                try:
                    rewritten_query = rewrite_query(
                        st.session_state.query_text,
                        st.session_state.mappings,
                        st.session_state.excel_data
                    )
                    st.session_state.rewritten_query = rewritten_query
                    st.session_state.error_message = ""
                except Exception as e:
                    st.session_state.error_message = f"Error rewriting query: {str(e)}"
                    st.error(st.session_state.error_message)
        else:
            st.warning("Please complete all table mappings to generate the rewritten query.")
    
    # Display rewritten query if available
    if st.session_state.rewritten_query:
        st.subheader("Step 5: Rewritten SQL Query")
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
