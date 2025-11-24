# -*- coding: utf-8 -*-
{
    'name': 'SaaS Stripe Subscription Integration',
    'version': '18.0.1.0.0',
    'category': 'Services/SaaS',
    'summary': 'Integrate subscription_package with Stripe subscriptions API',
    'description': """
        SaaS Stripe Subscription Integration
        =====================================

        This module integrates the subscription_package module with Stripe's
        subscription API to automatically sync subscriptions between Odoo and Stripe.

        Features:
        * Automatic creation of Stripe customers and subscriptions
        * Sync subscription lifecycle (create, cancel, update)
        * Automatic product and price sync with Stripe
        * Support for test and production environments
        * Integration with existing payment_stripe provider configuration

        When a subscription is created/modified/cancelled in Odoo, the corresponding
        changes are automatically reflected in Stripe.
    """,
    'author': 'AutomateAI',
    'website': 'https://automateai.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'subscription_package',
        'payment_stripe',
        'saas_management',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Views
        'views/subscription_package_views.xml',
        'views/product_template_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
