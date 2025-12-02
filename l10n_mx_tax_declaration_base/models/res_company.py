# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResCompany(models.Model):
    """Extensión de compañía para configuración fiscal"""
    _inherit = 'res.company'

    # Obligaciones fiscales
    tax_obligation_ids = fields.One2many(
        'mx.tax.obligation',
        'company_id',
        string='Obligaciones Fiscales',
    )

    tax_obligation_count = fields.Integer(
        string='Número de Obligaciones',
        compute='_compute_tax_obligation_count',
    )

    # Configuración general de declaraciones
    tax_declaration_auto_mark = fields.Boolean(
        string='Auto-marcar Facturas',
        default=True,
        help='Marcar automáticamente facturas nuevas para incluir en declaraciones',
    )

    @api.depends('tax_obligation_ids')
    def _compute_tax_obligation_count(self):
        for record in self:
            record.tax_obligation_count = len(record.tax_obligation_ids)

    def action_view_tax_obligations(self):
        """Acción para ver obligaciones fiscales de la compañía"""
        self.ensure_one()
        return {
            'name': _('Obligaciones Fiscales'),
            'type': 'ir.actions.act_window',
            'res_model': 'mx.tax.obligation',
            'view_mode': 'list,form',
            'domain': [('company_id', '=', self.id)],
            'context': {'default_company_id': self.id},
        }
