# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaasClient(models.Model):
    _inherit = 'saas.client'

    # Local Companies (multi-tenancy in same server)
    company_ids = fields.One2many(
        'res.company',
        'saas_client_id',
        string='Local Companies',
        help='Companies created for this client in the local server'
    )

    company_count = fields.Integer(
        string='Local Companies',
        compute='_compute_company_count'
    )

    @api.depends('company_ids')
    def _compute_company_count(self):
        for client in self:
            client.company_count = len(client.company_ids)

    def action_view_companies(self):
        """View companies for this client"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Companies'),
            'res_model': 'res.company',
            'view_mode': 'list,form',
            'domain': [('saas_client_id', '=', self.id)],
            'context': {'default_saas_client_id': self.id},
        }
