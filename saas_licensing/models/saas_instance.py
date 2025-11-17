# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaasInstance(models.Model):
    _inherit = 'saas.instance'

    # License tracking
    license_ids = fields.One2many(
        'saas.license',
        'instance_id',
        string='License Records'
    )
    license_count = fields.Integer(
        string='License Records',
        compute='_compute_license_count'
    )

    # Current Usage (extended from base)
    company_count = fields.Integer(
        string='Company Count',
        default=1,
        help='Number of companies in this instance'
    )

    # Latest metrics
    latest_license_id = fields.Many2one(
        'saas.license',
        string='Latest License',
        compute='_compute_latest_license'
    )
    has_overages = fields.Boolean(
        string='Has Overages',
        compute='_compute_has_overages'
    )

    @api.depends('license_ids')
    def _compute_license_count(self):
        for record in self:
            record.license_count = len(record.license_ids)

    @api.depends('license_ids', 'license_ids.date')
    def _compute_latest_license(self):
        for record in self:
            record.latest_license_id = record.license_ids.sorted('date', reverse=True)[:1]

    @api.depends('latest_license_id', 'latest_license_id.is_billable')
    def _compute_has_overages(self):
        for record in self:
            record.has_overages = record.latest_license_id.is_billable if record.latest_license_id else False

    def action_view_licenses(self):
        """View license records for this instance"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('License Records'),
            'res_model': 'saas.license',
            'view_mode': 'list,form',
            'domain': [('instance_id', '=', self.id)],
            'context': {
                'default_instance_id': self.id,
                'default_user_count': self.current_users,
                'default_company_count': self.company_count,
                'default_storage_gb': self.storage_used_gb,
            },
        }

    def action_create_license_snapshot(self):
        """Create a license snapshot for current usage"""
        self.ensure_one()

        license = self.env['saas.license'].create({
            'instance_id': self.id,
            'date': fields.Date.today(),
            'user_count': self.current_users,
            'company_count': self.company_count,
            'storage_gb': self.storage_used_gb,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('License Snapshot'),
            'res_model': 'saas.license',
            'res_id': license.id,
            'view_mode': 'form',
            'target': 'current',
        }
