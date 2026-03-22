#!/usr/bin/env python3
"""
Quick start script for the production-ready PLC backend.
Run: python run_backend.py
"""

import sys
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("Agent4PLC - Production Backend")
    print("=" * 60)
    print("\nStarting server on http://0.0.0.0:8001")
    print("API docs: http://127.0.0.1:8001/docs")
    print("\nPress Ctrl+C to stop")
    print("=" * 60 + "\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False
    )
