# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LicenseAddCompanyWizard(models.TransientModel):
    _name = 'license.add.company.wizard'
    _description = 'Add Company to License Wizard'

    license_id = fields.Many2one('saas.license', string='License', required=True, readonly=True)
    current_companies = fields.Integer(related='license_id.current_companies', string='Current Companies', readonly=True)
    max_companies = fields.Integer(related='license_id.max_companies', string='Max Companies', readonly=True)
    company_id = fields.Many2one('res.company', string='Company to Add', required=True,
                                 domain="[('is_licensed','=',False)]")
    monthly_price = fields.Monetary(string='Monthly Price', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='license_id.currency_id')

    def action_add_company(self):
        """Add company to license"""
        self.ensure_one()

        # Check limit
        if self.license_id.current_companies >= self.license_id.max_companies:
            raise UserError(
                _('Cannot add company. License limit reached (%s / %s)') %
                (self.license_id.current_companies, self.license_id.max_companies)
            )

        # Create licensed company
        self.env['saas.licensed.company'].create({
            'license_id': self.license_id.id,
            'company_id': self.company_id.id,
            'is_active': True,
            'monthly_price': self.monthly_price,
        })

        # Mark company as licensed
        self.company_id.is_licensed = True

        # Update subscription pricing
        self.license_id.update_subscription_pricing()

        # Post message
        self.license_id.message_post(
            body=_('Company %s added to license') % self.company_id.name
        )

        return {'type': 'ir.actions.act_window_close'}
