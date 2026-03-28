#!/usr/bin/env python3
"""
Crypto Trading System - Launcher Script
"""

import os
import sys
import subprocess

def main():
    """Main launcher with menu options"""
    print("🚀 Crypto Trading System")
    print("=" * 40)
    print("1. Train Models")
    print("2. Start Trading Server")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        print("🧠 Training models...")
        subprocess.run([sys.executable, "backend/ml/multi_train.py"])
    
    elif choice == "2":
        print("🌐 Starting trading server...")
        subprocess.run([sys.executable, "backend/run.py"])
    
    elif choice == "3":
        print("👋 Goodbye!")
        return 0
    
    else:
        print("❌ Invalid choice")
        return 1

if __name__ == "__main__":
    sys.exit(main())
