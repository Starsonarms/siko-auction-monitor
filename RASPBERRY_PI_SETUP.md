# Raspberry Pi Setup Guide

## System Requirements

### System Libraries (Required)

These must be installed via `apt` before installing Python packages:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and development tools
sudo apt install python3 python3-pip python3-venv git -y

# Install Pillow dependencies (for image processing)
sudo apt install libopenjp2-7 libjpeg-dev zlib1g-dev libtiff5-dev -y
```

### Python Dependencies

After system libraries are installed:

```bash
cd ~/siko-auction-monitor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Why System Libraries?

- `libopenjp2-7` - JPEG 2000 image support for Pillow
- `libjpeg-dev` - JPEG image support
- `zlib1g-dev` - PNG compression support
- `libtiff5-dev` - TIFF image support

These are C libraries that Pillow links against. They can't be installed via pip.

## Quick Install Script

```bash
# One-command setup
sudo apt update && \
sudo apt install -y python3 python3-pip python3-venv git libopenjp2-7 libjpeg-dev zlib1g-dev libtiff5-dev && \
cd ~/siko-auction-monitor && \
python3 -m venv venv && \
source venv/bin/activate && \
pip install -r requirements.txt
```
