# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta


class SaasInstance(models.Model):
    _name = 'saas.instance'
    _description = 'SaaS Odoo Instance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Basic Info
    name = fields.Char(string='Instance Name', required=True, tracking=True)
    subdomain = fields.Char(string='Subdomain', required=True, tracking=True)
    full_url = fields.Char(string='Full URL', compute='_compute_full_url', store=True)

    # Client & Subscription
    client_id = fields.Many2one(
        'saas.client',
        string='Client',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        related='client_id.partner_id',
        string='Partner',
        store=True,
        readonly=True
    )
    subscription_id = fields.Many2one(
        'subscription.package',
        string='Subscription',
        readonly=True
    )

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
    ], string='Status', default='draft', required=True, tracking=True)

    # Odoo Version
    odoo_version = fields.Selection([
        ('16.0', 'Odoo 16.0'),
        ('17.0', 'Odoo 17.0'),
        ('18.0', 'Odoo 18.0'),
    ], string='Odoo Version', default='18.0', required=True)

    # Dates
    create_date = fields.Datetime(string='Created', readonly=True)
    trial_end_date = fields.Date(string='Trial End Date', tracking=True)
    activated_date = fields.Datetime(string='Activated', readonly=True)

    # Resource Usage
    current_users = fields.Integer(string='Current Users', default=1)
    storage_used_gb = fields.Float(string='Storage Used (GB)', default=0.0)

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    # Notes
    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('subdomain_unique', 'UNIQUE(subdomain)', 'Subdomain must be unique!'),
    ]

    @api.depends('subdomain')
    def _compute_full_url(self):
        """Compute full URL from subdomain"""
        base_domain = self.env['ir.config_parameter'].sudo().get_param(
            'saas.base_domain', 'odoo.cloud'
        )
        for record in self:
            if record.subdomain:
                record.full_url = f"https://{record.subdomain}.{base_domain}"
            else:
                record.full_url = False

    def action_start_trial(self):
        """Start trial period"""
        self.write({
            'state': 'trial',
            'trial_end_date': fields.Date.today() + timedelta(days=7)
        })

    def action_activate(self):
        """Activate instance"""
        self.write({
            'state': 'active',
            'activated_date': fields.Datetime.now()
        })

    def action_suspend(self):
        """Suspend instance"""
        self.state = 'suspended'

    def action_terminate(self):
        """Terminate instance"""
        self.state = 'terminated'
