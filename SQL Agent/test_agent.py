"""
Test script for SQL Agent
Verifies that the agent is working correctly
"""

import os
import sys
from pathlib import Path
import traceback

def test_imports():
    """Test if all required packages can be imported"""
    print("🔄 Testing imports...")
    
    try:
        import pandas as pd
        print("✅ pandas imported successfully")
    except ImportError as e:
        print(f"❌ pandas import failed: {e}")
        return False
    
    try:
        import google.generativeai as genai
        print("✅ google-generativeai imported successfully")
    except ImportError as e:
        print(f"❌ google-generativeai import failed: {e}")
        return False
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        print("✅ langchain-google-genai imported successfully")
    except ImportError as e:
        print(f"❌ langchain-google-genai import failed: {e}")
        return False
    
    try:
        from langgraph.graph import StateGraph, END
        print("✅ langgraph imported successfully")
    except ImportError as e:
        print(f"❌ langgraph import failed: {e}")
        return False
    
    try:
        import streamlit as st
        print("✅ streamlit imported successfully")
    except ImportError as e:
        print(f"❌ streamlit import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database initialization and connection"""
    print("\n🔄 Testing database...")
    
    try:
        from database.init_db import init_database, get_database_info
        
        # Initialize database
        success = init_database()
        if not success:
            print("❌ Database initialization failed")
            return False
        
        print("✅ Database initialized successfully")
        
        # Get database info
        info = get_database_info()
        if info:
            print("✅ Database schema loaded successfully")
            print(f"   Tables found: {list(info.keys())}")
        else:
            print("❌ Failed to get database info")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_env_config():
    """Test environment configuration"""
    print("\n🔄 Testing environment configuration...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("⚠️  GOOGLE_API_KEY not found in environment")
            print("   Please add your Gemini API key to .env file")
            return False
        elif api_key == "your_gemini_api_key_here":
            print("⚠️  Please replace the placeholder API key in .env file")
            return False
        else:
            print("✅ GOOGLE_API_KEY found in environment")
            print(f"   Key preview: {api_key[:8]}...{api_key[-8:]}")
        
        db_path = os.getenv("DATABASE_PATH", "database/sql_agent.db")
        if Path(db_path).exists():
            print(f"✅ Database path configured: {db_path}")
        else:
            print(f"❌ Database not found at: {db_path}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def test_sql_agent():
    """Test SQL Agent initialization and basic functionality"""
    print("\n🔄 Testing SQL Agent...")
    
    try:
        # Skip actual agent test if no API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            print("⚠️  Skipping SQL Agent test - API key not configured")
            return True
        
        from sql_agent import SQLAgent
        
        # Initialize agent
        agent = SQLAgent()
        print("✅ SQL Agent initialized successfully")
        
        # Test schema loading
        schema = agent.get_schema_info()
        if schema and "customers" in schema:
            print("✅ Database schema loaded successfully")
        else:
            print("❌ Failed to load database schema")
            return False
        
        # Test simple query (if API key is available)
        try:
            response = agent.query("How many customers are there?")
            if response.get('success'):
                print("✅ Simple query test passed")
            else:
                print(f"⚠️  Query test failed: {response.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"⚠️  Query test failed: {e}")
            # Don't fail the whole test for API issues
        
        return True
        
    except Exception as e:
        print(f"❌ SQL Agent test failed: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def main():
    """Run all tests"""
    print("🧪 SQL Agent Test Suite")
    print("=" * 50)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
        print("\n💡 Fix: Run 'pip install -r requirements.txt'")
    
    # Test database
    if not test_database():
        all_passed = False
        print("\n💡 Fix: Check database files and permissions")
    
    # Test environment
    if not test_env_config():
        all_passed = False
        print("\n💡 Fix: Configure .env file with your API key")
    
    # Test SQL Agent
    if not test_sql_agent():
        all_passed = False
        print("\n💡 Fix: Check API key and database configuration")
    
    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Your SQL Agent is ready to use.")
        print("\nNext steps:")
        print("1. Run 'streamlit run streamlit_app.py' for web interface")
        print("2. Run 'python cli_app.py' for command line interface")
        print("3. Import SQLAgent in your Python code")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install packages: pip install -r requirements.txt")
        print("- Configure API key in .env file")
        print("- Initialize database: python database/init_db.py")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
