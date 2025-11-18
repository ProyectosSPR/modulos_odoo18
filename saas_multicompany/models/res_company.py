# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    # SaaS Multi-Company Fields
    saas_client_id = fields.Many2one(
        'saas.client',
        string='SaaS Client',
        help='Client that owns this company (for multi-tenancy)',
        ondelete='restrict'
    )

    is_saas_company = fields.Boolean(
        string='Is SaaS Company',
        default=False,
        help='This company was created for a SaaS client'
    )

    is_saas_template = fields.Boolean(
        string='Is Template Company',
        default=False,
        help='This company can be used as a template for new SaaS companies'
    )

    # License tracking for this company
    license_ids = fields.One2many(
        'saas.license',
        'company_id',
        string='License Records'
    )

    license_count = fields.Integer(
        string='License Records',
        compute='_compute_license_count'
    )

    # Users assigned to this company
    user_count = fields.Integer(
        string='Active Users',
        compute='_compute_user_count'
    )

    # Current subscription
    subscription_id = fields.Many2one(
        'subscription.package',
        string='Subscription Package',
        help='Active subscription package for this company'
    )

    @api.depends('license_ids')
    def _compute_license_count(self):
        for company in self:
            company.license_count = len(company.license_ids)

    def _compute_user_count(self):
        for company in self:
            # Count active internal users in this company
            company.user_count = self.env['res.users'].search_count([
                ('company_ids', 'in', [company.id]),
                ('active', '=', True),
                ('share', '=', False),  # Only internal users
            ])

    def action_view_licenses(self):
        """View license records for this company"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('License Records'),
            'res_model': 'saas.license',
            'view_mode': 'list,form',
            'domain': [('company_id', '=', self.id)],
            'context': {
                'default_company_id': self.id,
                'default_client_id': self.saas_client_id.id,
            },
        }

    def action_view_users(self):
        """View users assigned to this company"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Users'),
            'res_model': 'res.users',
            'view_mode': 'list,form',
            'domain': [('company_ids', 'in', [self.id])],
        }
