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
    saas_customer_ids = fields.One2many(
        'saas.customer',
        'partner_id',
        string='SaaS Customer Records',
        help='All SaaS customer records linked to this partner'
    )
    saas_customer_id = fields.Many2one(
        'saas.customer',
        string='Primary SaaS Customer',
        compute='_compute_saas_customer_id',
        store=True,
        help='Primary SaaS customer record (first one found)'
    )
    saas_customer_count = fields.Integer(
        string='SaaS Customers',
        compute='_compute_saas_customer_count',
        help='Number of SaaS customer records'
    )
    saas_instance_count = fields.Integer(
        string='SaaS Instances',
        compute='_compute_saas_instance_count',
        help='Total number of SaaS instances across all customer records'
    )

    @api.depends('saas_customer_ids')
    def _compute_saas_customer_id(self):
        """Compute primary SaaS customer (first one)"""
        for partner in self:
            partner.saas_customer_id = partner.saas_customer_ids[:1] if partner.saas_customer_ids else False

    @api.depends('saas_customer_ids')
    def _compute_saas_customer_count(self):
        """Count SaaS customer records"""
        for partner in self:
            partner.saas_customer_count = len(partner.saas_customer_ids)

    @api.depends('saas_customer_ids', 'saas_customer_ids.instance_ids')
    def _compute_saas_instance_count(self):
        """Count total SaaS instances across all customer records"""
        for partner in self:
            total_instances = 0
            for customer in partner.saas_customer_ids:
                total_instances += len(customer.instance_ids)
            partner.saas_instance_count = total_instances

    def action_view_saas_customers(self):
        """View all SaaS customer records for this partner"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'SaaS Customers',
            'res_model': 'saas.customer',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    def action_view_saas_customer(self):
        """Open primary SaaS customer record"""
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

    def action_view_saas_instances(self):
        """View all SaaS instances for this partner"""
        self.ensure_one()
        instance_ids = []
        for customer in self.saas_customer_ids:
            instance_ids.extend(customer.instance_ids.ids)
        return {
            'type': 'ir.actions.act_window',
            'name': 'SaaS Instances',
            'res_model': 'saas.instance',
            'view_mode': 'list,form',
            'domain': [('id', 'in', instance_ids)],
        }
