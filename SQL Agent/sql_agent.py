"""
SQL Agent using Gemini API and LangGraph
A powerful SQL agent that can query databases and explain results
"""

import sqlite3
import os
from pathlib import Path
from typing import Dict, List, Any, TypedDict, Annotated
import pandas as pd
import json
import traceback

from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

# Load environment variables
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Please set GOOGLE_API_KEY in your .env file")

genai.configure(api_key=GOOGLE_API_KEY)

class AgentState(TypedDict):
    """State of the SQL agent"""
    messages: Annotated[List[BaseMessage], "Messages in the conversation"]
    query_result: Annotated[Dict[str, Any], "Results from SQL query execution"]
    sql_query: Annotated[str, "Generated SQL query"]
    error: Annotated[str, "Error message if any"]
    explanation: Annotated[str, "Explanation of the query and results"]
    retry_count: Annotated[int, "Number of retries attempted"]

class SQLAgent:
    """SQL Agent powered by Gemini and LangGraph"""
    
    def __init__(self, db_path: str = None):
        """Initialize the SQL Agent
        
        Args:
            db_path: Path to the SQLite database
        """
        if db_path is None:
            db_path = os.getenv("DATABASE_PATH", "database/sql_agent.db")
        
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}")
            
        # Initialize Gemini model
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.1,
        )
        
        # Get database schema
        self.schema_info = self._get_database_schema()
        
        # Create the agent graph
        self.graph = self._create_agent_graph()
        
    def _get_database_schema(self) -> str:
        """Get the database schema information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            schema_info = "DATABASE SCHEMA:\n\n"
            
            for table in tables:
                schema_info += f"Table: {table}\n"
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                for col in columns:
                    col_name, col_type, not_null, default, pk = col[1], col[2], col[3], col[4], col[5]
                    constraints = []
                    if pk:
                        constraints.append("PRIMARY KEY")
                    if not_null:
                        constraints.append("NOT NULL")
                    if default:
                        constraints.append(f"DEFAULT {default}")
                    
                    constraint_str = f" ({', '.join(constraints)})" if constraints else ""
                    schema_info += f"  - {col_name}: {col_type}{constraint_str}\n"
                
                # Get sample data (first 3 rows)
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                sample_data = cursor.fetchall()
                if sample_data:
                    schema_info += f"  Sample data: {sample_data}\n"
                
                schema_info += "\n"
            
            # Get foreign key relationships
            for table in tables:
                cursor.execute(f"PRAGMA foreign_key_list({table})")
                fks = cursor.fetchall()
                if fks:
                    schema_info += f"Foreign Keys for {table}:\n"
                    for fk in fks:
                        schema_info += f"  - {fk[3]} -> {fk[2]}({fk[4]})\n"
                    schema_info += "\n"
            
            conn.close()
            return schema_info
            
        except Exception as e:
            return f"Error getting schema: {str(e)}"
    
    def _execute_sql_query(self, query: str) -> Dict[str, Any]:
        """Execute SQL query and return results"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Execute query
            cursor.execute(query)
            
            # Get results
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                # Convert to pandas DataFrame for better display
                df = pd.DataFrame(results, columns=columns)
                
                conn.close()
                
                return {
                    "success": True,
                    "data": results,
                    "columns": columns,
                    "dataframe": df,
                    "row_count": len(results),
                    "query": query
                }
            else:
                # For non-SELECT queries
                conn.commit()
                rows_affected = cursor.rowcount
                conn.close()
                
                return {
                    "success": True,
                    "message": f"Query executed successfully. Rows affected: {rows_affected}",
                    "rows_affected": rows_affected,
                    "query": query
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def _generate_sql_query(self, user_question: str) -> str:
        """Generate SQL query based on user question"""
        system_prompt = f"""You are an expert SQL query generator. 
        
Given the following database schema, generate a SQL query to answer the user's question.

{self.schema_info}

IMPORTANT RULES:
1. Only generate valid SQLite SQL queries
2. Use proper table and column names from the schema
3. Include appropriate WHERE clauses, JOINs, and aggregations as needed
4. Return ONLY the SQL query, no explanations or markdown formatting
5. Ensure the query is safe and does not modify data unless explicitly requested
6. Use proper SQL syntax for SQLite (e.g., use || for string concatenation)
7. When dealing with location-based queries, use the provided latitude/longitude columns
8. For date queries, remember SQLite stores dates as TEXT in YYYY-MM-DD format

Example questions and approaches:
- "Show all customers" -> SELECT * FROM customers
- "Find active subscriptions" -> SELECT * FROM subscriptions WHERE status = 'active'
- "Revenue by month" -> Use date functions and GROUP BY
- "Customers in specific city" -> Use WHERE clause on city column

User Question: {user_question}

SQL Query:"""

        try:
            # Create a proper prompt
            full_prompt = f"{system_prompt}"
            response = self.llm.invoke(full_prompt)
            sql_query = response.content.strip()
            
            # Clean up the response (remove markdown formatting if present)
            if sql_query.startswith('```sql'):
                sql_query = sql_query[6:]
            if sql_query.endswith('```'):
                sql_query = sql_query[:-3]
            
            return sql_query.strip()
            
        except Exception as e:
            return f"Error generating SQL: {str(e)}"
    
    def _generate_explanation(self, user_question: str, sql_query: str, query_result: Dict[str, Any]) -> str:
        """Generate explanation of the query and results"""
        
        if not query_result.get("success", False):
            return f"Query failed with error: {query_result.get('error', 'Unknown error')}"
        
        # Prepare result summary
        if "dataframe" in query_result:
            df = query_result["dataframe"]
            result_summary = f"""
Query Results Summary:
- Rows returned: {len(df)}
- Columns: {', '.join(df.columns.tolist())}

First few results:
{df.head(5).to_string(index=False) if not df.empty else 'No data returned'}
"""
        else:
            result_summary = query_result.get("message", "Query executed successfully")
        
        system_prompt = f"""You are an expert data analyst. Provide a clear, comprehensive explanation of the SQL query and its results.

Database Schema Context:
{self.schema_info}

User Question: {user_question}

SQL Query Generated:
{sql_query}

{result_summary}

Please provide:
1. A brief explanation of what the SQL query does
2. Analysis of the results (key insights, patterns, notable findings)
3. Answer to the original user question in plain English
4. Any recommendations or additional insights based on the data

Keep the explanation clear, informative, and user-friendly."""

        try:
            response = self.llm.invoke(system_prompt)
            return response.content
            
        except Exception as e:
            return f"Error generating explanation: {str(e)}"
    
    def _create_agent_graph(self) -> StateGraph:
        """Create the LangGraph agent workflow"""
        
        def query_generation_node(state: AgentState) -> AgentState:
            """Generate SQL query from user question"""
            messages = state["messages"]
            if messages:
                user_question = messages[-1].content
                sql_query = self._generate_sql_query(user_question)
                state["sql_query"] = sql_query
            return state
        
        def query_execution_node(state: AgentState) -> AgentState:
            """Execute the generated SQL query"""
            sql_query = state.get("sql_query", "")
            if sql_query:
                query_result = self._execute_sql_query(sql_query)
                state["query_result"] = query_result
                
                if not query_result.get("success", False):
                    state["error"] = query_result.get("error", "Unknown error")
            return state
        
        def explanation_node(state: AgentState) -> AgentState:
            """Generate explanation of results"""
            messages = state["messages"]
            sql_query = state.get("sql_query", "")
            query_result = state.get("query_result", {})
            
            if messages:
                user_question = messages[-1].content
                explanation = self._generate_explanation(user_question, sql_query, query_result)
                state["explanation"] = explanation
                
                # Add AI response to messages
                state["messages"].append(AIMessage(content=explanation))
            
            return state
        
        def should_retry_query(state: AgentState) -> str:
            """Decide whether to retry query generation if there was an error"""
            retry_count = state.get("retry_count", 0)
            if state.get("error") and retry_count < 2:  # Max 2 retries
                return "retry"
            return "explanation"
        
        def retry_query_node(state: AgentState) -> AgentState:
            """Retry query generation with error context"""
            messages = state["messages"]
            error = state.get("error", "")
            original_query = state.get("sql_query", "")
            retry_count = state.get("retry_count", 0)
            
            # Increment retry count
            state["retry_count"] = retry_count + 1
            
            if messages:
                user_question = messages[-1].content
                retry_prompt = f"""The previous SQL query failed with error: {error}
                
Original query: {original_query}

Please generate a corrected SQL query for: {user_question}"""
                
                sql_query = self._generate_sql_query(retry_prompt)
                state["sql_query"] = sql_query
                state["error"] = ""  # Clear the error
            
            return state
        
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("generate_query", query_generation_node)
        workflow.add_node("execute_query", query_execution_node)
        workflow.add_node("retry_query", retry_query_node)
        workflow.add_node("explain_results", explanation_node)
        
        # Add edges
        workflow.set_entry_point("generate_query")
        workflow.add_edge("generate_query", "execute_query")
        workflow.add_conditional_edges(
            "execute_query",
            should_retry_query,
            {
                "retry": "retry_query",
                "explanation": "explain_results"
            }
        )
        workflow.add_edge("retry_query", "execute_query")
        workflow.add_edge("explain_results", END)
        
        return workflow.compile()
    
    def query(self, user_question: str) -> Dict[str, Any]:
        """Process a user question and return comprehensive results"""
        
        # Initial state
        initial_state = AgentState(
            messages=[HumanMessage(content=user_question)],
            query_result={},
            sql_query="",
            error="",
            explanation="",
            retry_count=0
        )
        
        try:
            # Run the graph with recursion limit
            final_state = self.graph.invoke(
                initial_state,
                config={"recursion_limit": 10}
            )
            
            # Format response
            response = {
                "user_question": user_question,
                "sql_query": final_state.get("sql_query", ""),
                "query_result": final_state.get("query_result", {}),
                "explanation": final_state.get("explanation", ""),
                "success": final_state.get("query_result", {}).get("success", False)
            }
            
            # Add formatted data if available
            if "dataframe" in final_state.get("query_result", {}):
                df = final_state["query_result"]["dataframe"]
                response["formatted_data"] = df.to_dict('records') if not df.empty else []
                response["data_summary"] = {
                    "total_rows": len(df),
                    "columns": df.columns.tolist()
                }
            
            return response
            
        except Exception as e:
            return {
                "user_question": user_question,
                "sql_query": "",
                "query_result": {"success": False, "error": str(e)},
                "explanation": f"An error occurred while processing your question: {str(e)}",
                "success": False,
                "error": str(e)
            }
    
    def get_schema_info(self) -> str:
        """Get formatted database schema information"""
        return self.schema_info

def main():
    """Example usage of the SQL Agent"""
    try:
        # Initialize the agent
        agent = SQLAgent()
        
        print("🤖 SQL Agent Initialized!")
        print("=" * 50)
        print(agent.get_schema_info())
        print("=" * 50)
        
        # Example queries
        example_questions = [
            "Show me all active customers",
            "What are the top 3 most expensive offers?",
            "How many customers are in California?",
            "Show me revenue by subscription status",
            "Which customers have active subscriptions?",
        ]
        
        print("\n📝 Example Questions:")
        for i, question in enumerate(example_questions, 1):
            print(f"{i}. {question}")
        
        # Interactive mode
        print("\n💬 Ask me anything about your database (type 'quit' to exit):")
        
        while True:
            user_input = input("\n🤔 Your question: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input:
                continue
            
            print("\n🔄 Processing your question...")
            
            # Get response from agent
            response = agent.query(user_input)
            
            print(f"\n📊 SQL Query Generated:")
            print(f"```sql\n{response['sql_query']}\n```")
            
            if response['success']:
                print(f"\n✅ Query executed successfully!")
                
                # Show data if available
                if 'formatted_data' in response and response['formatted_data']:
                    print(f"\n📋 Data (showing first 10 rows):")
                    df = pd.DataFrame(response['formatted_data'])
                    print(df.head(10).to_string(index=False))
                    
                    if len(response['formatted_data']) > 10:
                        print(f"\n... and {len(response['formatted_data']) - 10} more rows")
            else:
                print(f"\n❌ Query failed: {response.get('error', 'Unknown error')}")
            
            print(f"\n🧠 AI Explanation:")
            print(response['explanation'])
            print("\n" + "=" * 80)
    
    except Exception as e:
        print(f"Error initializing SQL Agent: {str(e)}")
        print("Make sure your database is set up and API key is configured.")

if __name__ == "__main__":
    main()
