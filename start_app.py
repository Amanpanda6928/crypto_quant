#!/usr/bin/env python3
"""
Crypto Quant Trading System - Complete App Launcher
Runs both frontend and backend services
"""

import os
import sys
import subprocess
import threading
import time

def run_backend():
    """Start the backend server"""
    print("🚀 Starting Backend Server...")
    os.chdir("backend")
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--host", "127.0.0.1", 
        "--port", "8000", 
        "--reload"
    ])

def run_frontend():
    """Start the frontend server"""
    print("🌐 Starting Frontend Server...")
    time.sleep(3)  # Wait for backend to start
    os.chdir("../frontend")
    
    # Full path to npm on Windows
    npm_path = r"C:\Program Files\nodejs\npm.cmd"
    
    # Try npm with full path
    if os.path.exists(npm_path):
        subprocess.run([npm_path, "start"], shell=True)
    else:
        print(r"❌ npm not found at C:\Program Files\nodejs\npm.cmd")
        print("📥 Please install Node.js from: https://nodejs.org/")
        print("🔧 Or run manually: cd frontend && npm start")
        input("Press Enter to exit...")
        sys.exit(1)

def main():
    # Add Node.js to PATH if installed
    node_path = r"C:\Program Files\nodejs"
    if os.path.exists(node_path) and node_path not in os.environ.get("PATH", ""):
        os.environ["PATH"] = os.environ.get("PATH", "") + ";" + node_path
    
    # Get the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("📊 Crypto Quant Trading System Launcher")
    print("=" * 50)
    print("🔗 Backend: http://127.0.0.1:8000")
    print("🌐 Frontend: http://localhost:5174")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print("=" * 50)
    print("🔐 Login: Any username/password")
    print("⏳ Starting services...")
    
    # Start backend in main thread
    backend_thread = threading.Thread(target=run_backend)
    backend_thread.daemon = True
    backend_thread.start()
    
    # Start frontend in main thread (this will block)
    try:
        run_frontend()
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
