# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class MxTaxObligation(models.Model):
    """Obligaciones fiscales configuradas por empresa"""
    _name = 'mx.tax.obligation'
    _description = 'Obligación Fiscal de Empresa'
    _order = 'company_id, sequence, name'

    name = fields.Char(
        string='Nombre',
        compute='_compute_name',
        store=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
    )
    obligation_type_id = fields.Many2one(
        'mx.tax.obligation.type',
        string='Tipo de Obligación',
        required=True,
        ondelete='restrict',
    )
    periodicity_id = fields.Many2one(
        'mx.tax.periodicity',
        string='Periodicidad',
        required=True,
        ondelete='restrict',
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
    )
    active = fields.Boolean(
        default=True,
    )

    # Configuración de fechas límite
    deadline_day = fields.Integer(
        string='Día Límite de Pago',
        default=17,
        help='Día del mes siguiente para presentar la declaración',
    )

    # Reglas de cálculo
    calculation_rule_ids = fields.One2many(
        'mx.tax.calculation.rule',
        'obligation_id',
        string='Reglas de Cálculo',
    )

    # Campos relacionados para facilitar búsquedas
    obligation_category = fields.Selection(
        related='obligation_type_id.category',
        string='Categoría',
        store=True,
    )
    obligation_code = fields.Char(
        related='obligation_type_id.code',
        string='Código SAT',
        store=True,
    )

    # Configuración adicional
    auto_include_invoices = fields.Boolean(
        string='Auto-incluir Facturas',
        default=True,
        help='Marcar automáticamente las facturas nuevas para incluir en declaración',
    )
    invoice_type_filter = fields.Selection([
        ('all', 'Todas'),
        ('out_invoice', 'Solo Facturas de Cliente'),
        ('in_invoice', 'Solo Facturas de Proveedor'),
        ('out_refund', 'Solo Notas de Crédito de Cliente'),
        ('in_refund', 'Solo Notas de Crédito de Proveedor'),
    ], string='Filtro de Tipo de Factura', default='all')

    notes = fields.Text(
        string='Notas',
    )

    @api.depends('obligation_type_id', 'periodicity_id', 'company_id')
    def _compute_name(self):
        for record in self:
            if record.obligation_type_id and record.periodicity_id:
                periodicity_name = dict(record.periodicity_id._fields['code'].selection).get(
                    record.periodicity_id.code, ''
                )
                record.name = f"{record.obligation_type_id.name} - {periodicity_name}"
            else:
                record.name = _('Nueva Obligación Fiscal')

    @api.constrains('deadline_day')
    def _check_deadline_day(self):
        for record in self:
            if record.deadline_day < 1 or record.deadline_day > 31:
                raise ValidationError(_('El día límite debe estar entre 1 y 31'))

    _sql_constraints = [
        ('company_obligation_unique',
         'unique(company_id, obligation_type_id, periodicity_id)',
         'Ya existe esta obligación con esta periodicidad para esta compañía'),
    ]
