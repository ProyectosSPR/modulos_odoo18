# -*- coding: utf-8 -*-
{
    'name': 'México - Conciliación Automática Avanzada',
    'version': '18.0.1.0.2',
    'category': 'Accounting/Localizations',
    'summary': 'Conciliación automática inteligente con reglas personalizables y modo inverso',
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
        - Sistema unificado con 3 modos: Directo, Relación, Relación Inversa
        - Match exacto, contiene, like, regex
        - Búsqueda en documentos relacionados (órdenes de venta/compra)
        - Búsqueda inversa: desde órdenes hacia pagos
        - Score de confianza para cada match
        - Wizard de prueba con tabla detallada de resultados
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
        'l10n_mx_sat_sync_itadmin',
        'l10n_mx_edi',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/mx_reconcile_rule_data.xml',
        'data/mx_reconcile_rule_unified_data.xml',
        'views/mx_reconcile_rule_views.xml',
        'views/mx_reconcile_relation_rule_views.xml',
        'views/mx_reconcile_rule_unified_views.xml',
        'views/mx_reconcile_log_views.xml',
        'views/account_bank_statement_line_views.xml',
        'views/account_payment_views.xml',
        'wizard/mx_auto_reconcile_wizard_views.xml',
        'wizard/mx_mark_non_deductible_wizard_views.xml',
        'wizard/mx_reconcile_rule_test_wizard_unified_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
