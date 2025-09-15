# Home Assistant Dashboard Setup for Siko Auction Monitor

To make notifications open in the Home Assistant companion app and show your auctions page, you need to configure a Home Assistant dashboard called `siko-akutioner`.

## Method 1: Using Home Assistant UI (Recommended)

1. **Open Home Assistant** in your browser: `http://homeassistant.local:8123`

2. **Go to Settings → Dashboards**

3. **Add New Dashboard**
   - Click the "+" button
   - Name: `Siko Auction Monitor`
   - URL: `siko-akutioner` (important: this must match the notification URL)
   - Icon: `mdi:gavel`
   - Click "Create"

4. **Edit the Dashboard**
   - Click on your new dashboard
   - Click the pencil icon (Edit Dashboard)
   - Click "Add Card"

5. **Add an iFrame Card**
   - Search for "Webpage" or "iFrame" 
   - URL: `http://homeassistant.local:5000/auctions`
   - Title: `Current Auctions`
   - Aspect Ratio: Leave default or set to `100%`
   - Click "Save"

6. **Add Quick Links Card (Optional)**
   - Add another card: "Markdown"
   - Content:
     ```markdown
     ## Quick Links
     📋 [View All Auctions](http://homeassistant.local:5000/auctions)
     🏠 [Dashboard](http://homeassistant.local:5000/)
     ⚙️ [Configuration](http://homeassistant.local:5000/config)
     📊 [Logs](http://homeassistant.local:5000/logs)
     ```
   - Title: `Siko Auction Monitor`
   - Click "Save"

7. **Save Dashboard**
   - Click "Done" to save your dashboard

## Method 2: YAML Configuration (Advanced)

If you prefer YAML configuration:

1. **Copy the YAML configuration** from `home-assistant-dashboard-config.yaml` in this repository

2. **Add to Home Assistant**:
   - Go to **Settings → Dashboards**
   - Click **"Create Dashboard"**
   - Choose **"Start with empty dashboard"**
   - Set URL to: `siko-akutioner`
   - Enable **"Show in sidebar"**
   - Save and then switch to **"Raw configuration editor"**
   - Paste the YAML content

## Method 3: File-based Configuration

1. **SSH into your Home Assistant** or use the File Editor add-on

2. **Create the dashboard file**:
   ```bash
   # Create/edit the dashboard configuration
   nano /config/ui-lovelace-siko-akutioner.yaml
   ```

3. **Add the YAML content** from the provided configuration file

4. **Update configuration.yaml**:
   ```yaml
   lovelace:
     mode: storage
     dashboards:
       siko-akutioner:
         mode: yaml
         title: Siko Auction Monitor
         icon: mdi:gavel
         show_in_sidebar: true
         filename: ui-lovelace-siko-akutioner.yaml
   ```

5. **Restart Home Assistant**

## Testing the Setup

1. **Send a test notification** using your web interface:
   - Go to `http://homeassistant.local:5000`
   - Click "Test Home Assistant" button

2. **Tap the notification** on your mobile device
   - Should open Home Assistant companion app
   - Should navigate to your `siko-akutioner` dashboard
   - Should show the auctions page in an iframe

3. **Verify the URL**:
   - The dashboard should be accessible at: `homeassistant://navigate/siko-akutioner/0`
   - Or via web: `http://homeassistant.local:8123/siko-akutioner/0`

## Troubleshooting

**Dashboard not appearing:**
- Check that the URL is exactly `siko-akutioner` 
- Ensure "Show in sidebar" is enabled

**iFrame not loading:**
- Try opening `http://homeassistant.local:5000/auctions` directly in your browser first
- Check Home Assistant logs for any iframe security issues
- You may need to add iframe permissions to your web app

**Notification not opening dashboard:**
- Verify the notification URL in logs: should be `homeassistant://navigate/siko-akutioner/0`
- Test the URL manually by typing it in your phone's browser (should open HA app)

## What Users Will Experience

When you tap a notification:
1. 📱 **Home Assistant companion app opens**
2. 🎯 **Navigates to siko-akutioner dashboard**  
3. 📋 **Shows auctions page embedded in the dashboard**
4. 🔗 **Can tap any auction to view on Siko website**
5. 🏠 **Stays within Home Assistant app environment**

This provides the best of both worlds: stays in the companion app while showing your detailed auctions page!