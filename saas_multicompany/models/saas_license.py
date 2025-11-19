# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaasLicense(models.Model):
    _inherit = 'saas.license'

    # Override instance_id to make it not required when using company_id
    instance_id = fields.Many2one(required=False)

    # Support for both instance and local company
    company_id = fields.Many2one(
        'res.company',
        string='Local Company',
        help='For local multi-company licensing',
        ondelete='cascade'
    )

    # Override client_id to allow direct assignment (not just related field)
    client_id = fields.Many2one(
        'saas.client',
        string='Client',
        store=True,
        compute='_compute_client_id',
        readonly=False
    )

    # Override subscription_id to allow direct assignment
    subscription_id = fields.Many2one(
        'subscription.package',
        string='Subscription',
        store=True,
        compute='_compute_subscription_id',
        readonly=False
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

    @api.depends('instance_id', 'company_id')
    def _compute_client_id(self):
        """Compute client from instance or company"""
        for record in self:
            if not record.client_id:  # Only compute if not manually set
                if record.instance_id and record.instance_id.client_id:
                    record.client_id = record.instance_id.client_id
                elif record.company_id and record.company_id.saas_client_id:
                    record.client_id = record.company_id.saas_client_id

    @api.depends('instance_id', 'company_id')
    def _compute_subscription_id(self):
        """Compute subscription from instance or company"""
        for record in self:
            if not record.subscription_id:  # Only compute if not manually set
                if record.instance_id and record.instance_id.subscription_id:
                    record.subscription_id = record.instance_id.subscription_id
                elif record.company_id and record.company_id.subscription_id:
                    record.subscription_id = record.company_id.subscription_id

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
