"""
Streamlit Web Interface for SQL Agent
A user-friendly web interface for the SQL Agent powered by Gemini and LangGraph
"""

import streamlit as st
import pandas as pd
import json
import sqlite3
from pathlib import Path
import traceback
import os

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
    st.sidebar.title("🤖 SQL Agent")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["🔍 Query Interface", "🗃️ Database Manager"]
    )
    
    if page == "🔍 Query Interface":
        query_interface()
    elif page == "🗃️ Database Manager":
        database_manager()

def database_manager():
    """Load the database management interface"""
    import subprocess
    import sys
    
    st.title("🗃️ Database Management")
    st.markdown("""
    **Database Management Interface is available as a separate application.**
    
    To access the full database management features, please run the following command in your terminal:
    """)
    
    st.code("streamlit run database_manager.py --server.port 8502", language="bash")
    
    st.markdown("""
    Or click the button below to launch it automatically:
    """)
    
    if st.button("🚀 Launch Database Manager", type="primary"):
        try:
            # Launch database manager on different port
            subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", "database_manager.py",
                "--server.port", "8502",
                "--server.headless", "true"
            ])
            st.success("🎉 Database Manager launched on http://localhost:8502")
            st.markdown("[🔗 Open Database Manager](http://localhost:8502)")
        except Exception as e:
            st.error(f"Error launching Database Manager: {str(e)}")
            st.info("Please run manually: `streamlit run database_manager.py --server.port 8502`")

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
            schema_info = agent.get_schema_info()
            st.text(schema_info)
        
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
    if query_button and user_question.strip():
        with st.spinner("🤖 AI Agent is working on your question..."):
            try:
                # Get response from agent
                response = agent.query(user_question)
                
                # Display SQL Query
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
                        
                        # Show charts for numeric data
                        numeric_columns = df.select_dtypes(include=['number']).columns
                        if len(numeric_columns) > 0:
                            st.header("📈 Data Visualization")
                            
                            chart_type = st.selectbox(
                                "Choose chart type:",
                                ["Bar Chart", "Line Chart", "Area Chart", "Histogram"]
                            )
                            
                            if len(numeric_columns) >= 1:
                                if chart_type == "Bar Chart" and len(df) <= 50:
                                    if len(df.columns) >= 2:
                                        x_col = st.selectbox("X-axis:", df.columns)
                                        y_col = st.selectbox("Y-axis:", numeric_columns)
                                        st.bar_chart(df.set_index(x_col)[y_col])
                                
                                elif chart_type == "Line Chart" and len(numeric_columns) >= 1:
                                    st.line_chart(df[numeric_columns])
                                
                                elif chart_type == "Area Chart" and len(numeric_columns) >= 1:
                                    st.area_chart(df[numeric_columns])
                                
                                elif chart_type == "Histogram":
                                    col_hist = st.selectbox("Column for histogram:", numeric_columns)
                                    st.bar_chart(df[col_hist].value_counts())
                    
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
                
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
                st.error(f"Traceback: {traceback.format_exc()}")
    
    elif query_button and not user_question.strip():
        st.warning("⚠️ Please enter a question first!")
    
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
