# Streamlit app launcher for PowerShell
# The protobuf compatibility fix is now built into the app

Write-Host "Starting RAG-LLM Assistant..." -ForegroundColor Green
streamlit run app.py

Read-Host "Press Enter to exit"
