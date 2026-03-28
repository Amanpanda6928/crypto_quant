#!/usr/bin/env python3
"""
Crypto Quant Trading System - Simple Launcher
"""

import os
import sys
import subprocess

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("📊 Crypto Quant Trading System")
    print("=" * 40)
    print("🔗 Backend: http://127.0.0.1:8000")
    print("🌐 Frontend: http://localhost:3000")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print("🔐 Login: Any username/password")
    print("=" * 40)
    
    print("\n🚀 Starting services...")
    
    # Start backend
    print("▶️  Starting Backend...")
    backend_proc = subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "backend.main:app", 
        "--host", "127.0.0.1", 
        "--port", "8000", 
        "--reload"
    ])
    
    # Start frontend with command prompt
    print("▶️  Starting Frontend...")
    frontend_proc = subprocess.Popen([
        "cmd", "/c", "cd frontend && npm start"
    ])
    
    print("\n✅ Services started!")
    print("🌐 Open: http://localhost:3000")
    print("⏹️  Press Ctrl+C to stop")
    
    try:
        # Wait for processes
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down...")
        backend_proc.terminate()
        frontend_proc.terminate()

if __name__ == "__main__":
    main()
