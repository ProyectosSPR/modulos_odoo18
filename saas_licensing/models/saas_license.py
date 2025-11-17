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
    overage_amount = fields.Float(
        string='Overage Amount',
        compute='_compute_overage_amount',
        store=True
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

    @api.depends('user_overage', 'company_overage', 'storage_overage')
    def _compute_is_billable(self):
        for record in self:
            record.is_billable = (
                record.user_overage > 0 or
                record.company_overage > 0 or
                record.storage_overage > 0
            )

    @api.depends('user_overage', 'company_overage', 'storage_overage', 'subscription_id')
    def _compute_overage_amount(self):
        for record in self:
            amount = 0.0

            if record.subscription_id:
                # User overage
                if record.user_overage > 0:
                    amount += record.user_overage * record.subscription_id.price_per_user

                # Company overage
                if record.company_overage > 0:
                    amount += record.company_overage * record.subscription_id.price_per_company

                # Storage overage
                if record.storage_overage > 0:
                    amount += record.storage_overage * record.subscription_id.price_per_gb

            record.overage_amount = amount

    def action_create_invoice(self):
        """Create invoice for overage charges"""
        self.ensure_one()

        if not self.is_billable:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Overages'),
                    'message': _('No billable overages for this license record.'),
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

        # Create invoice
        invoice_lines = []

        # User overage line
        if self.user_overage > 0:
            invoice_lines.append((0, 0, {
                'name': _('Additional Users - %s') % self.instance_id.name,
                'quantity': self.user_overage,
                'price_unit': self.subscription_id.price_per_user,
            }))

        # Company overage line
        if self.company_overage > 0:
            invoice_lines.append((0, 0, {
                'name': _('Additional Companies - %s') % self.instance_id.name,
                'quantity': self.company_overage,
                'price_unit': self.subscription_id.price_per_company,
            }))

        # Storage overage line
        if self.storage_overage > 0:
            invoice_lines.append((0, 0, {
                'name': _('Additional Storage (GB) - %s') % self.instance_id.name,
                'quantity': self.storage_overage,
                'price_unit': self.subscription_id.price_per_gb,
            }))

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
