# -*- coding: utf-8 -*-
{
    'name': "SaaS_AccessManagement",

    'summary': "modulo para brindar productos de servicios saas",

    'description': """
este modulo es para poder brindar productos para ofrecer odoo como servicio saas junto con el modulo de sucripcion. 
    """,

    'author': "automateai",
    'website': "https://automateai.com.mx",

    'category': 'sales',
    'version': '0.1',

    # Cambia 'subscription_oca' por 'subscription_package'
    'depends': [
        'product',
        'sale_management',
        'website_sale',
        'subscription_package', # <-- CAMBIO AQUÍ
        'base_automation', 
    ],

    'data': [
        'security/ir.model.access.csv',
        'security/saas_security_rules.xml',
        'views/product_template_views.xml',
        'views/sale_subscription_views.xml',
        'data/automated_actions.xml',
    ],
    'installable': True,
    'application': True,
    'icon': 'saa_s__access_management/static/description/icon.png',
    'demo': [
        'demo/demo.xml',
    ],
}
