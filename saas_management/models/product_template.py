# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # SaaS Configuration
    is_saas_instance = fields.Boolean(
        string='Is SaaS Instance Product',
        default=False,
        help='Check if this product represents a SaaS instance subscription'
    )

    auto_create_instance = fields.Boolean(
        string='Auto-Create Instance',
        default=False,
        help='Automatically create a SaaS instance when this product is sold'
    )

    trial_days = fields.Integer(
        string='Trial Days',
        default=7,
        help='Number of trial days for new instances'
    )

    subscription_package_id = fields.Many2one(
        'subscription.package',
        string='Subscription Package',
        help='Subscription package to assign to the created instance'
    )
