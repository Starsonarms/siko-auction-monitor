#!/usr/bin/env python3
"""
Siko Auction Monitor - Management Script
Easy commands to manage your auction monitoring
"""

import os
import sys
import subprocess

def run_command(cmd):
    """Run a command in the virtual environment"""
    venv_python = os.path.join("venv", "Scripts", "python.exe") if os.name == 'nt' else os.path.join("venv", "bin", "python")
    
    if isinstance(cmd, str):
        full_cmd = f'"{venv_python}" {cmd}'
    else:
        full_cmd = [venv_python] + cmd
    
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result

def main():
    if len(sys.argv) < 2:
        print("🔨 Siko Auction Monitor - Management Script")
        print()
        print("Available commands:")
        print("  test-scraper     - Test if the auction scraper is working")
        print("  test-ha          - Test Home Assistant connection")
        print("  test-notification - Send test notification to your phone")
        print("  test-search WORD - Test search for specific word (e.g. lego)")
        print("  add-search WORD  - Add a search word")
        print("  list-searches    - List all current search words")
        print("  check-once       - Run a single auction check")
        print("  start-web        - Start the web interface")
        print("  start-monitor    - Start continuous monitoring")
        print()
        print("Examples:")
        print("  python manage.py add-search vintage")
        print("  python manage.py check-once")
        print("  python manage.py start-web")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "test-scraper":
        print("🔍 Testing auction scraper...")
        result = run_command('-c "from src.scraper import SikoScraper; s = SikoScraper(); urls = s.get_auction_urls(); print(f\'Found {len(urls)} auctions\')"')
        print(result.stdout.strip())
        if result.returncode != 0:
            print("❌ Scraper test failed:", result.stderr.strip())
    
    elif command == "test-ha":
        print("🏠 Testing Home Assistant connection...")
        result = run_command('-c "from src.home_assistant import HomeAssistantNotifier; n = HomeAssistantNotifier(); print(\'✅ Connected\' if n.test_connection() else \'❌ Failed\')"')
        print(result.stdout.strip())
        if result.returncode != 0:
            print("❌ HA test failed:", result.stderr.strip())
    
    elif command == "test-notification":
        print("📱 Sending test notification...")
        result = run_command('-c "from src.home_assistant import HomeAssistantNotifier; n = HomeAssistantNotifier(); print(\'✅ Notification sent\' if n.send_test_notification() else \'❌ Failed to send\')"')
        print(result.stdout.strip())
        if result.returncode != 0:
            print("❌ Notification test failed:", result.stderr.strip())
    
    elif command == "test-search":
        if len(sys.argv) < 3:
            print("❌ Please provide a search word: python manage.py test-search WORD")
            sys.exit(1)
        search_word = sys.argv[2]
        print(f"🔍 Testing search for: {search_word}")
        result = run_command(f'test_search.py {search_word}')
        print(result.stdout.strip())
        if result.returncode != 0:
            print("❌ Search test failed:", result.stderr.strip())
    
    elif command == "add-search":
        if len(sys.argv) < 3:
            print("❌ Please provide a search word: python manage.py add-search WORD")
            sys.exit(1)
        search_word = sys.argv[2]
        print(f"➕ Adding search word: {search_word}")
        result = run_command(f'-m src.main --add-search "{search_word}"')
        print(result.stdout.strip())
        if result.returncode != 0:
            print("❌ Failed to add search word:", result.stderr.strip())
    
    elif command == "list-searches":
        print("📝 Current search words:")
        result = run_command('-m src.main --list-searches')
        print(result.stdout.strip())
        if result.returncode != 0:
            print("❌ Failed to list search words:", result.stderr.strip())
    
    elif command == "check-once":
        print("🔍 Running single auction check...")
        result = run_command('-m src.main --once')
        print(result.stdout.strip())
        if result.returncode != 0:
            print("❌ Auction check failed:", result.stderr.strip())
    
    elif command == "start-web":
        print("🌐 Starting web interface at http://localhost:5000")
        print("Press Ctrl+C to stop")
        result = run_command('-m src.web_app')
        print(result.stdout.strip())
        if result.returncode != 0:
            print("❌ Web interface failed:", result.stderr.strip())
    
    elif command == "start-monitor":
        print("⏰ Starting continuous monitoring...")
        print("Press Ctrl+C to stop")
        result = run_command('-m src.main')
        print(result.stdout.strip())
        if result.returncode != 0:
            print("❌ Monitoring failed:", result.stderr.strip())
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python manage.py' to see available commands")
        sys.exit(1)

if __name__ == "__main__":
    main()