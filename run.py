#!/usr/bin/env python3
"""
Crypto Quant Trading System - Launcher Script

This script ensures the system runs with the correct environment and directory.
"""

import os
import sys
import subprocess

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Change to the project root directory
    os.chdir(script_dir)

    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not running in a virtual environment")
        print("   Consider activating your virtual environment first")

    # Run the main script with all arguments passed through
    cmd = [sys.executable, "backend/main.py"] + sys.argv[1:]

    print(f"🚀 Running: {' '.join(cmd)}")
    print(f"📁 Working directory: {script_dir}")

    try:
        result = subprocess.run(cmd)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())