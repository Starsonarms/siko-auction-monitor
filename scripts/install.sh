#!/bin/bash
set -e

# Siko Auction Monitor - Raspberry Pi Installation Script
echo "🔨 Installing Siko Auction Monitor on Raspberry Pi"
echo "================================================"

# Configuration
PROJECT_DIR="/home/pi/siko-auction-monitor"
USER="pi"
PYTHON_CMD="python3"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_error "Please do not run this script as root. Run as the pi user."
    exit 1
fi

# Check if we're on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    log_warn "This doesn't appear to be a Raspberry Pi, but continuing anyway..."
fi

log_info "Step 1: Updating system packages..."
sudo apt update
sudo apt upgrade -y

log_info "Step 2: Installing required system packages..."
sudo apt install -y python3 python3-pip python3-venv git curl

log_info "Step 3: Creating project directory..."
if [ ! -d "$PROJECT_DIR" ]; then
    log_error "Project directory $PROJECT_DIR not found. Please clone the repository first:"
    log_error "git clone <repository-url> $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

log_info "Step 4: Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
else
    log_info "Virtual environment already exists"
fi

log_info "Step 5: Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

log_info "Step 6: Creating configuration from template..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    log_warn "Configuration file created at .env - PLEASE EDIT IT BEFORE STARTING!"
    log_warn "You need to set your Home Assistant URL, token, and notification service."
else
    log_info "Configuration file already exists"
fi

log_info "Step 7: Creating directories..."
mkdir -p logs config

log_info "Step 8: Setting up systemd services..."
sudo cp scripts/siko-auction-monitor.service /etc/systemd/system/
sudo cp scripts/siko-web.service /etc/systemd/system/

# Update service files with correct paths if different from default
if [ "$PROJECT_DIR" != "/home/pi/siko-auction-monitor" ] || [ "$USER" != "pi" ]; then
    log_info "Updating service files for custom paths..."
    sudo sed -i "s|/home/pi/siko-auction-monitor|$PROJECT_DIR|g" /etc/systemd/system/siko-auction-monitor.service
    sudo sed -i "s|/home/pi/siko-auction-monitor|$PROJECT_DIR|g" /etc/systemd/system/siko-web.service
    sudo sed -i "s|User=pi|User=$USER|g" /etc/systemd/system/siko-auction-monitor.service
    sudo sed -i "s|User=pi|User=$USER|g" /etc/systemd/system/siko-web.service
    sudo sed -i "s|Group=pi|Group=$USER|g" /etc/systemd/system/siko-auction-monitor.service
    sudo sed -i "s|Group=pi|Group=$USER|g" /etc/systemd/system/siko-web.service
fi

log_info "Step 9: Reloading systemd and enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable siko-auction-monitor.service
sudo systemctl enable siko-web.service

log_info "Step 10: Setting file permissions..."
chown -R $USER:$USER "$PROJECT_DIR"
chmod +x scripts/*.sh

echo
echo "✅ Installation completed successfully!"
echo
echo "🔧 Next steps:"
echo "1. Edit your configuration: nano $PROJECT_DIR/.env"
echo "2. Add your Home Assistant URL, token, and notification service"
echo "3. Test the setup: cd $PROJECT_DIR && source venv/bin/activate && python -m src.main --once"
echo "4. Start services:"
echo "   sudo systemctl start siko-auction-monitor.service"
echo "   sudo systemctl start siko-web.service"
echo "5. Check status:"
echo "   sudo systemctl status siko-auction-monitor.service"
echo "   sudo systemctl status siko-web.service"
echo "6. Access web interface at: http://$(hostname -I | cut -d' ' -f1):5000"
echo
echo "📝 View logs:"
echo "   sudo journalctl -u siko-auction-monitor.service -f"
echo "   sudo journalctl -u siko-web.service -f"
echo
echo "🔨 Happy auction hunting!"