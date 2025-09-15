# Siko Auction Monitor

Monitor [sikoauktioner.se](https://sikoauktioner.se) for auctions matching your search words and get notifications via Home Assistant on your iPhone.

Perfect for running on a Raspberry Pi as a continuous monitoring service.

## Features

- 🔍 **Smart Search**: Monitor auctions with customizable search words
- 📱 **iPhone Notifications**: Get instant alerts via Home Assistant
- 🌐 **Web Interface**: Manage search words remotely through a clean web UI
- 🤖 **Automated**: Runs continuously as a background service
- 🍓 **Raspberry Pi Ready**: Optimized for deployment on Raspberry Pi

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd siko-auction-monitor
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure

Copy the example configuration:
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```bash
nano .env
```

Required settings:
- `HA_URL`: Your Home Assistant URL (e.g., `http://192.168.1.100:8123`)
- `HA_TOKEN`: Long-lived access token from Home Assistant
- `HA_SERVICE`: Notification service (e.g., `notify.mobile_app_your_iphone`)

### 4. Add Search Words

Add your first search words:
```bash
python -m src.main --add-search "antique"
python -m src.main --add-search "vintage tools"
python -m src.main --list-searches
```

### 5. Test the Setup

Test scraper:
```bash
python -m src.main --once
```

Or use the web interface:
```bash
python -m src.web_app
```

Visit `http://your-pi-ip:5000` to access the web interface.

## Raspberry Pi Deployment

### 1. Install on Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv git -y

# Clone repository to your home directory
# Note: ~ always points to your home directory regardless of username
cd ~
git clone <your-repo-url>
cd siko-auction-monitor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy configuration
cp .env.example .env
nano .env

# Create directories
mkdir -p logs config
```

### 3. Set up as System Service

```bash
# Copy and set up the startup script
cp scripts/start-service.sh .
chmod +x start-service.sh

# Edit the script to use your username (replace "pi" with your actual username)
nano start-service.sh
# Change: cd /home/pi/siko-auction-monitor
# To: cd /home/your_username/siko-auction-monitor

# Copy service file
sudo cp scripts/siko-auction-monitor.service /etc/systemd/system/

# Edit service file with correct paths and username
sudo nano /etc/systemd/system/siko-auction-monitor.service

# You need to replace all instances of "pi" with your actual username:
# - User=pi → User=your_username
# - Group=pi → Group=your_username  
# - /home/pi/ → /home/your_username/
# (Find your username with: whoami)

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable siko-auction-monitor.service
sudo systemctl start siko-auction-monitor.service

# Check status
sudo systemctl status siko-auction-monitor.service
```

### 4. Access Web Interface

The web interface will be available at:
- `http://your-pi-ip:5000`

## Home Assistant Setup

### 1. Create Long-Lived Access Token

1. Go to Home Assistant → Profile → Security
2. Create a Long-Lived Access Token
3. Copy the token to your `.env` file

### 2. Find Your Notification Service

Common notification services:
- `notify.mobile_app_your_iphone` (iPhone app)
- `notify.mobile_app_your_android` (Android app) 
- `notify.persistent_notification` (HA dashboard)

You can find available services in Home Assistant:
- Developer Tools → Services → Filter by "notify"

### 3. Test Notification

```bash
# Test from command line
python -c "from src.home_assistant import HomeAssistantNotifier; HomeAssistantNotifier().send_test_notification()"
```

Or use the web interface test button.

## Usage

### Command Line

```bash
# Run once
python -m src.main --once

# Run continuously (scheduled)
python -m src.main

# Manage search words
python -m src.main --add-search "keyword"
python -m src.main --remove-search "keyword"
python -m src.main --list-searches
```

### Web Interface

Access at `http://your-pi-ip:5000`:

- 📊 **Dashboard**: View status and manage search words
- 🔧 **Tests**: Test scraper and Home Assistant connection
- 📝 **Logs**: View application logs
- ⚙️ **Config**: View configuration

### Search Words

Search words are matched against:
- Auction titles
- Auction descriptions
- Auction locations
- Individual item titles and descriptions

Examples:
- `"antique"` - matches any auction containing "antique"
- `"vintage tools"` - matches auctions with both "vintage" and "tools"
- `"möbler"` - matches Swedish furniture auctions

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HA_URL` | `http://homeassistant.local:8123` | Home Assistant URL |
| `HA_TOKEN` | - | Home Assistant access token |
| `HA_SERVICE` | `notify.mobile_app_your_iphone` | Notification service |
| `CHECK_INTERVAL` | `15` | Minutes between checks |
| `WEB_PORT` | `5000` | Web interface port |
| `LOG_LEVEL` | `INFO` | Logging level |

### Files

- `.env` - Environment configuration
- `config/search_words.json` - Search words storage
- `logs/auction_monitor.log` - Application logs

## Troubleshooting

### Common Issues

**Can't connect to Home Assistant:**
- Check HA_URL is correct and accessible from Pi
- Verify HA_TOKEN is valid
- Ensure Home Assistant is running

**No auctions found:**
- Check if sikoauktioner.se is accessible
- Verify scraper selectors (website may have changed)
- Check logs for errors

**Service won't start:**
- Check service file paths are correct
- Verify virtual environment path
- Check file permissions

**Wrong directory paths:**
- Use `cd ~` instead of `cd /home/pi` (works with any username)
- Find your home directory with `echo $HOME` if unsure

**Service file errors:**
- Update all "pi" references in the service file to your actual username
- Check User=, Group=, WorkingDirectory=, ExecStart=, EnvironmentFile=, and ReadWritePaths=
- Find your username with `whoami`
- If you get "CHDIR" errors, the issue is likely `ProtectHome=true` - change it to `ProtectHome=false`

**Service won't start (203/EXEC errors):**
- Make sure the startup script exists and is executable: `chmod +x start-service.sh`
- Check that the script uses the correct username in the path
- Verify the script works manually: `./start-service.sh`

### Logs

```bash
# View live logs
tail -f logs/auction_monitor.log

# View service logs
sudo journalctl -u siko-auction-monitor.service -f
```

### Debug Mode

Enable debug logging:
```bash
echo "LOG_LEVEL=DEBUG" >> .env
```

## Development

### Project Structure

```
siko-auction-monitor/
├── src/
│   ├── main.py              # Main application
│   ├── scraper.py           # Web scraper
│   ├── search_manager.py    # Search word management
│   ├── home_assistant.py    # HA integration
│   ├── config.py           # Configuration
│   └── web_app.py          # Web interface
├── templates/              # HTML templates
├── config/                 # Runtime configuration
├── logs/                   # Log files
├── scripts/               # Deployment scripts
└── requirements.txt       # Python dependencies
```

### Adding Features

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - feel free to modify and use for your own needs.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs for error messages  
3. Test individual components (scraper, Home Assistant)
4. Create an issue with logs and configuration (remove sensitive data)

---

**Happy auction hunting! 🔨**