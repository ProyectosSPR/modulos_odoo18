# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaasCustomer(models.Model):
    _name = 'saas.customer'
    _description = 'SaaS Customer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_created desc'

    # Basic Information
    name = fields.Char(string='Customer Name', required=True, tracking=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Related Partner',
        required=True,
        ondelete='restrict',
        tracking=True,
        help="Partner record associated with this SaaS customer"
    )
    company_name = fields.Char(string='Company Name', tracking=True)
    tax_code = fields.Char(string='Tax ID / RFC', tracking=True)

    # Contact Information
    address = fields.Text(string='Address')
    phone = fields.Char(string='Phone', tracking=True)
    email = fields.Char(string='Email', required=True, tracking=True)
    website = fields.Char(string='Website')

    # Primary Contact
    contact_name = fields.Char(string='Contact Name', required=True, tracking=True)
    contact_email = fields.Char(string='Contact Email', required=True)
    contact_phone = fields.Char(string='Contact Phone')
    contact_position = fields.Char(string='Position')

    # Support Contact
    support_contact = fields.Char(string='Support Contact')
    support_email = fields.Char(string='Support Email')
    support_phone = fields.Char(string='Support Phone')

    # Status & Lifecycle
    state = fields.Selection([
        ('prospect', 'Prospect'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
    ], string='Status', default='prospect', required=True, tracking=True)

    # Dates
    date_created = fields.Datetime(
        string='Created On',
        default=fields.Datetime.now,
        readonly=True
    )
    date_updated = fields.Datetime(string='Last Updated', readonly=True)
    date_activated = fields.Date(string='Activation Date', tracking=True)

    # Relationships
    instance_ids = fields.One2many(
        'saas.instance',
        'customer_id',
        string='Instances'
    )

    # Computed Fields
    instance_count = fields.Integer(
        string='Total Instances',
        compute='_compute_instance_count'
    )
    active_instance_count = fields.Integer(
        string='Active Instances',
        compute='_compute_active_instance_count'
    )
    total_revenue = fields.Monetary(
        string='Total Revenue',
        compute='_compute_total_revenue',
        currency_field='currency_id'
    )

    # Additional Fields
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        'res.users',
        string='Account Manager',
        default=lambda self: self.env.user,
        tracking=True
    )
    tag_ids = fields.Many2many(
        'res.partner.category',
        string='Tags'
    )
    notes = fields.Text(string='Internal Notes')

    _sql_constraints = [
        ('email_unique', 'UNIQUE(email)', 'Email must be unique!'),
    ]

    @api.depends('instance_ids')
    def _compute_instance_count(self):
        for record in self:
            record.instance_count = len(record.instance_ids)

    @api.depends('instance_ids', 'instance_ids.status')
    def _compute_active_instance_count(self):
        for record in self:
            record.active_instance_count = len(
                record.instance_ids.filtered(lambda i: i.status == 'active')
            )

    def _compute_total_revenue(self):
        """Compute total revenue - can be extended by other modules"""
        for record in self:
            # Base implementation - can be extended by subscription module
            record.total_revenue = 0.0

    def write(self, vals):
        vals['date_updated'] = fields.Datetime.now()
        return super(SaasCustomer, self).write(vals)

    def action_view_instances(self):
        """Open instances list view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Instances'),
            'res_model': 'saas.instance',
            'view_mode': 'tree,form',
            'domain': [('customer_id', '=', self.id)],
            'context': {'default_customer_id': self.id},
        }

    def action_view_active_instances(self):
        """Open active instances list view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Active Instances'),
            'res_model': 'saas.instance',
            'view_mode': 'tree,form',
            'domain': [('customer_id', '=', self.id), ('status', '=', 'active')],
            'context': {'default_customer_id': self.id},
        }

    def action_activate(self):
        """Activate customer"""
        for record in self:
            record.write({
                'state': 'active',
                'date_activated': fields.Date.today()
            })

    def action_suspend(self):
        """Suspend customer"""
        for record in self:
            record.state = 'suspended'
            # Suspend all active instances
            record.instance_ids.filtered(
                lambda i: i.status == 'active'
            ).action_suspend()

    def action_terminate(self):
        """Terminate customer"""
        for record in self:
            record.state = 'terminated'
            # Terminate all instances
            record.instance_ids.action_terminate()

    @api.model
    def create(self, vals):
        """Override create to sync with partner"""
        customer = super(SaasCustomer, self).create(vals)

        # Update partner with SaaS customer flag
        if customer.partner_id:
            customer.partner_id.is_saas_customer = True

        return customer
