# -*- coding: utf-8 -*-
{
    'name': "N8N Sales",
    'summary': "Vende y gestiona automatizaciones de n8n como productos.",
    'description': """
        Este módulo integra Odoo con n8n para permitir la venta de workflows de automatización.
        - Crea usuarios en n8n al confirmar una venta.
        - Permite a los clientes sincronizar workflows desde Odoo.
        - Configuración dinámica de nodos del workflow.
    """,
    'author': "Automateai",
    'website': "https://automateai.com.mx",
    'category': 'Sales/Sales',
    'version': '18.0.1.0',
    'depends': [
        'base',
        'sale_management',
        'odoo_saas_core',  # SaaS Core para gestión de clientes e instancias
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/n8n_sync_wizard_views.xml', # <-- NUEVO ARCHIVO DE VISTA
        'views/n8n_workflow_instance_views.xml',
        'views/product_template_views.xml',
        'views/res_config_settings_views.xml',
        'views/n8n_menus.xml',
    ],
    'installable': True,
    'application': True,
}

