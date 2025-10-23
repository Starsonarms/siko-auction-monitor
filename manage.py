#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Siko Auction Monitor - Management Script
Easy commands to manage your auction monitoring
"""

import os
import sys
import subprocess

# Configure UTF-8 output for Windows
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

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
        print("🔨 Siko Auction Monitor - Management Script (Web App Only)")
        print()
        print("Available commands:")
        print("  test-scraper     - Test if the auction scraper is working")
        print("  test-ha          - Test Home Assistant connection")
        print("  test-notification - Send test notification to your phone")
        print("  test-search WORD - Test search for specific word (e.g. lego)")
        print("  add-search WORD  - Add a search word")
        print("  list-searches    - List all current search words")
        print("  hide-auction ID  - Hide/blacklist an auction by ID")
        print("  unhide-auction ID - Unhide/unblacklist an auction by ID")
        print("  list-hidden      - List all hidden/blacklisted auctions")
        print("  start-web        - Start the web interface")
        print()
        print("Examples:")
        print("  python manage.py add-search vintage")
        print("  python manage.py start-web")
        print()
        print("⚠️  Note: Standalone monitoring (start-monitor, check-once) is not available")
        print("    in this branch. Use the web interface instead.")
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
        
        # Create a simple script
        script_content = f'''from src.search_manager import SearchManager
sm = SearchManager()
result = sm.add_search_word("{search_word}")
if result:
    print("Search word added successfully")
else:
    print("Failed to add search word")
'''
        with open('temp_add_search_script.py', 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        result = run_command('temp_add_search_script.py')
        print(result.stdout.strip())
        if result.returncode != 0:
            print("❌ Failed to add search word:", result.stderr.strip())
        
        # Clean up temp file
        try:
            os.remove('temp_add_search_script.py')
        except:
            pass
    
    elif command == "list-searches":
        print("📝 Current search words:")
        
        # Create a simple script
        script_content = '''from src.search_manager import SearchManager
sm = SearchManager()
words = sm.get_search_words()
if words:
    print("Current search words:")
    for word in words:
        print(f"  - {word}")
else:
    print("No search words configured")
'''
        with open('temp_list_search_script.py', 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        result = run_command('temp_list_search_script.py')
        print(result.stdout.strip())
        if result.returncode != 0:
            print("❌ Failed to list search words:", result.stderr.strip())
        
        # Clean up temp file
        try:
            os.remove('temp_list_search_script.py')
        except:
            pass
    
    elif command == "hide-auction":
        if len(sys.argv) < 3:
            print("❌ Please provide an auction ID: python manage.py hide-auction AUCTION_ID")
            print("   Example: python manage.py hide-auction 834502")
            sys.exit(1)
        auction_id = sys.argv[2]
        print(f"Hiding auction: {auction_id}")
        
        # Create a simple script to avoid shell escaping issues
        script_content = f'''from src.blacklist_manager import BlacklistManager
bm = BlacklistManager()
result = bm.add_auction("{auction_id}")
if result:
    print("Auction hidden successfully")
else:
    print("Auction was already hidden")
'''
        with open('temp_hide_script.py', 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        result = run_command('temp_hide_script.py')
        print(result.stdout.strip())
        if result.returncode != 0:
            print("❌ Failed to hide auction:", result.stderr.strip())
        
        # Clean up temp file
        try:
            os.remove('temp_hide_script.py')
        except:
            pass
    
    elif command == "unhide-auction":
        if len(sys.argv) < 3:
            print("❌ Please provide an auction ID: python manage.py unhide-auction AUCTION_ID")
            print("   Example: python manage.py unhide-auction 834502")
            sys.exit(1)
        auction_id = sys.argv[2]
        print(f"Unhiding auction: {auction_id}")
        
        # Create a simple script to avoid shell escaping issues
        script_content = f'''from src.blacklist_manager import BlacklistManager
bm = BlacklistManager()
result = bm.remove_auction("{auction_id}")
if result:
    print("Auction unhidden successfully")
else:
    print("Auction was not in blacklist")
'''
        with open('temp_unhide_script.py', 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        result = run_command('temp_unhide_script.py')
        print(result.stdout.strip())
        if result.returncode != 0:
            print("❌ Failed to unhide auction:", result.stderr.strip())
        
        # Clean up temp file
        try:
            os.remove('temp_unhide_script.py')
        except:
            pass
    
    elif command == "list-hidden":
        print("Hidden auctions:")
        # Create a simple script to avoid shell escaping issues
        script_content = '''from src.blacklist_manager import BlacklistManager
bm = BlacklistManager()
ids = bm.get_blacklisted_ids()
if ids:
    print(f"Total hidden: {len(ids)}")
    for id in ids[:10]:
        print(f"  - {id}")
    if len(ids) > 10:
        print("  ... and more")
else:
    print("No hidden auctions")
'''
        with open('temp_list_script.py', 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        result = run_command('temp_list_script.py')
        print(result.stdout.strip())
        if result.returncode != 0:
            print("❌ Failed to list hidden auctions:", result.stderr.strip())
        
        # Clean up temp file
        try:
            os.remove('temp_list_script.py')
        except:
            pass
    
    elif command == "check-once":
        print("❌ Command 'check-once' is not available in this branch (mongodb-integration).")
        print("   This branch only supports the web interface.")
        print("   Switch to the main branch for standalone monitoring.")
        sys.exit(1)
    
    elif command == "start-web":
        print("Starting web interface at http://localhost:5000")
        print("Press Ctrl+C to stop")
        result = run_command('-m src.web_app')
        print(result.stdout.strip())
        if result.returncode != 0:
            print("❌ Web interface failed:", result.stderr.strip())
    
    elif command == "start-monitor":
        print("❌ Command 'start-monitor' is not available in this branch (mongodb-integration).")
        print("   This branch only supports the web interface.")
        print("   Switch to the main branch for standalone monitoring.")
        sys.exit(1)
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python manage.py' to see available commands")
        sys.exit(1)

if __name__ == "__main__":
    main()