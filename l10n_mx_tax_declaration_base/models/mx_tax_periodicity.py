# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class MxTaxPeriodicity(models.Model):
    """Catálogo de periodicidades para declaraciones fiscales"""
    _name = 'mx.tax.periodicity'
    _description = 'Periodicidad de Declaración Fiscal'
    _order = 'sequence, name'

    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True,
    )
    code = fields.Selection([
        ('01', '01 - Mensual'),
        ('02', '02 - Bimestral'),
        ('03', '03 - Trimestral'),
        ('04', '04 - Cuatrimestral'),
        ('05', '05 - Semestral'),
        ('06', '06 - Anual'),
        ('07', '07 - Bienal'),
        ('08', '08 - Quinquenal'),
        ('09', '09 - Decenal'),
        ('10', '10 - Por operación'),
    ], string='Código', required=True)

    sequence = fields.Integer(
        string='Secuencia',
        default=10,
    )
    months = fields.Integer(
        string='Meses',
        help='Número de meses que abarca la periodicidad',
    )
    days = fields.Integer(
        string='Días',
        help='Número de días para periodicidades especiales',
    )
    active = fields.Boolean(
        default=True,
    )

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'El código de la periodicidad debe ser único'),
    ]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, dict(self._fields['code'].selection).get(record.code)))
        return result
