# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Pricing Model
    saas_default_pricing_model = fields.Selection([
        ('overage_only', 'Overage Only'),
        ('base_included_overage', 'Base + Included + Overage'),
        ('per_user', 'Per User'),
        ('base_per_user', 'Base + Per User'),
    ], string='Default Pricing Model',
       config_parameter='saas_licensing.default_pricing_model',
       default='base_per_user')

    # Pricing
    saas_base_monthly_price = fields.Float(
        string='Default Base Monthly Price',
        config_parameter='saas_licensing.default_base_monthly_price',
        default=200.0
    )

    saas_included_users = fields.Integer(
        string='Default Included Users',
        config_parameter='saas_licensing.default_included_users',
        default=5
    )

    saas_price_per_user = fields.Float(
        string='Default Price per User',
        config_parameter='saas_licensing.default_price_per_user',
        default=50.0
    )

    # Limits
    saas_max_users = fields.Integer(
        string='Default Max Users',
        config_parameter='saas_licensing.default_max_users',
        default=0,
        help='0 = unlimited'
    )

    saas_max_companies = fields.Integer(
        string='Default Max Companies',
        config_parameter='saas_licensing.default_max_companies',
        default=1
    )

    saas_max_storage_gb = fields.Float(
        string='Default Max Storage (GB)',
        config_parameter='saas_licensing.default_max_storage_gb',
        default=10.0
    )

    # Overage Pricing
    saas_price_per_company = fields.Float(
        string='Default Price per Company',
        config_parameter='saas_licensing.default_price_per_company',
        default=200.0
    )

    saas_price_per_gb = fields.Float(
        string='Default Price per GB',
        config_parameter='saas_licensing.default_price_per_gb',
        default=10.0
    )

    # Billing Configuration
    saas_auto_invoice = fields.Boolean(
        string='Default Auto-Invoice',
        config_parameter='saas_licensing.default_auto_invoice',
        default=False
    )

    saas_invoice_on_overage = fields.Boolean(
        string='Default Invoice on Overage',
        config_parameter='saas_licensing.default_invoice_on_overage',
        default=True
    )
