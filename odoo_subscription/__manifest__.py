# -*- coding: utf-8 -*-
{
    'name': 'Odoo Subscription Management',
    'version': '18.0.1.0.0',
    'category': 'Sales/Subscriptions',
    'summary': 'Advanced Subscription Management with SaaS Integration',
    'description': """
        Enhanced Subscription Management for Odoo 18
        =============================================

        Based on subscription_package with major enhancements:

        * Full integration with SaaS Core module
        * Usage-based billing (metering)
        * Automatic plan upgrade/downgrade
        * Prorating on plan changes
        * Renewal management with email alerts
        * Automated invoice generation
        * Subscription lifecycle management
        * Financial reporting and analytics
        * Resource usage tracking
        * Multi-currency support

        Perfect for SaaS businesses offering subscription-based services.
    """,
    'author': 'AutomateAI',
    'website': 'https://automateai.com.mx',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'sale_management',
        'account',
        'odoo_saas_core',
    ],
    'data': [
        # Security
        'security/subscription_security.xml',
        'security/ir.model.access.csv',

        # Data
        # Note: Stage and Stop Reason data comes from subscription_package module
        'data/sequences.xml',
        'data/mail_templates.xml',
        'data/cron_jobs.xml',

        # Views (SaaS Extensions)
        'views/subscription_package_views.xml',  # Inherit to add SaaS features
        'views/subscription_metering_views.xml',  # New: Usage-based billing
        'views/sale_order_views.xml',  # Inherit to add subscription link
        'views/product_template_views.xml',  # Inherit to add SaaS product fields

        # Reports (before menus, as menus reference report actions)
        'report/subscription_report_views.xml',

        # Menus (must be loaded after actions)
        'views/subscription_menus.xml',

        # Wizards: Using base module wizards (subscription_package)
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
