# -*- coding: utf-8 -*-
{
    'name': 'Product Permissions Management',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Assign custom permissions to users when products are purchased',
    'description': """
        Product Permissions Management
        ================================

        Allows you to configure which security groups should be assigned to users
        when a specific product is purchased.

        Use Cases:
        - Sell CRM module access with specific user permissions
        - Sell Sales module access with manager permissions
        - Create custom permission packages per product

        Key Features:
        - Select security groups directly on products
        - Automatic permission assignment on sale order confirmation
        - Preserves existing user permissions (additive, not destructive)
        - Excludes administrators from automatic permission changes
        - Integration with subscription_package for recurring sales
    """,
    'author': 'AutomateAI',
    'website': 'https://automateai.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale_management',
        'subscription_package',  # Cybrosys subscription module
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
