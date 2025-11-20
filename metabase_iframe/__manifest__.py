# -*- coding: utf-8 -*-
{
    'name': 'Metabase Dashboard Iframe',
    'version': '18.0.1.0.0',
    'category': 'Reporting',
    'summary': 'Embed Metabase dashboards in Odoo using iframes',
    'description': """
        Metabase Dashboard Integration
        ===============================

        Simple module to embed Metabase dashboards in Odoo using iframes.

        Features:
        - Create multiple dashboard configurations
        - Embed Metabase dashboards via iframe
        - Menu items for easy access
        - Secure iframe implementation
    """,
    'author': 'AutomateAI',
    'website': 'https://automateai.com.mx',
    'license': 'LGPL-3',
    'depends': ['web'],
    'data': [
        'security/ir.model.access.csv',
        'views/metabase_dashboard_views.xml',
        'views/metabase_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'metabase_iframe/static/src/js/metabase_dashboard.js',
            'metabase_iframe/static/src/xml/metabase_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
