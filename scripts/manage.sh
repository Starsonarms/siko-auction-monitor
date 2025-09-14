#!/bin/bash

# Siko Auction Monitor - Management Script
# Usage: ./manage.sh [start|stop|restart|status|logs|update]

SERVICE_MONITOR="siko-auction-monitor.service"
SERVICE_WEB="siko-web.service"
PROJECT_DIR="/home/pi/siko-auction-monitor"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${BLUE}$1${NC}"
}

show_usage() {
    echo "Siko Auction Monitor - Management Script"
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  start     - Start both services"
    echo "  stop      - Stop both services"
    echo "  restart   - Restart both services"
    echo "  status    - Show status of both services"
    echo "  logs      - Show logs (use -f for follow)"
    echo "  update    - Update from git and restart services"
    echo "  test      - Run system tests"
    echo "  backup    - Backup configuration"
    echo
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs -f"
    echo "  $0 status"
}

start_services() {
    log_header "🚀 Starting Siko Auction Monitor services..."
    sudo systemctl start $SERVICE_MONITOR
    sudo systemctl start $SERVICE_WEB
    
    sleep 2
    status_services
}

stop_services() {
    log_header "🛑 Stopping Siko Auction Monitor services..."
    sudo systemctl stop $SERVICE_MONITOR
    sudo systemctl stop $SERVICE_WEB
    
    sleep 1
    log_info "Services stopped"
}

restart_services() {
    log_header "🔄 Restarting Siko Auction Monitor services..."
    stop_services
    start_services
}

status_services() {
    log_header "📊 Service Status:"
    
    echo -n "Monitor Service: "
    if systemctl is-active --quiet $SERVICE_MONITOR; then
        echo -e "${GREEN}RUNNING${NC}"
    else
        echo -e "${RED}STOPPED${NC}"
    fi
    
    echo -n "Web Interface:   "
    if systemctl is-active --quiet $SERVICE_WEB; then
        echo -e "${GREEN}RUNNING${NC}"
        IP=$(hostname -I | cut -d' ' -f1)
        echo -e "                 ${BLUE}http://$IP:5000${NC}"
    else
        echo -e "${RED}STOPPED${NC}"
    fi
    
    echo
    log_info "Detailed status:"
    sudo systemctl status $SERVICE_MONITOR --no-pager -l
    echo
    sudo systemctl status $SERVICE_WEB --no-pager -l
}

show_logs() {
    local follow_flag=""
    if [[ "$2" == "-f" ]]; then
        follow_flag="-f"
        log_header "📝 Following logs (Ctrl+C to exit)..."
    else
        log_header "📝 Recent logs:"
    fi
    
    echo "Monitor logs:"
    sudo journalctl -u $SERVICE_MONITOR $follow_flag --no-pager -n 20
    
    if [[ "$2" != "-f" ]]; then
        echo
        echo "Web interface logs:"
        sudo journalctl -u $SERVICE_WEB $follow_flag --no-pager -n 20
    fi
}

update_system() {
    log_header "🔄 Updating Siko Auction Monitor..."
    
    cd "$PROJECT_DIR" || {
        log_error "Could not change to project directory: $PROJECT_DIR"
        exit 1
    }
    
    # Stop services
    stop_services
    
    # Backup current config
    log_info "Backing up current configuration..."
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
    
    # Update from git
    log_info "Pulling latest changes from git..."
    git pull
    
    # Update dependencies
    log_info "Updating Python dependencies..."
    source venv/bin/activate
    pip install --upgrade -r requirements.txt
    
    # Update systemd services if changed
    log_info "Updating systemd service files..."
    sudo cp scripts/siko-auction-monitor.service /etc/systemd/system/
    sudo cp scripts/siko-web.service /etc/systemd/system/
    sudo systemctl daemon-reload
    
    # Restart services
    start_services
    
    log_info "Update completed!"
}

run_tests() {
    log_header "🧪 Running system tests..."
    
    cd "$PROJECT_DIR" || {
        log_error "Could not change to project directory: $PROJECT_DIR"
        exit 1
    }
    
    source venv/bin/activate
    
    log_info "Testing scraper..."
    python -c "from src.scraper import SikoScraper; s = SikoScraper(); urls = s.get_auction_urls(); print(f'Found {len(urls)} auction URLs')"
    
    log_info "Testing Home Assistant connection..."
    python -c "from src.home_assistant import HomeAssistantNotifier; n = HomeAssistantNotifier(); print('HA connection:', 'OK' if n.test_connection() else 'FAILED')"
    
    log_info "Testing search manager..."
    python -c "from src.search_manager import SearchManager; s = SearchManager(); words = s.get_search_words(); print(f'Search words configured: {len(words)}')"
    
    log_info "Tests completed!"
}

backup_config() {
    log_header "💾 Backing up configuration..."
    
    cd "$PROJECT_DIR" || {
        log_error "Could not change to project directory: $PROJECT_DIR"
        exit 1
    }
    
    backup_dir="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup configuration files
    cp .env "$backup_dir/" 2>/dev/null || log_warn ".env not found"
    cp -r config "$backup_dir/" 2>/dev/null || log_warn "config directory not found"
    cp -r logs "$backup_dir/" 2>/dev/null || log_warn "logs directory not found"
    
    log_info "Backup created in: $PROJECT_DIR/$backup_dir"
}

# Main script logic
case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        status_services
        ;;
    logs)
        show_logs "$@"
        ;;
    update)
        update_system
        ;;
    test)
        run_tests
        ;;
    backup)
        backup_config
        ;;
    "")
        show_usage
        ;;
    *)
        log_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac