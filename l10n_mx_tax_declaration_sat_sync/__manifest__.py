# -*- coding: utf-8 -*-
{
    'name': 'México - Declaraciones Fiscales SAT Sync Integration',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Integración entre Declaraciones Fiscales y SAT Sync',
    'description': '''
        Integración Declaraciones Fiscales - SAT Sync
        ==============================================

        Este módulo conecta el sistema de declaraciones fiscales con
        el módulo de importación de facturas del SAT.

        Funcionalidades:
        * Auto-marcado de facturas importadas del SAT para declaración
        * Extensión del wizard de importación
        * Configuración de período fiscal automático
        * Sincronización de datos fiscales

    ''',
    'author': 'IT Admin',
    'website': 'www.itadmin.com.mx',
    'license': 'OPL-1',
    'depends': [
        'l10n_mx_tax_declaration_base',
        'l10n_mx_sat_sync_itadmin',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/cfdi_invoice_views.xml',
        'views/ir_attachment_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,  # Se instala automáticamente si ambos módulos están presentes
}
