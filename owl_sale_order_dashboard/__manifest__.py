# -*- coding: utf-8 -*-
{
    'name': 'Sale Dashboard',
    'version': '18.0.1.0.0',
    'category': 'sale',
    'summary': 'OWL-based Sales Dashboard',
    'description': 'Interactive sales dashboard with OWL components',
    'author': 'Shahadat Hossain',
    'company': '',
    'maintainer': 'Shahadat Hossain',
    'website': "https://github.com/shahadatcs/modern_sales_dashboard.git",
    'license': 'LGPL-3',
    'images': ['static/description/icon.png'],
    'depends': ['web','sale','sale_management','account'],
    'data': [
        'security/security.xml',
        'views/sale_dashboard_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'owl_sale_order_dashboard/static/src/css/dashboard_views.css',
            'owl_sale_order_dashboard/static/src/js/sale_dashboard.js',
            'owl_sale_order_dashboard/static/src/xml/dashboard.xml',
        ],
    },
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
