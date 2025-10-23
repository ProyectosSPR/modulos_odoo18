{
    'name': "O'Dashboard",
    'version': '18.0.0.1.0',
    'category': 'Dashboard',
    'summary': 'Advanced business intelligence dashboards with drag-and-drop interface, real-time analytics, and role-based access control for Odoo data visualization and reporting.',
    'description': """
       Advanced Dashboard Solution for Odoo

Create powerful, interactive dashboards with a simple drag and drop system.

Key Features:
- Drag & Drop Dashboard Builder
- Real-time Data Visualization  
- Multiple Chart Types (bar, line, pie, gauge)
- Dynamic Filters and Live Data
- Multi-user Support and Sharing
- Custom Themes and Branding
- PDF Export Capabilities
- Security Groups Integration

Perfect for business intelligence, KPIs monitoring, and data analysis.
No coding required - just install and start building!

    """,
    'author': "O'Solutions Company",
    'website': 'https://odashboard.app',
    'depends': [
        'base',
        'web',
        'mail',
    ],
    'data': [
        # Security
        'security/odash_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/ir_config_parameter.xml',
        'data/ir_cron.xml',
        'data/ir_cron_pdf_reports.xml',
        'data/mail_template_pdf_report.xml',

        # Views
        'views/res_config_settings_views.xml',
        'views/dashboard_views.xml',
        'views/odash_security_group_views.xml',
        'views/odash_config_views.xml',
        'views/odash_category_views.xml',
        'views/dashboard_public_views.xml',
        'views/odash_dashboard_views.xml',
        'views/odash_pdf_report_views.xml',
        # Wizards
        'wizards/odash_config_import_wizard_views.xml',
        'wizards/odash_config_export_wizard_views.xml',
        # Menu
        'views/menu_items.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odashboard/static/src/css/odash_iframe_widget.css',
            'odashboard/static/src/js/odash_iframe_widget.js',
            'odashboard/static/src/xml/odash_iframe_widget.xml'
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
        'static/description/youtube-link.png',
    ],
    'license': 'OPL-1',
    'application': True,
    'installable': True,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
