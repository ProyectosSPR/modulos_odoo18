# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Licensing Fields
    is_licensed = fields.Boolean(string='Is Licensed', default=False)
    licensed_company_id = fields.Many2one(
        'saas.licensed.company',
        string='License Record',
        compute='_compute_licensed_company_id',
        store=True
    )
    license_id = fields.Many2one(
        'saas.license',
        related='licensed_company_id.license_id',
        string='License',
        store=True
    )
    license_customer_id = fields.Many2one(
        'saas.customer',
        related='licensed_company_id.customer_id',
        string='License Customer'
    )

    @api.depends('is_licensed')
    def _compute_licensed_company_id(self):
        for company in self:
            if company.is_licensed:
                licensed = self.env['saas.licensed.company'].search([
                    ('company_id', '=', company.id),
                    ('is_active', '=', True)
                ], limit=1)
                company.licensed_company_id = licensed.id if licensed else False
            else:
                company.licensed_company_id = False

    @api.model
    def create(self, vals):
        """Override to trigger license check when new company is created"""
        company = super(ResCompany, self).create(vals)

        # Check if current user has an active license
        user = self.env.user
        if user.partner_id:
            saas_customer = self.env['saas.customer'].search([
                ('partner_id', '=', user.partner_id.id)
            ], limit=1)

            if saas_customer:
                # Find active license
                active_license = self.env['saas.license'].search([
                    ('customer_id', '=', saas_customer.id),
                    ('state', '=', 'active')
                ], limit=1)

                if active_license:
                    # Check if we can add company
                    if active_license.current_companies < active_license.max_companies:
                        # Auto-add to license
                        self.env['saas.licensed.company'].create({
                            'license_id': active_license.id,
                            'company_id': company.id,
                            'is_active': True,
                        })
                        company.is_licensed = True

                        # Update subscription pricing
                        active_license.update_subscription_pricing()
                    else:
                        # Send alert - limit reached
                        active_license._send_usage_alert()

        return company
