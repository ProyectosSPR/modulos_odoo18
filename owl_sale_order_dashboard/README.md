Sales Dashboard Module(Odoo Version 18)
===========================

A comprehensive sales dashboard for Odoo that provides visual analytics and key performance indicators for your sales team.

Features
--------

- **Date Range Filtering:** Filter data by custom date ranges with a user-friendly interface.
- **Key Performance Indicators (KPIs):**
  - Total Orders
  - Total Revenue
  - Best Selling Product
  - Top Performing Salesperson
  - Total Canceled Orders
  - Total Not Invoiced Orders
- **Interactive Charts:**
  - Best Selling Products (Bar Chart)
  - Top Salespersons (Horizontal Bar Chart)
  - Order Status Overview (Pie Chart)
  - Payment Summary (Doughnut Chart)
- **Responsive Design:** Works on desktop, tablet, and mobile devices.
- **Real-time Data:** All data updates automatically when filters change.

Installation
------------

1. clone this repo into your custom_modules folder
2. Install the module through the Odoo Apps menu.
3. Grant appropriate access rights to users who need to view the dashboard.

Usage
-----

1. Navigate to the **Sales Dashboard** from the main menu.
2. Use the date pickers to select a start and end date for your analysis.
3. Click **Apply** to update the dashboard with the selected date range.
4. View the various charts and metrics to analyze your sales performance.

Technical Details
-----------------

**Backend (Python)**

The module extends the `sale.order` model with a `get_dashboard_data` method that:

- Accepts `start_date` and `end_date` parameters.
- Calculates all KPI metrics with date filtering.
- Executes optimized SQL queries for best performance.
- Returns structured data for frontend visualization.

**Frontend (JavaScript/OWL)**

The dashboard is built using Odoo's OWL framework with:

- Reactive state management.
- Chart.js integration for data visualization.
- Responsive design with Bootstrap classes.
- Real-time data updates.

Data Sources
------------

- Sales Orders
- Account Moves (Invoices)
- Product Catalog
- Sales Team Members

Customization
-------------

You can extend this dashboard by:

- Adding new KPI cards by modifying the Python method and frontend components.
- Changing chart types or colors in the JavaScript code.
- Adding additional filters (e.g., by sales team, product category).
- Integrating with other Odoo modules for expanded analytics.
