# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta


class SaasLicense(models.Model):
    _name = 'saas.license'
    _description = 'SaaS License Usage Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    # Basic Info
    name = fields.Char(string='License Record', compute='_compute_name', store=True)
    instance_id = fields.Many2one(
        'saas.instance',
        string='Instance',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    client_id = fields.Many2one(
        'saas.client',
        related='instance_id.client_id',
        string='Client',
        store=True,
        readonly=True
    )
    subscription_id = fields.Many2one(
        'subscription.package',
        related='instance_id.subscription_id',
        string='Subscription',
        store=True,
        readonly=True
    )

    # Date
    date = fields.Date(
        string='Record Date',
        default=fields.Date.today,
        required=True,
        tracking=True
    )

    # Usage Metrics
    user_count = fields.Integer(
        string='User Count',
        default=0,
        required=True,
        tracking=True
    )
    company_count = fields.Integer(
        string='Company Count',
        default=1,
        required=True,
        tracking=True
    )
    storage_gb = fields.Float(
        string='Storage (GB)',
        default=0.0,
        tracking=True
    )

    # Plan Limits (from subscription)
    plan_user_limit = fields.Integer(
        string='Plan User Limit',
        related='subscription_id.max_users',
        readonly=True
    )
    plan_company_limit = fields.Integer(
        string='Plan Company Limit',
        related='subscription_id.max_companies',
        readonly=True
    )
    plan_storage_limit = fields.Float(
        string='Plan Storage Limit (GB)',
        related='subscription_id.max_storage_gb',
        readonly=True
    )

    # Overages
    user_overage = fields.Integer(
        string='User Overage',
        compute='_compute_overages',
        store=True
    )
    company_overage = fields.Integer(
        string='Company Overage',
        compute='_compute_overages',
        store=True
    )
    storage_overage = fields.Float(
        string='Storage Overage (GB)',
        compute='_compute_overages',
        store=True
    )

    # Billing
    is_billable = fields.Boolean(
        string='Billable',
        compute='_compute_is_billable',
        store=True
    )
    base_amount = fields.Float(
        string='Base Amount',
        compute='_compute_billing_amounts',
        store=True,
        help='Base monthly price (depends on pricing model)'
    )
    user_amount = fields.Float(
        string='User Amount',
        compute='_compute_billing_amounts',
        store=True,
        help='Amount charged for users (depends on pricing model)'
    )
    overage_amount = fields.Float(
        string='Additional Overage Amount',
        compute='_compute_billing_amounts',
        store=True,
        help='Additional charges for companies and storage overages'
    )
    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_billing_amounts',
        store=True,
        help='Total amount to bill (base + users + overages)'
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        readonly=True
    )
    invoice_state = fields.Selection(
        related='invoice_id.state',
        string='Invoice Status',
        readonly=True
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    @api.depends('instance_id', 'date')
    def _compute_name(self):
        for record in self:
            if record.instance_id and record.date:
                record.name = f"{record.instance_id.name} - {record.date}"
            else:
                record.name = "New License Record"

    @api.depends('user_count', 'company_count', 'storage_gb',
                 'plan_user_limit', 'plan_company_limit', 'plan_storage_limit')
    def _compute_overages(self):
        for record in self:
            # User overage
            if record.plan_user_limit and record.user_count > record.plan_user_limit:
                record.user_overage = record.user_count - record.plan_user_limit
            else:
                record.user_overage = 0

            # Company overage
            if record.plan_company_limit and record.company_count > record.plan_company_limit:
                record.company_overage = record.company_count - record.plan_company_limit
            else:
                record.company_overage = 0

            # Storage overage
            if record.plan_storage_limit and record.storage_gb > record.plan_storage_limit:
                record.storage_overage = record.storage_gb - record.plan_storage_limit
            else:
                record.storage_overage = 0.0

    @api.depends('user_count', 'user_overage', 'company_overage', 'storage_overage', 'subscription_id',
                 'subscription_id.pricing_model', 'subscription_id.base_monthly_price',
                 'subscription_id.price_per_user', 'subscription_id.included_users')
    def _compute_billing_amounts(self):
        """Calculate billing amounts based on pricing model"""
        for record in self:
            base_amount = 0.0
            user_amount = 0.0
            overage_amount = 0.0

            if not record.subscription_id:
                record.base_amount = 0.0
                record.user_amount = 0.0
                record.overage_amount = 0.0
                record.total_amount = 0.0
                record.is_billable = False
                continue

            sub = record.subscription_id
            pricing_model = sub.pricing_model or 'overage_only'

            # === CALCULATE BASED ON PRICING MODEL ===

            if pricing_model == 'overage_only':
                # Only charge for users that exceed the limit
                base_amount = 0.0
                user_amount = 0.0
                if record.user_overage > 0:
                    user_amount = record.user_overage * sub.price_per_user

            elif pricing_model == 'base_included_overage':
                # Base price + charge for additional users beyond included
                base_amount = sub.base_monthly_price
                user_amount = 0.0
                if record.user_overage > 0:
                    user_amount = record.user_overage * sub.price_per_user

            elif pricing_model == 'per_user':
                # Charge for every user, no base price
                base_amount = 0.0
                user_amount = record.user_count * sub.price_per_user

            elif pricing_model == 'base_per_user':
                # Base price + charge for every user
                base_amount = sub.base_monthly_price
                user_amount = record.user_count * sub.price_per_user

            # === ADDITIONAL OVERAGES (company and storage) ===
            # These work the same for all models

            # Company overage
            if record.company_overage > 0:
                overage_amount += record.company_overage * sub.price_per_company

            # Storage overage
            if record.storage_overage > 0:
                overage_amount += record.storage_overage * sub.price_per_gb

            # === SET VALUES ===
            record.base_amount = base_amount
            record.user_amount = user_amount
            record.overage_amount = overage_amount
            record.total_amount = base_amount + user_amount + overage_amount

            # Is billable if there's any amount to charge
            record.is_billable = record.total_amount > 0

    @api.depends('total_amount')
    def _compute_is_billable(self):
        """Compute is_billable based on total amount"""
        for record in self:
            record.is_billable = record.total_amount > 0

    def action_create_invoice(self):
        """Create invoice based on pricing model"""
        self.ensure_one()

        if not self.is_billable:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Not Billable'),
                    'message': _('No charges for this license record.'),
                    'type': 'warning',
                }
            }

        if self.invoice_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Already Invoiced'),
                    'message': _('This license record has already been invoiced.'),
                    'type': 'warning',
                }
            }

        # Create invoice lines based on pricing model
        invoice_lines = []
        instance_name = self.instance_id.name if self.instance_id else (self.company_id.name if hasattr(self, 'company_id') else 'License')
        pricing_model = self.subscription_id.pricing_model or 'overage_only'

        # Base amount line (for applicable models)
        if self.base_amount > 0:
            invoice_lines.append((0, 0, {
                'name': _('Subscription Base - %s') % instance_name,
                'quantity': 1,
                'price_unit': self.base_amount,
            }))

        # User amount line (varies by model)
        if self.user_amount > 0:
            if pricing_model in ['overage_only', 'base_included_overage']:
                # Additional users (overage)
                invoice_lines.append((0, 0, {
                    'name': _('Additional Users (%s) - %s') % (self.user_overage, instance_name),
                    'quantity': self.user_overage,
                    'price_unit': self.subscription_id.price_per_user,
                }))
            elif pricing_model in ['per_user', 'base_per_user']:
                # All users
                invoice_lines.append((0, 0, {
                    'name': _('Users (%s) - %s') % (self.user_count, instance_name),
                    'quantity': self.user_count,
                    'price_unit': self.subscription_id.price_per_user,
                }))

        # Company overage line (always additional)
        if self.company_overage > 0:
            invoice_lines.append((0, 0, {
                'name': _('Additional Companies (%s) - %s') % (self.company_overage, instance_name),
                'quantity': self.company_overage,
                'price_unit': self.subscription_id.price_per_company,
            }))

        # Storage overage line (always additional)
        if self.storage_overage > 0:
            invoice_lines.append((0, 0, {
                'name': _('Additional Storage (%.2f GB) - %s') % (self.storage_overage, instance_name),
                'quantity': self.storage_overage,
                'price_unit': self.subscription_id.price_per_gb,
            }))

        if not invoice_lines:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('No invoice lines to create.'),
                    'type': 'danger',
                }
            }

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.client_id.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
        })

        self.invoice_id = invoice.id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def create_monthly_license_records(self):
        """
        Cron job to create monthly license records for all active instances
        """
        instances = self.env['saas.instance'].search([
            ('state', 'in', ['active', 'trial'])
        ])

        for instance in instances:
            # Check if record already exists for this month
            existing = self.search([
                ('instance_id', '=', instance.id),
                ('date', '=', fields.Date.today())
            ])

            if not existing:
                self.create({
                    'instance_id': instance.id,
                    'date': fields.Date.today(),
                    'user_count': instance.current_users,
                    'company_count': instance.company_count,
                    'storage_gb': instance.storage_used_gb,
                })

        return True
