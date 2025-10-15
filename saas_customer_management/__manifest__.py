{
    'name': 'SaaS Customer Management',
    'version': '17.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Manage SaaS customers, service packages, and Odoo instances',
    'description': '''
        Module to manage:
        - Customer information and company details
        - SaaS service packages subscription
        - Odoo instances management
        - Payment history tracking
        - Instance status monitoring
        - Support contact management
    ''',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'contacts', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/saas_service_package_data.xml',
        'views/saas_service_package_views.xml',
        'views/saas_customer_views.xml',
        'views/saas_instance_views.xml',
        'views/saas_payment_history_views.xml',
        'views/saas_menus.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
