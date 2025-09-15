#!/bin/bash
# Startup script for Siko Auction Monitor service
# This script activates the virtual environment and starts the web application

cd /home/pi/siko-auction-monitor
source ./venv/bin/activate
exec python manage.py start-web