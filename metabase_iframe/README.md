# Metabase Dashboard Iframe

Simple module to embed Metabase dashboards in Odoo 18 using iframes.

## Features

- ✅ Simple and lightweight
- ✅ Embed multiple Metabase dashboards
- ✅ Auto-generate menu items for each dashboard
- ✅ Configurable iframe height
- ✅ Easy to use interface

## Installation

1. Copy this module to your Odoo addons directory
2. Update the app list in Odoo
3. Install "Metabase Dashboard Iframe"

## Usage

### Step 1: Get Metabase Dashboard URL

From your Metabase instance:
1. Open the dashboard you want to embed
2. Click the "Share" button
3. Enable "Public link"
4. Copy the public URL (it will look like: `https://metabase.example.com/public/dashboard/xxxxx`)

### Step 2: Create Dashboard in Odoo

1. Go to **Metabase → Configuration → Dashboards**
2. Click **Create**
3. Fill in:
   - **Dashboard Name**: Give it a name (e.g., "Sales Dashboard")
   - **Dashboard URL**: Paste the Metabase public URL
   - **Sequence**: Order in which it appears in menu (lower = first)
   - **Height**: Height of the iframe in pixels (default: 800)
   - **Description**: Optional description
4. Click **Save**

### Step 3: View Dashboard

A new menu item will be created automatically under **Metabase** with the name you specified.

Click on it to view your dashboard!

## Configuration

### Adjust Dashboard Height

Different dashboards may need different heights. You can adjust this in the dashboard configuration:

- Small dashboards: 600px
- Medium dashboards: 800px (default)
- Large dashboards: 1200px or more

### Reorder Dashboards

Use the **Sequence** field to control the order of dashboard menu items. Lower numbers appear first.

### Disable Dashboard

Uncheck the **Active** field to hide a dashboard without deleting it.

## Security

- Only **Settings / Administration / Access Rights** users can create/edit dashboards
- All internal users can view dashboards

## Troubleshooting

### Dashboard doesn't load

1. Check if the URL is a **public** Metabase dashboard URL
2. Make sure your Metabase server allows iframe embedding
3. Check browser console for CSP (Content Security Policy) errors

### Menu item not appearing

1. Refresh the page (Ctrl + F5)
2. Check if the dashboard is **Active**
3. Verify you have permission to view the dashboard

## Technical Details

- **Model**: `metabase.dashboard`
- **Action**: `ir.actions.client` with tag `metabase_dashboard_viewer`
- **Frontend**: OWL Component

## Support

For issues or questions, contact AutomateAI support.
