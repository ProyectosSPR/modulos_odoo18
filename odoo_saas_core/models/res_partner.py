# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # SaaS Integration
    is_saas_customer = fields.Boolean(
        string='Is SaaS Customer',
        default=False,
        help='Indicates this partner is a SaaS customer'
    )
    saas_customer_id = fields.Many2one(
        'saas.customer',
        string='SaaS Customer Record',
        compute='_compute_saas_customer_id',
        store=True
    )
    saas_instance_count = fields.Integer(
        string='SaaS Instances',
        compute='_compute_saas_instance_count'
    )

    @api.depends('is_saas_customer')
    def _compute_saas_customer_id(self):
        for partner in self:
            if partner.is_saas_customer:
                saas_customer = self.env['saas.customer'].search([
                    ('partner_id', '=', partner.id)
                ], limit=1)
                partner.saas_customer_id = saas_customer.id if saas_customer else False
            else:
                partner.saas_customer_id = False

    def _compute_saas_instance_count(self):
        for partner in self:
            if partner.saas_customer_id:
                partner.saas_instance_count = len(partner.saas_customer_id.instance_ids)
            else:
                partner.saas_instance_count = 0

    def action_view_saas_customer(self):
        """Open SaaS customer record"""
        self.ensure_one()
        if self.saas_customer_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'SaaS Customer',
                'res_model': 'saas.customer',
                'res_id': self.saas_customer_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
