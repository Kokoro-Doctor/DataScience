# 🤖 SQL Agent - Powered by Gemini AI & LangGraph

A powerful SQL agent that allows you to query databases using natural language. Built with Google's Gemini AI and LangGraph for intelligent SQL generation and data explanation.

## ✨ Features

- **Natural Language to SQL**: Ask questions in plain English, get accurate SQL queries
- **Intelligent Query Generation**: Powered by Gemini 2.0 Flash for advanced reasoning
- **Error Handling & Retry**: Automatically fixes common SQL errors
- **Data Explanation**: AI provides detailed analysis and insights about query results
- **Multiple Interfaces**: Command line, Streamlit web app, and Python API
- **Database Schema Awareness**: Understands your database structure for better queries
- **Location-based Queries**: Handles geographic and location-specific data
- **Data Visualization**: Built-in charts and graphs in the web interface

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8 or higher
- Google AI API key (for Gemini)
- SQLite database (sample provided)

### 2. Installation

1. Clone or download this repository
2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Set up your environment variables:

```bash
# Copy the .env file and add your API key
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

4. Initialize the database:

```bash
python database/init_db.py
```

### 3. Get Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file:

```
GOOGLE_API_KEY=your_api_key_here
```

## 🎯 Usage

### Option 1: Web Interface (Recommended)

Launch the Streamlit web app:

```bash
streamlit run streamlit_app.py
```

Then open your browser to `http://localhost:8501`

### Option 2: Command Line Interface

Run the CLI application:

```bash
python cli_app.py
```

### Option 3: Python API

```python
from sql_agent import SQLAgent

# Initialize the agent
agent = SQLAgent()

# Ask a question
response = agent.query("Show me all active customers in California")

# Access the results
print(f"SQL Query: {response['sql_query']}")
print(f"Results: {response['formatted_data']}")
print(f"Explanation: {response['explanation']}")
```

## 💡 Example Questions

Here are some example questions you can ask:

### Customer Queries
- "Show me all active customers"
- "How many customers are in each state?"
- "Find customers in New York with active subscriptions"
- "Which customers registered this year?"

### Offer & Subscription Queries
- "What are the top 5 most expensive offers?"
- "Show me revenue by subscription status"
- "Which offers are location-specific?"
- "List all California-exclusive offers"

### Analytics Queries
- "What's the average subscription price?"
- "Show me expired subscriptions from this year"
- "Calculate total revenue from active subscriptions"
- "Which state has the most customers?"

### Complex Queries
- "Show customers with multiple subscriptions"
- "Find offers with no active subscriptions"
- "Compare subscription rates by state"
- "Show customer lifetime value"

## 📊 Database Schema

The sample database includes three main tables:

### Customers Table
- Customer information with location data
- Fields: name, email, phone, address, coordinates
- Geographic data for location-based queries

### Offers Table
- Subscription offers with pricing and availability
- Location-specific offers with geographic restrictions
- Supports distance-based and region-based filtering

### Subscriptions Table
- Links customers to offers with status tracking
- Tracks subscription lifecycle and payments
- Supports revenue and analytics queries

## 🏗️ Architecture

The SQL Agent uses a sophisticated multi-step workflow:

1. **Query Generation**: Gemini AI converts natural language to SQL
2. **Query Execution**: Safe execution against SQLite database
3. **Error Handling**: Automatic retry with error context if queries fail
4. **Result Analysis**: AI analyzes results and provides insights
5. **Explanation Generation**: Creates user-friendly explanations

### LangGraph Workflow

```
User Question → Query Generation → Query Execution → Error Check
                     ↑                                     ↓
              Retry Generation ← ← ← ← ← ← ← ← ← ← Error? → → → → → → → Explanation
                     ↓                                     ↓
                Final Response ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← Success
```

## 🔧 Configuration

### Environment Variables

```bash
# Required: Your Gemini API key
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional: Database path (defaults to database/sql_agent.db)
DATABASE_PATH=database/sql_agent.db

# Optional: Debug mode
DEBUG=True
```

### Customization

You can customize the agent by:

1. **Modifying the database schema** in `database/schema.sql`
2. **Adding sample data** in `database/sample_data.sql`
3. **Adjusting AI prompts** in `sql_agent.py`
4. **Customizing the web interface** in `streamlit_app.py`

## 📁 Project Structure

```
sql-agent/
├── database/
│   ├── init_db.py          # Database initialization
│   ├── schema.sql          # Database schema
│   ├── sample_data.sql     # Sample data
│   └── sql_agent.db        # SQLite database (created automatically)
├── sql_agent.py            # Main SQL Agent class
├── streamlit_app.py        # Web interface
├── cli_app.py              # Command line interface
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
└── README.md              # This file
```

## 🛠️ Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   Error: Please set GOOGLE_API_KEY in your .env file
   ```
   - Solution: Get a Gemini API key and add it to `.env`

2. **Database Not Found**
   ```
   Error: Database not found at database/sql_agent.db
   ```
   - Solution: Run `python database/init_db.py`

3. **Package Import Errors**
   ```
   Error: No module named 'langgraph'
   ```
   - Solution: Run `pip install -r requirements.txt`

4. **SQL Query Errors**
   - The agent has automatic retry functionality
   - Check database schema if errors persist
   - Verify your question references existing tables/columns

### Performance Tips

- Use specific questions for better results
- The agent works best with questions about existing data
- Complex analytical queries may take longer to process
- Large result sets are automatically paginated

## 🤝 Contributing

Feel free to contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- **Google Gemini AI** for powerful language understanding
- **LangGraph** for workflow orchestration
- **Streamlit** for the beautiful web interface
- **SQLite** for the lightweight database

## 📞 Support

If you have questions or need help:

1. Check the troubleshooting section above
2. Review the example questions
3. Make sure your API key is properly configured
4. Verify the database is initialized correctly

---

**Happy Querying! 🚀**

*Ask questions in natural language and let AI handle the SQL complexity for you!*
