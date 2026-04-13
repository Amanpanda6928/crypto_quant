#!/usr/bin/env python3
"""Start the backend server with correct paths"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Change to backend directory for imports
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))

# Now import and run
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
