# -*- coding: utf-8 -*-
{
    'name': 'México - Conciliación Automática Avanzada',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Conciliación automática inteligente con reglas personalizables',
    'description': '''
        Conciliación Automática Avanzada para México
        =============================================
        
        Módulo de conciliación automática con reglas inteligentes que permite:
        
        * Reglas de conciliación directa (campo a campo)
        * Reglas por relación (a través de órdenes de venta/compra)
        * Búsqueda con regex y fuzzy matching
        * Integración con account_reconcile_oca
        * Marcado manual de pagos no deducibles
        * Log completo de auditoría
        
        Características:
        - Match exacto, contiene, like, regex
        - Búsqueda en documentos relacionados
        - Score de confianza para cada match
        - Vista embebida en wizard de declaraciones
        - Opción de vista completa de conciliación
        - Wizard para marcar no deducibles manualmente
    ''',
    'author': 'IT Admin',
    'website': 'www.itadmin.com.mx',
    'license': 'OPL-1',
    'depends': [
        'account',
        'account_reconcile_oca',
        'l10n_mx_tax_declaration_base',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/mx_reconcile_rule_data.xml',
        'views/mx_reconcile_rule_views.xml',
        'views/mx_reconcile_relation_rule_views.xml',
        'views/mx_reconcile_log_views.xml',
        'views/account_bank_statement_line_views.xml',
        'views/account_payment_views.xml',
        'views/menu_views.xml',
        'wizard/mx_auto_reconcile_wizard_views.xml',
        'wizard/mx_mark_non_deductible_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
