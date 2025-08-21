"""
Streamlit Web Interface for SQL Agent with Database Management
A user-friendly web interface for the SQL Agent powered by Gemini and LangGraph
"""

import streamlit as st
import pandas as pd
import json
import sqlite3
from pathlib import Path
import traceback
import os
import subprocess
import sys

# Import our SQL Agent
from sql_agent import SQLAgent

# Page configuration
st.set_page_config(
    page_title="SQL Agent - Powered by Gemini & LangGraph",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Multi-page navigation
def main():
    # Sidebar navigation
    st.sidebar.title("🤖 SQL Agent Suite")
    st.sidebar.markdown("---")
    
    page = st.sidebar.selectbox(
        "🧭 Choose a page:",
        ["🔍 Query Interface", "🗃️ Database Manager"],
        help="Select between querying the database or managing the data directly"
    )
    
    # Page routing
    if page == "🔍 Query Interface":
        query_interface()
    elif page == "🗃️ Database Manager":
        database_manager_launcher()

def database_manager_launcher():
    """Load the database management interface launcher"""
    
    # Custom CSS
    st.markdown("""
    <style>
        .launcher-header {
            background: linear-gradient(90deg, #2E8B57 0%, #228B22 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .feature-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid #e0e6ed;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="launcher-header">
        <h1>🗃️ Database Management</h1>
        <p>Complete CRUD operations for your SQL Agent database</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Features overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🔍 View & Browse</h3>
            <ul>
                <li>Browse all tables and data</li>
                <li>Pagination for large datasets</li>
                <li>Export data to CSV</li>
                <li>Real-time table statistics</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>✏️ Edit & Manage</h3>
            <ul>
                <li>Add new records with validation</li>
                <li>Update existing records</li>
                <li>Delete records safely</li>
                <li>Execute custom SQL queries</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 🚀 Launch Database Manager")
    
    st.markdown("""
    **The Database Management Interface is available as a separate application for better performance.**
    
    Choose one of the options below to access the full database management features:
    """)
    
    # Option 1: Auto launch
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔄 Auto Launch")
        if st.button("🚀 Launch Database Manager", type="primary", use_container_width=True):
            try:
                # Launch database manager on different port
                subprocess.Popen([
                    sys.executable, "-m", "streamlit", "run", "database_manager.py",
                    "--server.port", "8502",
                    "--server.headless", "false"
                ])
                st.success("🎉 Database Manager launched successfully!")
                st.markdown("**[🔗 Open Database Manager](http://localhost:8502)**", unsafe_allow_html=True)
                st.balloons()
            except Exception as e:
                st.error(f"Error launching Database Manager: {str(e)}")
                st.info("Please try the manual option below.")
    
    with col2:
        st.markdown("#### 💻 Manual Launch")
        st.markdown("Copy and run this command in your terminal:")
        st.code("streamlit run database_manager.py --server.port 8502", language="bash")
        st.info("💡 This will open the Database Manager on port 8502")
    
    # Quick database stats
    st.markdown("---")
    st.markdown("### 📊 Quick Database Overview")
    
    try:
        db_path = Path("database/sql_agent.db")
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📋 Total Tables", len(tables))
            
            if 'customers' in tables:
                cursor.execute("SELECT COUNT(*) FROM customers")
                customers_count = cursor.fetchone()[0]
                with col2:
                    st.metric("👥 Customers", customers_count)
            
            if 'subscriptions' in tables:
                cursor.execute("SELECT COUNT(*) FROM subscriptions WHERE status = 'active'")
                active_subs = cursor.fetchone()[0]
                with col3:
                    st.metric("✅ Active Subscriptions", active_subs)
            
            # Table details
            st.markdown("#### 📋 Available Tables")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                st.markdown(f"- **{table}**: {count} records")
            
            conn.close()
            
    except Exception as e:
        st.error(f"Error loading database stats: {str(e)}")

def query_interface():
    """Query interface page"""
    
    # Custom CSS for better styling
    st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .query-box {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e6ed;
        margin: 1rem 0;
    }
    .result-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .error-box {
        background: #f8d7da;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e6ed;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

    @st.cache_resource
    def initialize_agent():
        """Initialize the SQL Agent (cached for performance)"""
        try:
            agent = SQLAgent()
            return agent, None
        except Exception as e:
            return None, str(e)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 SQL Agent</h1>
        <p>Powered by Gemini AI & LangGraph | Ask questions about your database in natural language</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize agent
    agent, error = initialize_agent()
    
    if error:
        st.error(f"❌ Failed to initialize SQL Agent: {error}")
        st.info("💡 Make sure your database exists and API key is configured in .env file")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Database info
        st.subheader("📊 Database Schema")
        with st.expander("View Database Schema", expanded=False):
            if agent is not None:
                schema_info = agent.get_schema_info()
                st.text(schema_info)
            else:
                st.error("❌ SQL Agent is not available. Cannot display schema info.")
        
        # Example queries
        st.subheader("💡 Example Questions")
        example_questions = [
            "Show me all active customers",
            "What are the top 5 most expensive offers?",
            "How many customers are in each state?",
            "Show me revenue by subscription status",
            "Which customers have active subscriptions?",
            "Find customers in New York with active subscriptions",
            "What's the average subscription price?",
            "Show me expired subscriptions from this year",
            "List all offers available in California",
            "Which offers are location-specific?"
        ]
        
        for i, question in enumerate(example_questions, 1):
            if st.button(f"{i}. {question}", key=f"example_{i}"):
                st.session_state.selected_question = question
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Ask Your Question")
        
        # Question input
        default_question = st.session_state.get('selected_question', '')
        user_question = st.text_area(
            "Enter your question about the database:",
            value=default_question,
            height=100,
            placeholder="e.g., Show me all customers in California with active subscriptions"
        )
        
        # Query button
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        
        with col_btn1:
            query_button = st.button("🚀 Ask Agent", type="primary", use_container_width=True)
        
        with col_btn2:
            clear_button = st.button("🗑️ Clear", use_container_width=True)
        
        if clear_button:
            st.session_state.selected_question = ''
            # Clear stored results
            if 'query_results' in st.session_state:
                del st.session_state.query_results
            st.rerun()
    
    with col2:
        st.header("📈 Quick Stats")
        
        # Display database statistics
        try:
            db_path = Path("database/sql_agent.db")
            if db_path.exists():
                conn = sqlite3.connect(db_path)
                
                # Get table counts
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM customers")
                customers_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM offers")
                offers_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM subscriptions")
                subscriptions_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM subscriptions WHERE status = 'active'")
                active_subs = cursor.fetchone()[0]
                
                conn.close()
                
                # Display metrics
                st.metric("👥 Total Customers", customers_count)
                st.metric("🎯 Total Offers", offers_count)
                st.metric("📋 Total Subscriptions", subscriptions_count)
                st.metric("✅ Active Subscriptions", active_subs)
                
        except Exception as e:
            st.error(f"Error loading stats: {str(e)}")
    
    # Process query
    if query_button and user_question and user_question.strip():
        if agent is None:
            st.error("❌ SQL Agent is not available. Please check your configuration.")
        else:
            with st.spinner("🤖 AI Agent is working on your question..."):
                try:
                    # Get response from agent
                    response = agent.query(user_question)
                    
                    # Store results in session state
                    st.session_state.query_results = {
                        'query': user_question,
                        'response': response
                    }
                    
                    st.success("✅ Query completed!")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.session_state.query_results = None
    
    elif query_button and user_question and not user_question.strip():
        st.warning("⚠️ Please enter a question first!")
    
    # Display stored results from session state
    if 'query_results' in st.session_state and st.session_state.query_results:
        stored_data = st.session_state.query_results
        response = stored_data['response']
        original_query = stored_data['query']
        
        st.header("🔍 Generated SQL Query")
        st.code(response['sql_query'], language='sql')
        
        # Display results
        if response['success']:
            st.header("📊 Query Results")
            
            # Show data table if available
            if 'formatted_data' in response and response['formatted_data']:
                df = pd.DataFrame(response['formatted_data'])
                
                # Display data summary
                col_summary1, col_summary2, col_summary3 = st.columns(3)
                with col_summary1:
                    st.metric("📊 Total Rows", len(df))
                with col_summary2:
                    st.metric("📋 Columns", len(df.columns))
                with col_summary3:
                    if len(df) > 0 and df.select_dtypes(include=['number']).shape[1] > 0:
                        numeric_cols = df.select_dtypes(include=['number']).columns
                        st.metric("🔢 Numeric Columns", len(numeric_cols))
                
                # Display the data table
                st.dataframe(df, use_container_width=True, height=400)
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"query_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
                # Optional Data Visualization
                numeric_columns = df.select_dtypes(include=['number']).columns
                if len(numeric_columns) > 0:
                    st.header("📈 Data Visualization (Optional)")
                    
                    # Add button to show/hide visualization
                    show_viz = st.button("� Show Data Visualization", key="show_viz_btn")
                    
                    if show_viz or st.session_state.get('show_visualization', False):
                        st.session_state.show_visualization = True
                        
                        chart_type = st.selectbox(
                            "Choose chart type:",
                            ["Bar Chart", "Line Chart", "Area Chart", "Histogram"],
                            key="chart_type_select"
                        )
                        
                        if len(numeric_columns) >= 1:
                            if chart_type == "Bar Chart" and len(df) <= 50:
                                if len(df.columns) >= 2:
                                    x_col = st.selectbox("X-axis:", df.columns, key="x_axis_select")
                                    y_col = st.selectbox("Y-axis:", numeric_columns, key="y_axis_select")
                                    if x_col and y_col:
                                        st.bar_chart(df.set_index(x_col)[y_col])
                            
                            elif chart_type == "Line Chart" and len(numeric_columns) >= 1:
                                selected_cols = st.multiselect(
                                    "Select columns for line chart:", 
                                    numeric_columns, 
                                    default=list(numeric_columns[:3]),
                                    key="line_cols_select"
                                )
                                if selected_cols:
                                    st.line_chart(df[selected_cols])
                            
                            elif chart_type == "Area Chart" and len(numeric_columns) >= 1:
                                selected_cols = st.multiselect(
                                    "Select columns for area chart:", 
                                    numeric_columns, 
                                    default=list(numeric_columns[:3]),
                                    key="area_cols_select"
                                )
                                if selected_cols:
                                    st.area_chart(df[selected_cols])
                            
                            elif chart_type == "Histogram":
                                col_hist = st.selectbox("Column for histogram:", numeric_columns, key="hist_col_select")
                                if col_hist:
                                    st.bar_chart(df[col_hist].value_counts())
                        
                        # Button to hide visualization
                        if st.button("🔽 Hide Visualization", key="hide_viz_btn"):
                            st.session_state.show_visualization = False
                            st.rerun()
            
            else:
                # Non-SELECT query result
                query_result = response.get('query_result', {})
                if 'message' in query_result:
                    st.success(query_result['message'])
                if 'rows_affected' in query_result:
                    st.info(f"Rows affected: {query_result['rows_affected']}")
        
        else:
            # Display error
            st.header("❌ Query Error")
            error_msg = response.get('error', 'Unknown error occurred')
            st.error(f"The query failed with the following error: {error_msg}")
        
        # AI Explanation
        st.header("🧠 AI Explanation")
        st.markdown(response['explanation'])
        
        # Show raw response in expander for debugging
        with st.expander("🔧 Raw Response (Debug Info)", expanded=False):
            st.json(response, expanded=False)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>🤖 SQL Agent powered by <strong>Gemini AI</strong> & <strong>LangGraph</strong></p>
        <p>Built with ❤️ using Streamlit | Ask questions in natural language and get SQL insights!</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
