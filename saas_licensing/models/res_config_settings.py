# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Default Pricing Model
    default_pricing_model = fields.Selection([
        ('overage_only', 'Overage Only'),
        ('base_included_overage', 'Base + Included + Overage'),
        ('per_user', 'Per User'),
        ('base_per_user', 'Base + Per User'),
    ], string='Default Pricing Model',
       default='overage_only',
       config_parameter='saas_licensing.default_pricing_model')

    # Default Pricing
    default_base_monthly_price = fields.Float(
        string='Default Base Monthly Price',
        default=0.0,
        config_parameter='saas_licensing.default_base_monthly_price'
    )

    default_included_users = fields.Integer(
        string='Default Included Users',
        default=5,
        config_parameter='saas_licensing.default_included_users'
    )

    default_price_per_user = fields.Float(
        string='Default Price per User',
        default=50.0,
        config_parameter='saas_licensing.default_price_per_user'
    )

    # Default Limits
    default_max_users = fields.Integer(
        string='Default Max Users',
        default=0,
        config_parameter='saas_licensing.default_max_users',
        help='0 = unlimited'
    )

    default_max_companies = fields.Integer(
        string='Default Max Companies',
        default=1,
        config_parameter='saas_licensing.default_max_companies'
    )

    default_max_storage_gb = fields.Float(
        string='Default Max Storage (GB)',
        default=10.0,
        config_parameter='saas_licensing.default_max_storage_gb'
    )

    # Default Overage Pricing
    default_price_per_company = fields.Float(
        string='Default Price per Company',
        default=200.0,
        config_parameter='saas_licensing.default_price_per_company'
    )

    default_price_per_gb = fields.Float(
        string='Default Price per GB',
        default=10.0,
        config_parameter='saas_licensing.default_price_per_gb'
    )

    # Default Billing Configuration
    default_auto_invoice = fields.Boolean(
        string='Default Auto-Invoice',
        default=False,
        config_parameter='saas_licensing.default_auto_invoice'
    )

    default_invoice_on_overage = fields.Boolean(
        string='Default Invoice on Overage',
        default=True,
        config_parameter='saas_licensing.default_invoice_on_overage'
    )
