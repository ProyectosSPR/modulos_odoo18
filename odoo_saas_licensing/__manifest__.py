# -*- coding: utf-8 -*-
{
    'name': 'SaaS Licensing Management',
    'version': '18.0.1.0.0',
    'category': 'Sales/SaaS',
    'summary': 'Multi-Company Licensing & Usage-Based Billing',
    'description': """
        SaaS Multi-Company Licensing Module
        ====================================

        Perfect for accounting firms and businesses managing multiple companies:

        * License customers by number of companies
        * Automatic company counting and tracking
        * Dynamic subscription updates based on usage
        * Per-company user tracking
        * Automatic billing adjustments
        * License limit enforcement
        * Usage alerts and notifications
        * Multi-tier licensing (per company, per user, per module)
        * Real-time license usage dashboard

        Example Use Case:
        An accounting firm wants to use Odoo to manage 10 different client companies.
        The system tracks how many companies they're managing and bills accordingly.
    """,
    'author': 'AutomateAI',
    'website': 'https://automateai.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale_management',
        'odoo_saas_core',
        'odoo_subscription',
    ],
    'data': [
        # Security
        'security/licensing_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/license_type_data.xml',
        'data/sequences.xml',
        'data/automated_actions.xml',

        # Views
        'views/saas_license_views.xml',
        'views/saas_license_type_views.xml',
        'views/saas_licensed_company_views.xml',
        'views/res_company_views.xml',
        'views/saas_customer_views.xml',
        'views/licensing_menus.xml',

        # Wizards
        'wizards/license_add_company_wizard_views.xml',

        # Reports
        'report/license_usage_report_views.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
