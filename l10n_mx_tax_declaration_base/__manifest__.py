# -*- coding: utf-8 -*-
{
    'name': 'México - Declaraciones Fiscales SAT (Base)',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Sistema base para declaraciones fiscales ante el SAT en México',
    'description': '''
        Sistema de Declaraciones Fiscales SAT México - Módulo Base
        ===========================================================

        Este módulo proporciona la infraestructura base para generar
        declaraciones fiscales ante el SAT en México.

        Características principales:
        * Configuración de obligaciones fiscales por empresa
        * Motor de cálculo dinámico con fórmulas programables
        * Marcado de facturas para inclusión en declaraciones
        * Soporte para todas las obligaciones fiscales del SAT
        * Editor visual y de código para reglas de cálculo

        Obligaciones fiscales soportadas:
        * IVA (Impuesto al Valor Agregado)
        * ISR (Impuesto Sobre la Renta)
        * IEPS (Impuesto Especial sobre Producción y Servicios)
        * IDE (Impuesto a los Depósitos en Efectivo)
        * ISAN (Impuesto Sobre Automóviles Nuevos)
        * ISN (Impuesto Sobre Nómina)
        * RIF/RESICO (Régimen Simplificado de Confianza)
        * Retenciones (ISR, IVA, IEPS)
        * DIOT (Declaración Informativa de Operaciones con Terceros)

    ''',
    'author': 'IT Admin',
    'website': 'www.itadmin.com.mx',
    'license': 'OPL-1',
    'depends': [
        'account',
        'l10n_mx',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/mx_tax_periodicity_data.xml',
        'data/mx_tax_obligation_type_data.xml',
        'views/mx_tax_calculation_rule_views.xml',
        'views/mx_tax_obligation_views.xml',
        'views/account_move_views.xml',
        'views/res_company_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
