#!/usr/bin/env python3
"""
Siko Auction Monitor - Web App Entry Point (mongodb-integration branch)
This branch only supports the web interface. Standalone monitoring has been removed.
"""

# This file is kept for backward compatibility but is no longer used for standalone monitoring.
# Use web_app.py instead via: python manage.py start-web

if __name__ == "__main__":
    print("⚠️  Standalone monitoring is not available in this branch (mongodb-integration).")
    print("    This branch only supports the web interface.")
    print("")
    print("    To start the web app, run:")
    print("    python manage.py start-web")
    print("")
    print("    For standalone monitoring, switch to the main branch.")
