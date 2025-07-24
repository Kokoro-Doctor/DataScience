"""
Example usage of SQL Agent
Demonstrates key features and capabilities
"""

import os
from pathlib import Path
from sql_agent import SQLAgent

def run_examples():
    """Run example queries to demonstrate the SQL Agent"""
    
    print("🤖 SQL Agent Examples")
    print("=" * 50)
    
    # Check if API key is configured
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("⚠️  Please configure your GOOGLE_API_KEY in .env file first")
        print("   Get your key from: https://makersuite.google.com/app/apikey")
        return
    
    try:
        # Initialize the agent
        print("\n🚀 Initializing SQL Agent...")
        agent = SQLAgent()
        print("✅ Agent initialized successfully!")
        
        # Example queries
        examples = [
            {
                "question": "How many customers do we have in total?",
                "description": "Simple count query"
            },
            {
                "question": "Show me the top 3 most expensive offers",
                "description": "Sorting and limiting results"
            },
            {
                "question": "How many customers are in each state?",
                "description": "Grouping and counting"
            },
            {
                "question": "Show me all active subscriptions with customer details",
                "description": "Join query with filtering"
            },
            {
                "question": "What's the total revenue from active subscriptions?",
                "description": "Aggregation with filtering"
            }
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"\n{'='*60}")
            print(f"📝 Example {i}: {example['description']}")
            print(f"❓ Question: {example['question']}")
            print("=" * 60)
            
            try:
                # Get response from agent
                response = agent.query(example['question'])
                
                # Display SQL query
                print(f"\n🔍 Generated SQL:")
                print(f"```sql\n{response['sql_query']}\n```")
                
                # Display results
                if response['success']:
                    print(f"\n✅ Query executed successfully!")
                    
                    if 'formatted_data' in response and response['formatted_data']:
                        data = response['formatted_data']
                        print(f"\n📊 Results ({len(data)} rows):")
                        
                        # Display first few rows
                        for j, row in enumerate(data[:5]):
                            print(f"   {j+1}. {row}")
                        
                        if len(data) > 5:
                            print(f"   ... and {len(data) - 5} more rows")
                    
                    # Show AI explanation
                    print(f"\n🧠 AI Explanation:")
                    print(response['explanation'])
                
                else:
                    print(f"\n❌ Query failed: {response.get('error', 'Unknown error')}")
                
            except Exception as e:
                print(f"❌ Error processing example {i}: {str(e)}")
        
        print(f"\n{'='*60}")
        print("🎉 Examples completed!")
        print("=" * 60)
        print("\n💡 Try your own questions:")
        print("   - Run: python cli_app.py")
        print("   - Or: streamlit run streamlit_app.py")
        
    except Exception as e:
        print(f"❌ Error initializing agent: {str(e)}")
        print("💡 Make sure your API key is configured and database is set up")

if __name__ == "__main__":
    run_examples()
