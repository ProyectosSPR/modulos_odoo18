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
        'data/subscription_stage_data.xml',
        'data/subscription_stop_data.xml',
        'data/sequences.xml',
        'data/mail_templates.xml',
        'data/cron_jobs.xml',

        # Views
        'views/subscription_package_views.xml',
        'views/subscription_plan_views.xml',
        'views/subscription_product_line_views.xml',
        'views/subscription_stage_views.xml',
        'views/subscription_metering_views.xml',
        'views/sale_order_views.xml',
        'views/product_template_views.xml',
        'views/subscription_menus.xml',

        # Wizards
        'wizards/subscription_close_wizard_views.xml',
        'wizards/subscription_upgrade_wizard_views.xml',

        # Reports
        'report/subscription_report_views.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
