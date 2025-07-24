"""
Database Management Interface for SQL Agent
A comprehensive CRUD interface for managing database records
"""

import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import traceback
from datetime import datetime, date
import json

# Import our SQL Agent for schema info
from sql_agent import SQLAgent

def get_db_connection():
    """Get database connection"""
    db_path = Path("database/sql_agent.db")
    return sqlite3.connect(db_path)

def get_table_schema(table_name):
    """Get schema information for a table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    schema = cursor.fetchall()
    conn.close()
    return schema

def get_all_tables():
    """Get list of all tables in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def get_table_data(table_name, limit=100):
    """Get data from a table with pagination"""
    conn = get_db_connection()
    query = f"SELECT * FROM {table_name} LIMIT {limit}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_table_count(table_name):
    """Get total count of records in a table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def execute_query(query, params=None):
    """Execute a query and return results"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            conn.close()
            return True, results, columns
        else:
            conn.commit()
            rows_affected = cursor.rowcount
            conn.close()
            return True, f"Query executed successfully. Rows affected: {rows_affected}", []
    except Exception as e:
        conn.close()
        return False, str(e), []

def insert_record(table_name, data):
    """Insert a new record into a table"""
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data])
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    
    return execute_query(query, list(data.values()))

def update_record(table_name, record_id, id_column, data):
    """Update an existing record"""
    set_clause = ', '.join([f"{col} = ?" for col in data.keys()])
    query = f"UPDATE {table_name} SET {set_clause} WHERE {id_column} = ?"
    
    values = list(data.values()) + [record_id]
    return execute_query(query, values)

def delete_record(table_name, record_id, id_column):
    """Delete a record from a table"""
    query = f"DELETE FROM {table_name} WHERE {id_column} = ?"
    return execute_query(query, [record_id])

def render_data_input_form(schema, existing_data=None):
    """Render input form based on table schema"""
    form_data = {}
    
    for col_info in schema:
        col_name = col_info[1]
        col_type = col_info[2]
        not_null = col_info[3]
        default_val = col_info[4]
        is_pk = col_info[5]
        
        # Skip auto-increment primary keys for insert
        if is_pk and 'AUTOINCREMENT' in str(col_type).upper():
            continue
            
        # Get existing value if updating
        existing_val = existing_data.get(col_name, '') if existing_data else ''
        
        # Determine input type based on column type
        if 'INT' in col_type.upper():
            if existing_val == '':
                existing_val = 0 if not_null else None
            form_data[col_name] = st.number_input(
                f"{col_name} {'*' if not_null else ''}",
                value=existing_val,
                help=f"Type: {col_type}, Required: {not_null}"
            )
        elif 'DECIMAL' in col_type.upper() or 'REAL' in col_type.upper():
            if existing_val == '':
                existing_val = 0.0 if not_null else None
            form_data[col_name] = st.number_input(
                f"{col_name} {'*' if not_null else ''}",
                value=float(existing_val) if existing_val is not None else 0.0,
                format="%.2f",
                help=f"Type: {col_type}, Required: {not_null}"
            )
        elif 'DATE' in col_type.upper():
            if existing_val and existing_val != '':
                try:
                    existing_val = datetime.strptime(existing_val, '%Y-%m-%d').date()
                except:
                    existing_val = date.today()
            else:
                existing_val = date.today() if not_null else None
            
            form_data[col_name] = st.date_input(
                f"{col_name} {'*' if not_null else ''}",
                value=existing_val,
                help=f"Type: {col_type}, Required: {not_null}"
            )
        elif 'BOOLEAN' in col_type.upper():
            form_data[col_name] = st.checkbox(
                f"{col_name} {'*' if not_null else ''}",
                value=bool(existing_val) if existing_val else False,
                help=f"Type: {col_type}, Required: {not_null}"
            )
        else:  # TEXT, VARCHAR, etc.
            form_data[col_name] = st.text_input(
                f"{col_name} {'*' if not_null else ''}",
                value=str(existing_val) if existing_val else '',
                help=f"Type: {col_type}, Required: {not_null}"
            )
    
    return form_data

