# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SaasLicense(models.Model):
    _name = 'saas.license'
    _description = 'SaaS License'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_created desc'

    # Basic Information
    name = fields.Char(string='License Name', compute='_compute_name', store=True)
    reference = fields.Char(string='Reference', readonly=True, copy=False, default=lambda self: _('New'))

    # Customer
    customer_id = fields.Many2one('saas.customer', string='Customer', required=True, tracking=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', related='customer_id.partner_id', string='Partner', store=True)

    # License Type & Configuration
    license_type_id = fields.Many2one('saas.license.type', string='License Type', required=True, tracking=True)
    billing_model = fields.Selection(related='license_type_id.billing_model', string='Billing Model', store=True)

    # Company Limits
    max_companies = fields.Integer(string='Max Companies', required=True, default=1, tracking=True)
    current_companies = fields.Integer(string='Current Companies', compute='_compute_current_companies', store=True)
    company_usage_percent = fields.Float(string='Usage %', compute='_compute_usage_percent')

    # User Limits (if applicable)
    max_users_per_company = fields.Integer(string='Max Users per Company', default=0,
                                           help='0 = unlimited')

    # Pricing
    base_price = fields.Monetary(string='Base Price', currency_field='currency_id', tracking=True)
    price_per_company = fields.Monetary(string='Price per Company', currency_field='currency_id', tracking=True)
    price_per_user = fields.Monetary(string='Price per User', currency_field='currency_id',
                                     help='If billing by user')

    # Licensed Companies
    licensed_company_ids = fields.One2many('saas.licensed.company', 'license_id', string='Licensed Companies')

    # Status & Lifecycle
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
    ], string='Status', default='draft', required=True, tracking=True)

    # Dates
    date_created = fields.Datetime(string='Created', default=fields.Datetime.now, readonly=True)
    date_activated = fields.Date(string='Activated', readonly=True)
    expiry_date = fields.Date(string='Expiry Date', tracking=True)

    # Subscription Integration
    subscription_id = fields.Many2one('subscription.package', string='Linked Subscription', tracking=True)

    # Alerts & Warnings
    alert_threshold = fields.Integer(string='Alert Threshold %', default=80,
                                    help='Send alert when usage reaches this percentage')
    last_alert_date = fields.Date(string='Last Alert Sent')

    # Other
    company_id = fields.Many2one('res.company', string='Odoo Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('max_companies_positive', 'CHECK(max_companies > 0)', 'Max companies must be greater than 0!'),
    ]

    @api.depends('customer_id', 'license_type_id', 'reference')
    def _compute_name(self):
        for rec in self:
            parts = []
            if rec.license_type_id:
                parts.append(rec.license_type_id.name)
            if rec.reference and rec.reference != _('New'):
                parts.append(rec.reference)
            if rec.customer_id:
                parts.append(rec.customer_id.name)
            rec.name = ' - '.join(parts) if parts else _('New License')

    @api.depends('licensed_company_ids', 'licensed_company_ids.is_active')
    def _compute_current_companies(self):
        for rec in self:
            rec.current_companies = len(rec.licensed_company_ids.filtered(lambda c: c.is_active))

    @api.depends('current_companies', 'max_companies')
    def _compute_usage_percent(self):
        for rec in self:
            if rec.max_companies > 0:
                rec.company_usage_percent = (rec.current_companies / rec.max_companies) * 100
            else:
                rec.company_usage_percent = 0.0

    @api.model
    def create(self, vals):
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('saas.license') or _('New')
        return super(SaasLicense, self).create(vals)

    @api.constrains('current_companies', 'max_companies')
    def _check_company_limit(self):
        for rec in self:
            if rec.current_companies > rec.max_companies:
                raise ValidationError(
                    _('Company limit exceeded! Current: %s, Max: %s') %
                    (rec.current_companies, rec.max_companies)
                )

    def action_activate(self):
        """Activate license"""
        for rec in self:
            rec.write({
                'state': 'active',
                'date_activated': fields.Date.today()
            })
            rec.message_post(body=_('License activated'))

    def action_suspend(self):
        """Suspend license"""
        for rec in self:
            rec.state = 'suspended'
            rec.message_post(body=_('License suspended'))

    def action_add_company(self):
        """Open wizard to add company"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Company to License'),
            'res_model': 'license.add.company.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_license_id': self.id},
        }

    def action_view_companies(self):
        """View licensed companies"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Licensed Companies'),
            'res_model': 'saas.licensed.company',
            'view_mode': 'tree,form',
            'domain': [('license_id', '=', self.id)],
            'context': {'default_license_id': self.id},
        }

    def check_and_send_alerts(self):
        """Check usage and send alerts if needed"""
        for rec in self:
            if rec.state == 'active' and rec.company_usage_percent >= rec.alert_threshold:
                if not rec.last_alert_date or rec.last_alert_date < fields.Date.today():
                    rec._send_usage_alert()
                    rec.last_alert_date = fields.Date.today()

    def _send_usage_alert(self):
        """Send usage alert email"""
        self.ensure_one()
        template = self.env.ref('odoo_saas_licensing.mail_template_license_usage_alert', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

        # Post message
        self.message_post(
            body=_('License usage alert: %s%% of companies used (%s / %s)') %
            (round(self.company_usage_percent, 2), self.current_companies, self.max_companies)
        )

    def update_subscription_pricing(self):
        """Update linked subscription based on current usage"""
        self.ensure_one()
        if not self.subscription_id:
            return

        # Calculate new price based on billing model
        if self.billing_model == 'per_company':
            new_price = self.base_price + (self.current_companies * self.price_per_company)
        elif self.billing_model == 'per_user':
            total_users = sum(self.licensed_company_ids.filtered('is_active').mapped('users_count'))
            new_price = self.base_price + (total_users * self.price_per_user)
        else:
            new_price = self.base_price

        # Update subscription (simplified - you'd want to create a new product line or update existing)
        self.subscription_id.message_post(
            body=_('License usage updated. New calculated price: %s %s') %
            (new_price, self.currency_id.symbol)
        )

    @api.model
    def _cron_check_license_limits(self):
        """Cron job to check license limits and send alerts"""
        active_licenses = self.search([('state', '=', 'active')])
        for license in active_licenses:
            license.check_and_send_alerts()
