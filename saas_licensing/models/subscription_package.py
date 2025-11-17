# -*- coding: utf-8 -*-

from odoo import models, fields


class SubscriptionPackage(models.Model):
    _inherit = 'subscription.package'

    # License Limits
    max_users = fields.Integer(
        string='Max Users',
        default=10,
        help='Maximum number of users included in the plan (0 = unlimited)'
    )
    max_companies = fields.Integer(
        string='Max Companies',
        default=1,
        help='Maximum number of companies included in the plan (0 = unlimited)'
    )
    max_storage_gb = fields.Float(
        string='Max Storage (GB)',
        default=10.0,
        help='Maximum storage in GB included in the plan (0 = unlimited)'
    )

    # Overage Pricing
    price_per_user = fields.Float(
        string='Price per Additional User',
        default=10.0,
        help='Price charged per user beyond the plan limit'
    )
    price_per_company = fields.Float(
        string='Price per Additional Company',
        default=50.0,
        help='Price charged per company beyond the plan limit'
    )
    price_per_gb = fields.Float(
        string='Price per Additional GB',
        default=5.0,
        help='Price charged per GB beyond the plan storage limit'
    )
