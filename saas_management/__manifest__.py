# -*- coding: utf-8 -*-
{
    'name': 'SaaS Management',
    'version': '18.0.1.1.0',
    'category': 'Services/SaaS',
    'summary': 'Manage SaaS clients and Odoo instances with automatic subscription linking',
    'description': """
        SaaS Management - Client and Instance Management
        ==================================================

        Manage your SaaS business with:

        * **SaaS Clients:** Customer management with lifecycle tracking
        * **Odoo Instances:** Dedicated instances with usage monitoring
        * **Metrics:** Track users, storage, and instance status
        * **Integration:** Works with subscription_package and product_permissions

        Perfect for companies offering Odoo as a Service.
    """,
    'author': 'AutomateAI',
    'website': 'https://automateai.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale_management',
        'subscription_package',
        'product_permissions',  # For permission integration
    ],
    'data': [
        # Security
        'security/saas_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/saas_data.xml',

        # Views
        'views/saas_client_views.xml',
        'views/saas_instance_views.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/saas_menus.xml',

        # Wizards
        'views/menu_security_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
