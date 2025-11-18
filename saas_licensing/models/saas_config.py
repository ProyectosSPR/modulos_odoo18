# -*- coding: utf-8 -*-

from odoo import fields, models, api


class SaasLicensingConfig(models.TransientModel):
    _name = 'saas.licensing.config'
    _description = 'SaaS Licensing Default Configuration'

    # Default Pricing Model
    default_pricing_model = fields.Selection([
        ('overage_only', 'Overage Only'),
        ('base_included_overage', 'Base + Included + Overage'),
        ('per_user', 'Per User'),
        ('base_per_user', 'Base + Per User'),
    ], string='Default Pricing Model',
       default='base_per_user')

    # Default Pricing
    default_base_monthly_price = fields.Float(
        string='Default Base Monthly Price',
        default=200.0
    )

    default_included_users = fields.Integer(
        string='Default Included Users',
        default=5
    )

    default_price_per_user = fields.Float(
        string='Default Price per User',
        default=50.0
    )

    # Default Limits
    default_max_users = fields.Integer(
        string='Default Max Users',
        default=0,
        help='0 = unlimited'
    )

    default_max_companies = fields.Integer(
        string='Default Max Companies',
        default=1
    )

    default_max_storage_gb = fields.Float(
        string='Default Max Storage (GB)',
        default=10.0
    )

    # Default Overage Pricing
    default_price_per_company = fields.Float(
        string='Default Price per Company',
        default=200.0
    )

    default_price_per_gb = fields.Float(
        string='Default Price per GB',
        default=10.0
    )

    # Default Billing Configuration
    default_auto_invoice = fields.Boolean(
        string='Default Auto-Invoice',
        default=False
    )

    default_invoice_on_overage = fields.Boolean(
        string='Default Invoice on Overage',
        default=True
    )

    @api.model
    def default_get(self, fields_list):
        """Load current values from system parameters"""
        res = super().default_get(fields_list)

        ICP = self.env['ir.config_parameter'].sudo()

        res.update({
            'default_pricing_model': ICP.get_param('saas_licensing.default_pricing_model', 'base_per_user'),
            'default_base_monthly_price': float(ICP.get_param('saas_licensing.default_base_monthly_price', '200.0')),
            'default_included_users': int(ICP.get_param('saas_licensing.default_included_users', '5')),
            'default_price_per_user': float(ICP.get_param('saas_licensing.default_price_per_user', '50.0')),
            'default_max_users': int(ICP.get_param('saas_licensing.default_max_users', '0')),
            'default_max_companies': int(ICP.get_param('saas_licensing.default_max_companies', '1')),
            'default_max_storage_gb': float(ICP.get_param('saas_licensing.default_max_storage_gb', '10.0')),
            'default_price_per_company': float(ICP.get_param('saas_licensing.default_price_per_company', '200.0')),
            'default_price_per_gb': float(ICP.get_param('saas_licensing.default_price_per_gb', '10.0')),
            'default_auto_invoice': ICP.get_param('saas_licensing.default_auto_invoice', 'False') == 'True',
            'default_invoice_on_overage': ICP.get_param('saas_licensing.default_invoice_on_overage', 'True') == 'True',
        })

        return res

    def action_save(self):
        """Save configuration to system parameters"""
        self.ensure_one()

        ICP = self.env['ir.config_parameter'].sudo()

        ICP.set_param('saas_licensing.default_pricing_model', self.default_pricing_model)
        ICP.set_param('saas_licensing.default_base_monthly_price', str(self.default_base_monthly_price))
        ICP.set_param('saas_licensing.default_included_users', str(self.default_included_users))
        ICP.set_param('saas_licensing.default_price_per_user', str(self.default_price_per_user))
        ICP.set_param('saas_licensing.default_max_users', str(self.default_max_users))
        ICP.set_param('saas_licensing.default_max_companies', str(self.default_max_companies))
        ICP.set_param('saas_licensing.default_max_storage_gb', str(self.default_max_storage_gb))
        ICP.set_param('saas_licensing.default_price_per_company', str(self.default_price_per_company))
        ICP.set_param('saas_licensing.default_price_per_gb', str(self.default_price_per_gb))
        ICP.set_param('saas_licensing.default_auto_invoice', str(self.default_auto_invoice))
        ICP.set_param('saas_licensing.default_invoice_on_overage', str(self.default_invoice_on_overage))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Default configuration saved successfully',
                'type': 'success',
                'sticky': False,
            }
        }
