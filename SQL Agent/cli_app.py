"""
Command Line Interface for SQL Agent
Simple CLI for testing the SQL Agent functionality
"""

import sys
import os
from pathlib import Path
import pandas as pd
from sql_agent import SQLAgent

def print_banner():
    """Print application banner"""
    print("=" * 80)
    print("🤖 SQL AGENT - Powered by Gemini AI & LangGraph")
    print("=" * 80)
    print("Ask questions about your database in natural language!")
    print("Type 'help' for commands, 'quit' to exit")
    print("=" * 80)

def print_help():
    """Print help information"""
    print("\n📋 Available Commands:")
    print("  help          - Show this help message")
    print("  schema        - Display database schema")
    print("  examples      - Show example questions")
    print("  stats         - Show database statistics")
    print("  quit/exit     - Exit the application")
    print("\n💡 Or just ask a question about your database!")
    print("\nExample questions:")
    print("  - Show me all active customers")
    print("  - What are the top 5 most expensive offers?")
    print("  - How many customers are in California?")
    print("  - Show me revenue by subscription status")

def show_examples():
    """Show example questions"""
    examples = [
        "Show me all active customers",
        "What are the top 5 most expensive offers?",
        "How many customers are in each state?",
        "Show me revenue by subscription status",
        "Which customers have active subscriptions?",
        "Find customers in New York with active subscriptions",
        "What's the average subscription price?",
        "Show me expired subscriptions from this year",
        "List all offers available in California",
        "Which offers are location-specific?",
        "Show me customers who cancelled their subscriptions",
        "What's the total revenue from active subscriptions?"
    ]
    
    print("\n💡 Example Questions:")
    for i, example in enumerate(examples, 1):
        print(f"  {i:2d}. {example}")

def show_stats(agent):
    """Show database statistics"""
    try:
        stats_query = """
        SELECT 
            'Customers' as table_name, COUNT(*) as count
        FROM customers
        UNION ALL
        SELECT 
            'Offers' as table_name, COUNT(*) as count
        FROM offers
        UNION ALL
        SELECT 
            'Subscriptions' as table_name, COUNT(*) as count
        FROM subscriptions
        UNION ALL
        SELECT 
            'Active Subscriptions' as table_name, COUNT(*) as count
        FROM subscriptions WHERE status = 'active'
        """
        
        response = agent.query("Show me database statistics")
        print("\n📊 Database Statistics:")
        print("-" * 40)
        
        # Manual stats for better display
        stats_questions = [
            "How many customers are there?",
            "How many offers are there?",
            "How many total subscriptions are there?",
            "How many active subscriptions are there?"
        ]
        
        for question in stats_questions:
            result = agent.query(question)
            if result['success'] and 'formatted_data' in result:
                data = result['formatted_data']
                if data:
                    value = list(data[0].values())[0]
                    print(f"  {question.replace('How many ', '').replace(' are there?', '').title()}: {value}")
        
    except Exception as e:
        print(f"❌ Error getting stats: {str(e)}")

def format_results(response):
    """Format and display query results"""
    print(f"\n🔍 Generated SQL Query:")
    print(f"```sql")
    print(response['sql_query'])
    print(f"```")
    
    if response['success']:
        print(f"\n✅ Query executed successfully!")
        
        # Show data if available
        if 'formatted_data' in response and response['formatted_data']:
            data = response['formatted_data']
            df = pd.DataFrame(data)
            
            print(f"\n📊 Results ({len(data)} rows):")
            print("-" * 60)
            
            # Display data in a nice format
            if len(data) <= 20:
                # Show all data for small results
                print(df.to_string(index=False))
            else:
                # Show first 15 rows for large results
                print(df.head(15).to_string(index=False))
                print(f"\n... and {len(data) - 15} more rows")
                
        else:
            # Non-SELECT query result
            query_result = response.get('query_result', {})
            if 'message' in query_result:
                print(f"\n✅ {query_result['message']}")
    
    else:
        print(f"\n❌ Query failed:")
        error_msg = response.get('error', 'Unknown error occurred')
        print(f"Error: {error_msg}")
    
    print(f"\n🧠 AI Explanation:")
    print("-" * 60)
    print(response['explanation'])

def main():
    """Main CLI application"""
    
    # Initialize agent
    try:
        print("🚀 Initializing SQL Agent...")
        agent = SQLAgent()
        print("✅ SQL Agent initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize SQL Agent: {str(e)}")
        print("💡 Make sure your database exists and API key is configured.")
        return
    
    print_banner()
    
    while True:
        try:
            # Get user input
            user_input = input("\n🤔 Your question: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thanks for using SQL Agent! Goodbye!")
                break
            
            elif user_input.lower() == 'help':
                print_help()
                continue
            
            elif user_input.lower() == 'schema':
                print("\n📋 Database Schema:")
                print(agent.get_schema_info())
                continue
            
            elif user_input.lower() == 'examples':
                show_examples()
                continue
            
            elif user_input.lower() == 'stats':
                show_stats(agent)
                continue
            
            # Process as a question
            print("\n🔄 Processing your question...")
            
            try:
                response = agent.query(user_input)
                format_results(response)
                
            except Exception as e:
                print(f"❌ Error processing question: {str(e)}")
                
            print("\n" + "=" * 80)
        
        except KeyboardInterrupt:
            print("\n\n👋 Thanks for using SQL Agent! Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Thanks for using SQL Agent! Goodbye!")
            break

if __name__ == "__main__":
    main()
