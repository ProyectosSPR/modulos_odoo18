# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class MxTaxObligationType(models.Model):
    """Catálogo de tipos de obligaciones fiscales del SAT"""
    _name = 'mx.tax.obligation.type'
    _description = 'Tipo de Obligación Fiscal México'
    _order = 'sequence, name'

    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True,
    )
    code = fields.Char(
        string='Código SAT',
        required=True,
        help='Código oficial del SAT para esta obligación',
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
    )
    description = fields.Text(
        string='Descripción',
        translate=True,
    )
    active = fields.Boolean(
        default=True,
    )
    category = fields.Selection([
        ('iva', 'IVA - Impuesto al Valor Agregado'),
        ('isr', 'ISR - Impuesto Sobre la Renta'),
        ('ieps', 'IEPS - Impuesto Especial sobre Producción y Servicios'),
        ('ide', 'IDE - Impuesto a los Depósitos en Efectivo'),
        ('isan', 'ISAN - Impuesto Sobre Automóviles Nuevos'),
        ('isn', 'ISN - Impuesto Sobre Nómina'),
        ('resico', 'RESICO - Régimen Simplificado de Confianza'),
        ('retencion', 'Retenciones'),
        ('informativa', 'Declaración Informativa'),
        ('otros', 'Otros'),
    ], string='Categoría', required=True)

    default_periodicity_id = fields.Many2one(
        'mx.tax.periodicity',
        string='Periodicidad por Defecto',
        help='Periodicidad típica para esta obligación',
    )
    requires_electronic_accounting = fields.Boolean(
        string='Requiere Contabilidad Electrónica',
        default=False,
        help='Indica si esta obligación requiere envío de contabilidad electrónica',
    )
    has_complement = fields.Boolean(
        string='Tiene Complemento',
        default=False,
        help='Indica si se debe generar un complemento XML',
    )

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'El código de la obligación debe ser único'),
    ]

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result
