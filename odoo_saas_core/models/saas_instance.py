# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class SaasInstance(models.Model):
    _name = 'saas.instance'
    _description = 'SaaS Odoo Instance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_created desc'

    # Basic Information
    name = fields.Char(string='Instance Name', required=True, tracking=True)
    subdomain = fields.Char(string='Subdomain', required=True, tracking=True)
    full_url = fields.Char(string='Full URL', compute='_compute_full_url', store=True)
    database_id = fields.Char(string='Database ID', readonly=True, copy=False)

    # Technical Details
    odoo_version = fields.Selection([
        ('16.0', 'Odoo 16.0'),
        ('17.0', 'Odoo 17.0'),
        ('18.0', 'Odoo 18.0'),
    ], string='Odoo Version', required=True, default='18.0', tracking=True)

    server_location = fields.Selection([
        ('us_east', 'US East'),
        ('eu_west', 'EU West'),
        ('asia_pacific', 'Asia Pacific'),
    ], string='Server Location', default='us_east')

    # Customer & Package
    customer_id = fields.Many2one(
        'saas.customer',
        string='Customer',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        related='customer_id.partner_id',
        string='Partner',
        store=True,
        readonly=True
    )
    service_package_id = fields.Many2one(
        'saas.service.package',
        string='Service Package',
        required=True,
        tracking=True
    )

    # Status Management
    status = fields.Selection([
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ], string='Status', default='trial', required=True, tracking=True)

    # Dates
    date_created = fields.Datetime(
        string='Created On',
        default=fields.Datetime.now,
        readonly=True
    )
    date_activated = fields.Datetime(string='Activated On', readonly=True)
    trial_end_date = fields.Datetime(
        string='Trial End Date',
        compute='_compute_trial_end_date',
        store=True
    )
    subscription_end_date = fields.Date(string='Subscription End Date', tracking=True)

    # Billing
    billing_cycle = fields.Selection([
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ], string='Billing Cycle', default='monthly', tracking=True)

    # Resource Usage
    current_users = fields.Integer(string='Current Users', default=1)
    max_users = fields.Integer(
        string='Max Users',
        related='service_package_id.max_users',
        store=True,
        readonly=True
    )
    storage_used_gb = fields.Float(string='Storage Used (GB)', default=0.0)
    max_storage_gb = fields.Float(
        string='Max Storage (GB)',
        related='service_package_id.storage_gb',
        store=True,
        readonly=True
    )

    # Computed Fields
    days_until_expiry = fields.Integer(
        string='Days Until Expiry',
        compute='_compute_days_until_expiry'
    )
    storage_percentage = fields.Float(
        string='Storage Usage %',
        compute='_compute_storage_percentage'
    )
    users_percentage = fields.Float(
        string='Users Usage %',
        compute='_compute_users_percentage'
    )

    # Provisioning Status
    is_provisioned = fields.Boolean(
        string='Access Provisioned',
        default=False,
        readonly=True,
        copy=False,
        help='Indicates if user access has been provisioned for this instance'
    )
    provisioned_company_id = fields.Many2one(
        'res.company',
        string='Provisioned Company',
        readonly=True,
        help='Company created for this SaaS instance'
    )

    # Subscription Link
    subscription_id = fields.Many2one(
        'subscription.package',
        string='Subscription',
        readonly=True
    )

    # Other
    company_id = fields.Many2one(
        'res.company',
        string='Odoo Company',
        default=lambda self: self.env.company
    )
    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('subdomain_unique', 'UNIQUE(subdomain)', 'Subdomain must be unique!'),
        ('database_id_unique', 'UNIQUE(database_id)', 'Database ID must be unique!'),
    ]

    @api.depends('subdomain')
    def _compute_full_url(self):
        base_domain = self.env['ir.config_parameter'].sudo().get_param(
            'saas.base_domain', 'odoo.cloud'
        )
        for record in self:
            if record.subdomain:
                record.full_url = f"https://{record.subdomain}.{base_domain}"
            else:
                record.full_url = False

    @api.depends('date_created')
    def _compute_trial_end_date(self):
        for record in self:
            if record.date_created:
                record.trial_end_date = record.date_created + timedelta(days=7)
            else:
                record.trial_end_date = False

    @api.depends('subscription_end_date')
    def _compute_days_until_expiry(self):
        today = fields.Date.today()
        for record in self:
            if record.subscription_end_date:
                delta = record.subscription_end_date - today
                record.days_until_expiry = delta.days
            else:
                record.days_until_expiry = 0

    @api.depends('storage_used_gb', 'max_storage_gb')
    def _compute_storage_percentage(self):
        for record in self:
            if record.max_storage_gb > 0:
                record.storage_percentage = (record.storage_used_gb / record.max_storage_gb) * 100
            else:
                record.storage_percentage = 0.0

    @api.depends('current_users', 'max_users')
    def _compute_users_percentage(self):
        for record in self:
            if record.max_users > 0:
                record.users_percentage = (record.current_users / record.max_users) * 100
            else:
                record.users_percentage = 0.0

    @api.constrains('current_users', 'max_users')
    def _check_users_limit(self):
        for record in self:
            if record.current_users > record.max_users:
                raise ValidationError(
                    _('Current users (%s) cannot exceed max users (%s)') %
                    (record.current_users, record.max_users)
                )

    @api.constrains('storage_used_gb', 'max_storage_gb')
    def _check_storage_limit(self):
        for record in self:
            if record.storage_used_gb > record.max_storage_gb:
                raise ValidationError(
                    _('Storage used (%.2f GB) cannot exceed max storage (%.2f GB)') %
                    (record.storage_used_gb, record.max_storage_gb)
                )

    def action_activate(self):
        """Activate instance from trial"""
        for record in self:
            record.write({
                'status': 'active',
                'date_activated': fields.Datetime.now()
            })
            record.message_post(body=_('Instance activated successfully'))

    def action_suspend(self):
        """Suspend instance"""
        for record in self:
            record.status = 'suspended'
            record.message_post(body=_('Instance suspended'))

    def action_terminate(self):
        """Terminate instance"""
        for record in self:
            record.write({
                'status': 'terminated',
                'is_provisioned': False
            })
            record.message_post(body=_('Instance terminated'))

    def action_extend_trial(self):
        """Extend trial by 7 days"""
        for record in self:
            if record.status == 'trial' and record.trial_end_date:
                new_end_date = record.trial_end_date + timedelta(days=7)
                record.trial_end_date = new_end_date
                record.message_post(
                    body=_('Trial period extended to %s') % new_end_date.strftime('%Y-%m-%d')
                )

    def action_provision_access(self):
        """Manually trigger provisioning (normally done by automation)"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Provision Access'),
            'res_model': 'saas.provision.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_instance_id': self.id},
        }

    @api.model
    def _cron_check_trial_expiry(self):
        """Cron job to check trial expiry"""
        today = fields.Datetime.now()
        trial_instances = self.search([
            ('status', '=', 'trial'),
            ('trial_end_date', '<=', today)
        ])
        for instance in trial_instances:
            instance.write({'status': 'expired'})
            instance.message_post(body=_('Trial period expired'))

    @api.model
    def _cron_check_subscription_expiry(self):
        """Cron job to check subscription expiry"""
        today = fields.Date.today()
        active_instances = self.search([
            ('status', '=', 'active'),
            ('subscription_end_date', '<=', today)
        ])
        for instance in active_instances:
            instance.write({'status': 'expired'})
            instance.message_post(body=_('Subscription expired'))
