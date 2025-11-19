# -*- coding: utf-8 -*-
{
    'name': 'SaaS Multi-Company',
    'version': '18.0.1.0.0',
    'category': 'Services/SaaS',
    'summary': 'Multi-company SaaS with automatic company creation and licensing',
    'description': """
        SaaS Multi-Company Management
        ==============================

        Sell module access with automatic company creation and data isolation:

        * **Auto-Create Companies:** Automatically create companies for clients
        * **Data Isolation:** Users only see data from their company
        * **License Tracking:** Track usage per company (users, storage)
        * **Overage Billing:** Automatic billing for usage beyond limits
        * **Multi-Tenancy:** Multiple clients on same server, isolated data

        Perfect for:
        - ISVs selling module access
        - Consultants with multiple clients
        - Shared infrastructure SaaS

        Integrates with:
        - product_permissions (permission assignment)
        - saas_management (client management)
        - saas_licensing (usage tracking & billing)
    """,
    'author': 'AutomateAI',
    'website': 'https://automateai.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'portal',
        'sale_management',
        'product_permissions',
        'saas_management',
        'saas_licensing',
    ],
    'data': [
        # Security
        'security/saas_multicompany_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/saas_multicompany_data.xml',

        # Views
        'views/product_template_views.xml',
        'views/res_company_views.xml',
        'views/res_users_views.xml',
        'views/saas_client_views.xml',
        'views/saas_multicompany_menus.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}
