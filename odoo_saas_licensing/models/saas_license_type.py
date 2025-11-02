# -*- coding: utf-8 -*-

from odoo import models, fields


class SaasLicenseType(models.Model):
    _name = 'saas.license.type'
    _description = 'SaaS License Type'
    _order = 'sequence, name'

    name = fields.Char(string='License Type', required=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description')

    billing_model = fields.Selection([
        ('fixed', 'Fixed Price'),
        ('per_company', 'Per Company'),
        ('per_user', 'Per User'),
        ('hybrid', 'Hybrid (Company + User)'),
    ], string='Billing Model', default='per_company', required=True)

    default_max_companies = fields.Integer(string='Default Max Companies', default=1)
    default_max_users = fields.Integer(string='Default Max Users per Company', default=0)
    default_base_price = fields.Monetary(string='Default Base Price', currency_field='currency_id')
    default_price_per_company = fields.Monetary(string='Default Price/Company', currency_field='currency_id')
    default_price_per_user = fields.Monetary(string='Default Price/User', currency_field='currency_id')

    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'License type code must be unique!'),
    ]
