# -*- coding: utf-8 -*-
{
    'name': 'Payment Stripe URL Fix for Kubernetes',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'Fix Stripe return URL in Kubernetes environments',
    'description': """
        Payment Stripe URL Fix
        ======================

        Fixes the issue where Stripe return URLs use internal cluster URLs
        instead of the public domain in Kubernetes environments.

        This module forces the use of web.base.url parameter instead of
        relying on HTTP headers which may point to internal cluster addresses.
    """,
    'author': 'AutomateAI',
    'website': 'https://automateai.com.mx',
    'license': 'LGPL-3',
    'depends': ['payment_stripe'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
