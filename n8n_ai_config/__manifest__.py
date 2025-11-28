# -*- coding: utf-8 -*-
{
    'name': "N8N AI Configurator",
    'summary': "Configuración de Agentes IA para N8N - Multi-tenant con templates compartidos",
    'description': """
        Sistema de configuración de agentes de IA para N8N.

        Características:
        - Configuración multi-tenant (por empresa y usuario)
        - Templates compartidos globalmente
        - Prompts y comportamientos personalizables
        - Descripción de acciones para que la IA sepa cuándo usarlas
        - APIs para consulta desde N8N
        - Logs de ejecución y analytics
        - Sistema de activación/desactivación de configuraciones
    """,
    'author': "Automateai",
    'website': "https://automateai.com.mx",
    'category': 'Productivity/AI',
    'version': '18.0.1.0',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
    ],
    'data': [
        'security/ai_security.xml',
        'security/ir.model.access.csv',
        'views/ai_agent_profile_views.xml',
        'views/ai_action_views.xml',
        'views/ai_execution_log_views.xml',
        'views/ai_menus.xml',
        'data/ai_templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
