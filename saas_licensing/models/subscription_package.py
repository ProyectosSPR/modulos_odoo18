# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SubscriptionPackage(models.Model):
    _inherit = 'subscription.package'

    def _get_default_pricing_model(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'saas_licensing.default_pricing_model', 'overage_only')

    def _get_default_base_monthly_price(self):
        return float(self.env['ir.config_parameter'].sudo().get_param(
            'saas_licensing.default_base_monthly_price', '0.0'))

    def _get_default_included_users(self):
        return int(self.env['ir.config_parameter'].sudo().get_param(
            'saas_licensing.default_included_users', '5'))

    def _get_default_price_per_user(self):
        return float(self.env['ir.config_parameter'].sudo().get_param(
            'saas_licensing.default_price_per_user', '50.0'))

    def _get_default_max_users(self):
        return int(self.env['ir.config_parameter'].sudo().get_param(
            'saas_licensing.default_max_users', '0'))

    def _get_default_max_companies(self):
        return int(self.env['ir.config_parameter'].sudo().get_param(
            'saas_licensing.default_max_companies', '1'))

    def _get_default_max_storage_gb(self):
        return float(self.env['ir.config_parameter'].sudo().get_param(
            'saas_licensing.default_max_storage_gb', '10.0'))

    def _get_default_price_per_company(self):
        return float(self.env['ir.config_parameter'].sudo().get_param(
            'saas_licensing.default_price_per_company', '200.0'))

    def _get_default_price_per_gb(self):
        return float(self.env['ir.config_parameter'].sudo().get_param(
            'saas_licensing.default_price_per_gb', '10.0'))

    def _get_default_auto_invoice(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'saas_licensing.default_auto_invoice', 'False') == 'True'

    def _get_default_invoice_on_overage(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'saas_licensing.default_invoice_on_overage', 'True') == 'True'

    # ===== PRICING MODEL =====
    pricing_model = fields.Selection([
        ('overage_only', 'Overage Only - Only charge overages'),
        ('base_included_overage', 'Base + Included + Overage'),
        ('per_user', 'Per User - Charge for every user'),
        ('base_per_user', 'Base + Per User - Hybrid model'),
    ], string='Pricing Model',
       default=_get_default_pricing_model,
       required=True,
       help="""Choose your pricing model:
       • Overage Only: Only charge when limits are exceeded
       • Base + Included + Overage: Base price includes X users, charge for additional
       • Per User: Charge per user, no base price
       • Base + Per User: Base price + charge for every user""")

    # ===== BASE PRICING =====
    base_monthly_price = fields.Float(
        string='Base Monthly Price',
        default=_get_default_base_monthly_price,
        help='Fixed monthly price for the subscription (company cost)'
    )

    # ===== USER PRICING =====
    included_users = fields.Integer(
        string='Included Users',
        default=_get_default_included_users,
        help='Number of users included in the base price (only for base_included_overage model)'
    )

    price_per_user = fields.Float(
        string='Price per User',
        default=_get_default_price_per_user,
        help='Price per user (varies by model: overage only / all users / additional users)'
    )

    # ===== LIMITS (Max allowed) =====
    max_users = fields.Integer(
        string='Max Users Allowed',
        default=_get_default_max_users,
        help='Maximum number of users allowed (0 = unlimited, just for alerts)'
    )
    max_companies = fields.Integer(
        string='Max Companies',
        default=_get_default_max_companies,
        help='Maximum number of companies included in the plan (0 = unlimited)'
    )
    max_storage_gb = fields.Float(
        string='Max Storage (GB)',
        default=_get_default_max_storage_gb,
        help='Maximum storage in GB included in the plan (0 = unlimited)'
    )

    # ===== OVERAGE PRICING =====
    price_per_company = fields.Float(
        string='Price per Additional Company',
        default=_get_default_price_per_company,
        help='Price charged per company beyond the plan limit'
    )
    price_per_gb = fields.Float(
        string='Price per Additional GB',
        default=_get_default_price_per_gb,
        help='Price charged per GB beyond the plan storage limit'
    )

    # ===== BILLING CONFIGURATION =====
    auto_invoice = fields.Boolean(
        string='Auto-Invoice',
        default=_get_default_auto_invoice,
        help='Automatically create invoices for usage (uses subscription_package cron if enabled)'
    )

    invoice_on_overage = fields.Boolean(
        string='Invoice on Overage Detection',
        default=_get_default_invoice_on_overage,
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
