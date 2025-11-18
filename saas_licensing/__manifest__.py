# -*- coding: utf-8 -*-
{
    'name': 'SaaS Licensing & Billing',
    'version': '18.0.2.0.0',
    'category': 'Services/SaaS',
    'summary': 'License tracking and billing based on users and companies',
    'description': """
        SaaS Licensing & Billing
        ========================

        Advanced licensing and billing for SaaS instances:

        * **License Tracking:** Monitor user and company counts per instance
        * **Automatic Billing:** Generate invoices based on actual usage
        * **Usage Tiers:** Configure pricing tiers based on user/company count
        * **Overage Charges:** Automatic billing for usage beyond plan limits
        * **Reports:** Detailed usage and billing reports

        This module extends saas_management with licensing capabilities.
    """,
    'author': 'AutomateAI',
    'website': 'https://automateai.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale_management',
        'account',
        'saas_management',
        'subscription_package',
    ],
    'data': [
        # Security
        'security/saas_licensing_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/saas_license_data.xml',

        # Views
        'views/saas_license_views.xml',
        'views/saas_instance_views.xml',
        'views/subscription_package_views.xml',
        'views/saas_config_views.xml',
        'views/saas_licensing_menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
