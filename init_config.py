#!/usr/bin/env python3
"""
Initialize configuration for Siko Auction Monitor
Run this after pulling changes to ensure your settings are preserved
"""

import os
import shutil
from pathlib import Path

def init_environment():
    """Initialize the .env file from the example if it doesn't exist"""
    env_path = Path('.env')
    env_example_path = Path('.env.example')
    
    if not env_path.exists() and env_example_path.exists():
        print("🔧 Creating .env file from example...")
        shutil.copy(env_example_path, env_path)
        print("✅ Created .env file")
        print()
        print("📝 NEXT STEPS:")
        print("   1. Edit .env file with your Home Assistant settings:")
        print("      - HA_URL=http://your-homeassistant-ip:8123")
        print("      - HA_TOKEN=your_long_lived_access_token")
        print("      - HA_SERVICE=notify.mobile_app_your_phone")
        print()
        print("   2. Test your configuration:")
        print("      python manage.py test-ha")
        print()
        return True
    elif env_path.exists():
        print("✅ .env file exists - your settings are preserved")
        return False
    else:
        print("❌ Warning: .env.example file not found!")
        return False

def init_config_directory():
    """Initialize config directory and files"""
    config_dir = Path('config')
    config_dir.mkdir(exist_ok=True)
    
    # Create empty configuration files if they don't exist
    files_created = []
    
    search_words_file = config_dir / 'search_words.json'
    if not search_words_file.exists():
        search_words_file.write_text('[]')
        files_created.append('search_words.json')
    
    blacklisted_file = config_dir / 'blacklisted_auctions.json'
    if not blacklisted_file.exists():
        blacklisted_file.write_text('[]')
        files_created.append('blacklisted_auctions.json')
    
    if files_created:
        print(f"✅ Created config files: {', '.join(files_created)}")
    else:
        print("✅ Config files exist - your data is preserved")

def main():
    """Main initialization function"""
    print("🚀 Initializing Siko Auction Monitor configuration...")
    print()
    
    # Initialize environment file
    env_created = init_environment()
    
    # Initialize config directory
    init_config_directory()
    
    print()
    if env_created:
        print("⚠️  Don't forget to configure your .env file!")
    else:
        print("🎉 Configuration preserved! Ready to run.")
        print("   python manage.py start-web")

if __name__ == "__main__":
    main()