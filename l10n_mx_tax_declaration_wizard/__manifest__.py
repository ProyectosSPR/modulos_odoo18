# -*- coding: utf-8 -*-
{
    'name': 'México - Wizard de Declaraciones Fiscales SAT',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Wizard guiado paso a paso para generar declaraciones fiscales ante el SAT',
    'description': '''
        Wizard de Declaraciones Fiscales SAT México
        ============================================

        Este módulo proporciona un wizard multi-paso para generar
        declaraciones fiscales ante el SAT de manera guiada.

        Características principales:
        * Wizard guiado en 6 pasos
        * Selección de período y obligaciones fiscales
        * Selección y revisión de facturas a incluir
        * Integración con conciliación bancaria
        * Ejecución automática de cálculos fiscales
        * Revisión final antes de generar
        * Generación de declaración permanente

        Flujo del wizard:
        1. Configuración: Período y obligaciones
        2. Facturas: Selección y filtros
        3. Conciliación: Integración con módulo OCA
        4. Cálculos: Ejecución de reglas
        5. Revisión: Validación de resultados
        6. Reporte: Generación y guardado

        Requisitos:
        * l10n_mx_tax_declaration_base
        * account
        * mail

        Opcional:
        * account_reconcile_oca (para conciliación bancaria)

    ''',
    'author': 'IT Admin',
    'website': 'www.itadmin.com.mx',
    'license': 'OPL-1',
    'depends': [
        'l10n_mx_tax_declaration_base',
        'account',
        'mail',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/mx_tax_declaration_wizard_views.xml',
        'views/mx_tax_declaration_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
