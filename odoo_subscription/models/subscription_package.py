# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class SubscriptionPackage(models.Model):
    _inherit = 'subscription.package'
    _description = 'Subscription Package - SaaS Extension'

    # ============================================================================
    # SaaS-SPECIFIC FIELDS (New fields not in base subscription_package)
    # ============================================================================

    # SaaS Customer Integration
    saas_customer_id = fields.Many2one(
        'saas.customer',
        string='SaaS Customer',
        ondelete='restrict',
        tracking=True,
        help='Link to SaaS customer record for instance management'
    )

    # SaaS Instances Management
    saas_instance_ids = fields.One2many(
        'saas.instance',
        'subscription_id',
        string='SaaS Instances',
        help='Odoo instances provisioned for this subscription'
    )
    instance_count = fields.Integer(
        string='Instances',
        compute='_compute_instance_count',
        help='Number of active SaaS instances'
    )

    # Usage-Based Billing (Metering) - SaaS Enhancement
    enable_metering = fields.Boolean(
        string='Enable Usage Metering',
        default=False,
        help='Enable usage-based billing for this subscription'
    )
    metering_ids = fields.One2many(
        'subscription.metering',
        'subscription_id',
        string='Usage Records',
        help='Track resource usage for billing'
    )

    # ============================================================================
    # COMPUTE METHODS - SaaS Specific
    # ============================================================================

    @api.depends('saas_instance_ids')
    def _compute_instance_count(self):
        """Count active SaaS instances linked to this subscription"""
        for rec in self:
            rec.instance_count = len(rec.saas_instance_ids)

    # ============================================================================
    # ACTIONS - SaaS Specific
    # ============================================================================

    def action_view_instances(self):
        """View SaaS instances linked to this subscription"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('SaaS Instances'),
            'res_model': 'saas.instance',
            'view_mode': 'list,form',
            'domain': [('subscription_id', '=', self.id)],
            'context': {'default_subscription_id': self.id},
        }

    def action_provision_instance(self):
        """Open wizard to provision a new SaaS instance"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Provision SaaS Instance'),
            'res_model': 'saas.instance.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_subscription_id': self.id,
                'default_customer_id': self.saas_customer_id.id,
            },
        }

    # ============================================================================
    # BUSINESS LOGIC - SaaS Extensions
    # ============================================================================

    def button_start_date(self):
        """Override to handle SaaS customer creation"""
        res = super(SubscriptionPackage, self).button_start_date()

        # Auto-create SaaS customer if not exists
        for rec in self:
            if not rec.saas_customer_id and rec.partner_id:
                customer_vals = {
                    'name': rec.partner_id.name,
                    'partner_id': rec.partner_id.id,
                    'email': rec.partner_id.email or '',
                    'phone': rec.partner_id.phone or '',
                    'contact_name': rec.partner_id.name,
                    'contact_email': rec.partner_id.email or '',
                }
                saas_customer = self.env['saas.customer'].create(customer_vals)
                rec.saas_customer_id = saas_customer.id
                rec.message_post(body=_('SaaS Customer %s created automatically') % saas_customer.name)

        return res
