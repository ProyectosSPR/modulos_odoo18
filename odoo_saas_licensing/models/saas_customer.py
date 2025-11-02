# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaasCustomer(models.Model):
    _inherit = 'saas.customer'

    # Licensing
    license_ids = fields.One2many('saas.license', 'customer_id', string='Licenses')
    license_count = fields.Integer(string='Licenses', compute='_compute_license_count')
    total_licensed_companies = fields.Integer(
        string='Total Licensed Companies',
        compute='_compute_total_licensed_companies'
    )

    @api.depends('license_ids')
    def _compute_license_count(self):
        for rec in self:
            rec.license_count = len(rec.license_ids.filtered(lambda l: l.state == 'active'))

    @api.depends('license_ids', 'license_ids.current_companies')
    def _compute_total_licensed_companies(self):
        for rec in self:
            rec.total_licensed_companies = sum(
                rec.license_ids.filtered(lambda l: l.state == 'active').mapped('current_companies')
            )

    def action_view_licenses(self):
        """View customer licenses"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Licenses',
            'res_model': 'saas.license',
            'view_mode': 'tree,form',
            'domain': [('customer_id', '=', self.id)],
            'context': {'default_customer_id': self.id},
        }
