# -*- coding: utf-8 -*-
{
    'name': 'Subscription Auto-Start on Payment',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Automatically start subscriptions when payment is processed',
    'description': """
        Subscription Auto-Start on Payment
        ===================================

        Automatically starts subscription packages when their associated
        payment transaction is confirmed/done.

        When a sale order with subscription products is paid:
        1. Finds the associated subscription.package in draft state
        2. Automatically calls button_start_date() to activate it
        3. Triggers Stripe subscription creation if sync is enabled

        This eliminates the manual step of starting subscriptions after payment.
    """,
    'author': 'AutomateAI',
    'website': 'https://automateai.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'payment',
        'sale',
        'subscription_package',
    ],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
