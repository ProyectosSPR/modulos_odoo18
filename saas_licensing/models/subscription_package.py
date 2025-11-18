# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SubscriptionPackage(models.Model):
    _inherit = 'subscription.package'

    # ===== PRICING MODEL =====
    pricing_model = fields.Selection([
        ('overage_only', 'Overage Only - Only charge overages'),
        ('base_included_overage', 'Base + Included + Overage'),
        ('per_user', 'Per User - Charge for every user'),
        ('base_per_user', 'Base + Per User - Hybrid model'),
    ], string='Pricing Model',
       default='overage_only',
       required=True,
       help="""Choose your pricing model:
       • Overage Only: Only charge when limits are exceeded
       • Base + Included + Overage: Base price includes X users, charge for additional
       • Per User: Charge per user, no base price
       • Base + Per User: Base price + charge for every user""")

    # ===== BASE PRICING =====
    base_monthly_price = fields.Float(
        string='Base Monthly Price',
        default=0.0,
        help='Fixed monthly price for the subscription (company cost)'
    )

    # ===== USER PRICING =====
    included_users = fields.Integer(
        string='Included Users',
        default=5,
        help='Number of users included in the base price (only for base_included_overage model)'
    )

    price_per_user = fields.Float(
        string='Price per User',
        default=50.0,
        help='Price per user (varies by model: overage only / all users / additional users)'
    )

    # ===== LIMITS (Max allowed) =====
    max_users = fields.Integer(
        string='Max Users Allowed',
        default=0,
        help='Maximum number of users allowed (0 = unlimited, just for alerts)'
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

    # ===== OVERAGE PRICING =====
    price_per_company = fields.Float(
        string='Price per Additional Company',
        default=200.0,
        help='Price charged per company beyond the plan limit'
    )
    price_per_gb = fields.Float(
        string='Price per Additional GB',
        default=10.0,
        help='Price charged per GB beyond the plan storage limit'
    )

    # ===== BILLING CONFIGURATION =====
    auto_invoice = fields.Boolean(
        string='Auto-Invoice',
        default=False,
        help='Automatically create invoices for usage (uses subscription_package cron if enabled)'
    )

    invoice_on_overage = fields.Boolean(
        string='Invoice on Overage Detection',
        default=True,
        help='Create invoice automatically when overage is detected'
    )

    # ===== COMPUTED FIELDS FOR UI =====
    pricing_model_description = fields.Text(
        string='Pricing Description',
        compute='_compute_pricing_model_description',
        store=False
    )

    @api.depends('pricing_model', 'base_monthly_price', 'included_users', 'price_per_user', 'max_users')
    def _compute_pricing_model_description(self):
        """Generate description of how pricing works"""
        for record in self:
            if record.pricing_model == 'overage_only':
                record.pricing_model_description = f"""
                    Base Price: $0
                    Included Users: {record.included_users or record.max_users}
                    Only charge when users exceed {record.included_users or record.max_users}
                    Overage: ${record.price_per_user}/user

                    Example:
                    • 3 users = $0
                    • {record.included_users + 2} users = ${2 * record.price_per_user} (2 additional users)
                """
            elif record.pricing_model == 'base_included_overage':
                record.pricing_model_description = f"""
                    Base Price: ${record.base_monthly_price}/month
                    Included Users: {record.included_users}
                    Additional Users: ${record.price_per_user}/user

                    Example:
                    • 3 users = ${record.base_monthly_price}
                    • {record.included_users + 2} users = ${record.base_monthly_price + (2 * record.price_per_user)}
                """
            elif record.pricing_model == 'per_user':
                record.pricing_model_description = f"""
                    Base Price: $0
                    Price per User: ${record.price_per_user}/user (ALL users count)

                    Example:
                    • 3 users = ${3 * record.price_per_user}
                    • 5 users = ${5 * record.price_per_user}
                """
            elif record.pricing_model == 'base_per_user':
                record.pricing_model_description = f"""
                    Base Price: ${record.base_monthly_price}/month
                    Price per User: ${record.price_per_user}/user (ALL users count)

                    Example:
                    • 3 users = ${record.base_monthly_price + (3 * record.price_per_user)}
                    • 5 users = ${record.base_monthly_price + (5 * record.price_per_user)}
                """
            else:
                record.pricing_model_description = "Select a pricing model to see details"
