# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaasLicense(models.Model):
    _inherit = 'saas.license'

    # Support for both instance and local company
    company_id = fields.Many2one(
        'res.company',
        string='Local Company',
        help='For local multi-company licensing',
        ondelete='cascade'
    )

    license_type = fields.Selection([
        ('instance', 'SaaS Instance'),
        ('company', 'Local Company'),
    ], string='License Type', compute='_compute_license_type', store=True)

    @api.depends('instance_id', 'company_id')
    def _compute_license_type(self):
        for record in self:
            if record.instance_id:
                record.license_type = 'instance'
            elif record.company_id:
                record.license_type = 'company'
            else:
                record.license_type = False

    @api.depends('instance_id', 'company_id', 'date')
    def _compute_name(self):
        """Override to support both instance and company"""
        for record in self:
            if record.company_id:
                record.name = f"{record.company_id.name} - {record.date}"
            elif record.instance_id:
                record.name = f"{record.instance_id.name} - {record.date}"
            else:
                record.name = "New License Record"

    @api.model
    def create_monthly_license_records(self):
        """Extended to create records for both instances AND companies"""

        # Original: Track SaaS instances
        instances = self.env['saas.instance'].search([
            ('state', 'in', ['active', 'trial']),
            ('subscription_id', '!=', False)
        ])

        for instance in instances:
            # Check if record already exists
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

        # NEW: Track local SaaS companies
        companies = self.env['res.company'].search([
            ('is_saas_company', '=', True),
            ('subscription_id', '!=', False)
        ])

        for company in companies:
            # Check if record already exists
            existing = self.search([
                ('company_id', '=', company.id),
                ('date', '=', fields.Date.today())
            ])

            if not existing:
                # Count active internal users in this company
                user_count = self.env['res.users'].search_count([
                    ('company_ids', 'in', [company.id]),
                    ('active', '=', True),
                    ('share', '=', False),  # Only internal users
                ])

                # TODO: Calculate storage used by this company
                # This would require custom logic to track data size per company
                storage_gb = 0.0

                self.create({
                    'company_id': company.id,
                    'client_id': company.saas_client_id.id if company.saas_client_id else False,
                    'subscription_id': company.subscription_id.id,
                    'date': fields.Date.today(),
                    'user_count': user_count,
                    'company_count': 1,  # Local company counts as 1
                    'storage_gb': storage_gb,
                })

        return True
