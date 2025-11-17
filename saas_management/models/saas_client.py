# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaasClient(models.Model):
    _name = 'saas.client'
    _description = 'SaaS Client'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Basic Info
    name = fields.Char(string='Client Name', required=True, tracking=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    email = fields.Char(related='partner_id.email', string='Email', readonly=True)
    phone = fields.Char(related='partner_id.phone', string='Phone', readonly=True)

    # Status
    state = fields.Selection([
        ('prospect', 'Prospect'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('churned', 'Churned'),
    ], string='Status', default='prospect', required=True, tracking=True)

    # Instances
    instance_ids = fields.One2many(
        'saas.instance',
        'client_id',
        string='Instances'
    )
    instance_count = fields.Integer(
        string='Total Instances',
        compute='_compute_instance_count'
    )
    active_instance_count = fields.Integer(
        string='Active Instances',
        compute='_compute_active_instance_count'
    )

    # Dates
    create_date = fields.Datetime(string='Created', readonly=True)
    activated_date = fields.Date(string='Activation Date', tracking=True)

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    @api.depends('instance_ids')
    def _compute_instance_count(self):
        for record in self:
            record.instance_count = len(record.instance_ids)

    @api.depends('instance_ids', 'instance_ids.state')
    def _compute_active_instance_count(self):
        for record in self:
            record.active_instance_count = len(
                record.instance_ids.filtered(lambda i: i.state == 'active')
            )

    def action_activate(self):
        """Activate client"""
        self.write({
            'state': 'active',
            'activated_date': fields.Date.today()
        })

    def action_suspend(self):
        """Suspend client and all instances"""
        self.state = 'suspended'
        self.instance_ids.filtered(lambda i: i.state == 'active').write({'state': 'suspended'})

    def action_view_instances(self):
        """View client instances"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Instances'),
            'res_model': 'saas.instance',
            'view_mode': 'list,form',
            'domain': [('client_id', '=', self.id)],
            'context': {'default_client_id': self.id},
        }