def main():
    """Main database management interface"""
    
    st.set_page_config(
        page_title="Database Management - SQL Agent",
        page_icon="🗃️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(90deg, #2E8B57 0%, #228B22 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .table-header {
            background: #f0f2f6;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        .success-box {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        .error-box {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🗃️ Database Management</h1>
        <p>Comprehensive CRUD Interface for SQL Agent Database</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("🔧 Database Operations")
    
    # Get all tables
    try:
        tables = get_all_tables()
        if not tables:
            st.error("No tables found in the database!")
            return
    except Exception as e:
        st.error(f"Error connecting to database: {str(e)}")
        return
    
    # Table selection
    selected_table = st.sidebar.selectbox("Select Table", tables)
    
    # Operation selection
    operation = st.sidebar.radio(
        "Select Operation",
        ["📋 View Data", "➕ Add Record", "✏️ Edit Record", "🗑️ Delete Record", "📊 Custom Query"]
    )
    
    # Display table info
    if selected_table:
        st.sidebar.markdown("### 📋 Table Info")
        try:
            count = get_table_count(selected_table)
            schema = get_table_schema(selected_table)
            st.sidebar.info(f"**Records:** {count}")
            st.sidebar.info(f"**Columns:** {len(schema)}")
        except Exception as e:
            st.sidebar.error(f"Error getting table info: {str(e)}")
    
    # Main content area
    if operation == "📋 View Data":
        st.header(f"📋 View Data - {selected_table}")
        
        # Pagination controls
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            page_size = st.selectbox("Records per page", [25, 50, 100, 200], index=1)
        with col2:
            try:
                total_records = get_table_count(selected_table)
                max_page = max(1, (total_records - 1) // page_size + 1)
                page_number = st.number_input("Page", min_value=1, max_value=max_page, value=1)
                offset = (page_number - 1) * page_size
            except:
                offset = 0
                total_records = 0
        
        try:
            # Get data with pagination
            conn = get_db_connection()
            query = f"SELECT * FROM {selected_table} LIMIT {page_size} OFFSET {offset}"
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df.empty:
                st.dataframe(df, use_container_width=True, height=400)
                st.info(f"Showing records {offset + 1} to {min(offset + page_size, total_records)} of {total_records}")
                
                # Download option
                csv = df.to_csv(index=False)
                st.download_button(
                    label=f"📥 Download {selected_table} data as CSV",
                    data=csv,
                    file_name=f"{selected_table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning(f"No data found in {selected_table}")
                
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
    
    elif operation == "➕ Add Record":
        st.header(f"➕ Add New Record - {selected_table}")
        
        try:
            schema = get_table_schema(selected_table)
            
            with st.form(f"add_form_{selected_table}"):
                st.subheader("Enter Record Details")
                form_data = render_data_input_form(schema)
                
                submitted = st.form_submit_button("➕ Add Record", type="primary")
                
                if submitted:
                    # Filter out empty values for optional fields
                    clean_data = {}
                    for key, value in form_data.items():
                        if value is not None and str(value).strip() != '':
                            if isinstance(value, date):
                                clean_data[key] = value.strftime('%Y-%m-%d')
                            else:
                                clean_data[key] = value
                    
                    if clean_data:
                        success, message, _ = insert_record(selected_table, clean_data)
                        if success:
                            st.success(f"✅ Record added successfully to {selected_table}!")
                            st.json(clean_data)
                        else:
                            st.error(f"❌ Error adding record: {message}")
                    else:
                        st.warning("Please fill in at least some fields")
        
        except Exception as e:
            st.error(f"Error setting up add form: {str(e)}")
    
    elif operation == "✏️ Edit Record":
        st.header(f"✏️ Edit Record - {selected_table}")
        
        try:
            # Get primary key column
            schema = get_table_schema(selected_table)
            pk_column = None
            for col_info in schema:
                if col_info[5]:  # is_pk
                    pk_column = col_info[1]
                    break
            
            if not pk_column:
                st.error("No primary key found for this table. Cannot edit records.")
                return
            
            # Get record to edit
            col1, col2 = st.columns([1, 3])
            with col1:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT {pk_column} FROM {selected_table} ORDER BY {pk_column}")
                    ids = [row[0] for row in cursor.fetchall()]
                    conn.close()
                    
                    if ids:
                        selected_id = st.selectbox(f"Select {pk_column}", ids)
                    else:
                        st.warning("No records found to edit")
                        return
                except Exception as e:
                    st.error(f"Error loading record IDs: {str(e)}")
                    return
            
            with col2:
                if st.button("🔍 Load Record", type="secondary"):
                    st.session_state.load_record = True
            
            # Load and edit record
            if selected_id and (st.session_state.get('load_record', False) or f'edit_data_{selected_table}' in st.session_state):
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT * FROM {selected_table} WHERE {pk_column} = ?", [selected_id])
                    record = cursor.fetchone()
                    columns = [description[0] for description in cursor.description]
                    conn.close()
                    
                    if record:
                        existing_data = dict(zip(columns, record))
                        
                        with st.form(f"edit_form_{selected_table}"):
                            st.subheader(f"Edit Record ID: {selected_id}")
                            form_data = render_data_input_form(schema, existing_data)
                            
                            submitted = st.form_submit_button("💾 Update Record", type="primary")
                            
                            if submitted:
                                # Remove primary key from update data
                                clean_data = {}
                                for key, value in form_data.items():
                                    if key != pk_column and value is not None:
                                        if isinstance(value, date):
                                            clean_data[key] = value.strftime('%Y-%m-%d')
                                        else:
                                            clean_data[key] = value
                                
                                if clean_data:
                                    success, message, _ = update_record(selected_table, selected_id, pk_column, clean_data)
                                    if success:
                                        st.success(f"✅ Record updated successfully!")
                                        st.json(clean_data)
                                        st.session_state.load_record = False
                                    else:
                                        st.error(f"❌ Error updating record: {message}")
                                else:
                                    st.warning("No changes to save")
                    else:
                        st.error("Record not found")
                        
                except Exception as e:
                    st.error(f"Error loading record: {str(e)}")
        
        except Exception as e:
            st.error(f"Error setting up edit form: {str(e)}")
    
    elif operation == "🗑️ Delete Record":
        st.header(f"🗑️ Delete Record - {selected_table}")
        
        try:
            # Get primary key column
            schema = get_table_schema(selected_table)
            pk_column = None
            for col_info in schema:
                if col_info[5]:  # is_pk
                    pk_column = col_info[1]
                    break
            
            if not pk_column:
                st.error("No primary key found for this table. Cannot delete records.")
                return
            
            # Get record to delete
            col1, col2 = st.columns([1, 1])
            with col1:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT {pk_column} FROM {selected_table} ORDER BY {pk_column}")
                    ids = [row[0] for row in cursor.fetchall()]
                    conn.close()
                    
                    if ids:
                        selected_id = st.selectbox(f"Select {pk_column} to delete", ids)
                    else:
                        st.warning("No records found to delete")
                        return
                except Exception as e:
                    st.error(f"Error loading record IDs: {str(e)}")
                    return
            
            # Show record details before deletion
            if selected_id:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT * FROM {selected_table} WHERE {pk_column} = ?", [selected_id])
                    record = cursor.fetchone()
                    columns = [description[0] for description in cursor.description]
                    conn.close()
                    
                    if record:
                        st.subheader("Record to Delete:")
                        record_dict = dict(zip(columns, record))
                        st.json(record_dict)
                        
                        # Confirmation
                        st.warning("⚠️ This action cannot be undone!")
                        confirm = st.checkbox(f"I confirm I want to delete record with {pk_column} = {selected_id}")
                        
                        if st.button("🗑️ Delete Record", type="primary", disabled=not confirm):
                            success, message, _ = delete_record(selected_table, selected_id, pk_column)
                            if success:
                                st.success(f"✅ Record deleted successfully!")
                            else:
                                st.error(f"❌ Error deleting record: {message}")
                    else:
                        st.error("Record not found")
                        
                except Exception as e:
                    st.error(f"Error loading record: {str(e)}")
        
        except Exception as e:
            st.error(f"Error setting up delete interface: {str(e)}")
    
    elif operation == "📊 Custom Query":
        st.header("📊 Custom SQL Query")
        
        st.markdown("""
        **⚠️ Warning:** Be careful with custom queries, especially UPDATE and DELETE operations.
        Always backup your data before making changes.
        """)
        
        # Query input
        query = st.text_area(
            "Enter your SQL query:",
            height=150,
            placeholder="""Examples:
SELECT * FROM customers WHERE state = 'CA';
UPDATE customers SET city = 'San Francisco' WHERE customer_id = 1;
DELETE FROM subscriptions WHERE status = 'cancelled';
"""
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            execute_btn = st.button("🚀 Execute Query", type="primary")
        
        if execute_btn and query.strip():
            try:
                success, result, columns = execute_query(query)
                
                if success:
                    if columns:  # SELECT query
                        df = pd.DataFrame(result, columns=columns)
                        st.success(f"✅ Query executed successfully! Found {len(df)} rows.")
                        
                        if not df.empty:
                            st.dataframe(df, use_container_width=True)
                            
                            # Download option
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download results as CSV",
                                data=csv,
                                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("Query returned no results")
                    else:  # INSERT/UPDATE/DELETE query
                        st.success(f"✅ {result}")
                else:
                    st.error(f"❌ Query failed: {result}")
                    
            except Exception as e:
                st.error(f"❌ Error executing query: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>🗃️ Database Management Interface | Built with ❤️ using Streamlit</p>
        <p>⚠️ Always backup your data before making changes</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
