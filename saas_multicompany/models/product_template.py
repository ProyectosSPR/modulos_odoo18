# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Multi-Company Configuration
    is_module_access = fields.Boolean(
        string='Is Module Access Product',
        default=False,
        help='Grants access to modules without creating a separate SaaS instance'
    )

    auto_create_company = fields.Boolean(
        string='Auto-Create Company',
        default=False,
        help='Automatically create a dedicated company for the client when sold'
    )

    company_template_id = fields.Many2one(
        'res.company',
        string='Company Template',
        help='Template company to copy settings from (optional)',
        domain=[('is_saas_template', '=', True)]
    )

    restrict_to_company = fields.Boolean(
        string='Restrict Access to Company',
        default=True,
        help='User can only access data from their assigned company'
    )

    multicompany_subscription_id = fields.Many2one(
        'subscription.package',
        string='Multi-Company Subscription',
        help='Subscription package for multi-company licensing (separate from SaaS instance licensing)'
    )

    @api.onchange('is_module_access')
    def _onchange_is_module_access(self):
        """Reset fields when toggling module access"""
        if not self.is_module_access:
            self.auto_create_company = False
            self.company_template_id = False
            self.restrict_to_company = True
            self.multicompany_subscription_id = False
