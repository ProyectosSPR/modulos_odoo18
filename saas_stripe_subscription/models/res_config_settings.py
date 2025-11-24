# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    stripe_subscription_sync_enabled = fields.Boolean(
        string='Enable Stripe Subscription Sync',
        config_parameter='saas_stripe_subscription.sync_enabled',
        default=True,
        help='Enable automatic synchronization of subscriptions with Stripe'
    )
    stripe_subscription_provider_id = fields.Many2one(
        'payment.provider',
        string='Default Stripe Provider for Subscriptions',
        domain=[('code', '=', 'stripe')],
        config_parameter='saas_stripe_subscription.default_provider_id',
        help='The default Stripe payment provider to use for subscription synchronization'
    )
    stripe_product_auto_sync = fields.Boolean(
        string='Auto-sync Products to Stripe',
        config_parameter='saas_stripe_subscription.product_auto_sync',
        default=True,
        help='Automatically create products in Stripe when they are added to subscriptions'
    )
