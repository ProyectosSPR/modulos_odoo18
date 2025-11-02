# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaasLicensedCompany(models.Model):
    _name = 'saas.licensed.company'
    _description = 'Licensed Company'
    _order = 'date_added desc'

    # License & Company
    license_id = fields.Many2one('saas.license', string='License', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True)

    # Customer Info
    customer_id = fields.Many2one('saas.customer', related='license_id.customer_id', string='Customer', store=True)

    # Status
    is_active = fields.Boolean(string='Active', default=True)
    date_added = fields.Datetime(string='Date Added', default=fields.Datetime.now, readonly=True)
    date_deactivated = fields.Datetime(string='Date Deactivated', readonly=True)

    # Usage Tracking
    users_count = fields.Integer(string='Active Users', compute='_compute_users_count', store=True)
    storage_used = fields.Float(string='Storage Used (GB)', default=0.0)

    # Pricing (if individual pricing per company)
    monthly_price = fields.Monetary(string='Monthly Price', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='license_id.currency_id')

    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('license_company_unique', 'UNIQUE(license_id, company_id)',
         'A company can only be licensed once per license!'),
    ]

    @api.depends('company_id', 'is_active')
    def _compute_users_count(self):
        for rec in self:
            if rec.company_id and rec.is_active:
                rec.users_count = self.env['res.users'].search_count([
                    ('company_ids', 'in', [rec.company_id.id]),
                    ('active', '=', True),
                ])
            else:
                rec.users_count = 0

    def action_deactivate(self):
        """Deactivate licensed company"""
        for rec in self:
            rec.write({
                'is_active': False,
                'date_deactivated': fields.Datetime.now()
            })
            rec.license_id.message_post(
                body=_('Company %s deactivated from license') % rec.company_id.name
            )

    def action_activate(self):
        """Reactivate licensed company"""
        for rec in self:
            # Check license limit
            if rec.license_id.current_companies >= rec.license_id.max_companies:
                from odoo.exceptions import UserError
                raise UserError(
                    _('Cannot activate company. License limit reached (%s / %s)') %
                    (rec.license_id.current_companies, rec.license_id.max_companies)
                )

            rec.is_active = True
            rec.license_id.message_post(
                body=_('Company %s activated in license') % rec.company_id.name
            )
