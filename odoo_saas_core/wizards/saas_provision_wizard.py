# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaasProvisionWizard(models.TransientModel):
    _name = 'saas.provision.wizard'
    _description = 'SaaS Provisioning Wizard'

    instance_id = fields.Many2one(
        'saas.instance',
        string='Instance',
        required=True,
        readonly=True
    )
    customer_id = fields.Many2one(
        'saas.customer',
        related='instance_id.customer_id',
        string='Customer',
        readonly=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        related='instance_id.partner_id',
        string='Partner',
        readonly=True
    )
    service_package_id = fields.Many2one(
        'saas.service.package',
        related='instance_id.service_package_id',
        string='Service Package',
        readonly=True
    )

    # Provisioning Options
    create_company = fields.Boolean(
        string='Create Dedicated Company',
        default=True,
        help='Create a dedicated company for this SaaS instance'
    )
    company_name = fields.Char(
        string='Company Name',
        compute='_compute_company_name',
        store=True,
        readonly=False
    )
    assign_user_groups = fields.Boolean(
        string='Assign User Groups',
        default=True,
        help='Assign security groups from service package to user'
    )
    access_group_ids = fields.Many2many(
        'res.groups',
        related='service_package_id.access_group_ids',
        string='Groups to Assign',
        readonly=True
    )

    @api.depends('customer_id', 'customer_id.name')
    def _compute_company_name(self):
        for wizard in self:
            if wizard.customer_id:
                wizard.company_name = wizard.customer_id.name
            else:
                wizard.company_name = ''

    def action_provision(self):
        """Execute provisioning"""
        self.ensure_one()

        instance = self.instance_id
        partner = self.partner_id

        # Get or create user for partner
        user = partner.user_ids.filtered(lambda u: u.active)[:1]

        if not user:
            raise UserError(
                _('No active user found for partner %s. Please create a user first.') %
                partner.name
            )

        # Create company if requested
        company = False
        if self.create_company:
            company = self._create_company()
            instance.provisioned_company_id = company

        # Assign groups if requested
        if self.assign_user_groups and self.access_group_ids:
            self._assign_groups_to_user(user, company)

        # Mark as provisioned
        instance.is_provisioned = True

        # Post message
        instance.message_post(
            body=_('Access provisioned successfully.<br/>User: %s<br/>Company: %s<br/>Groups: %s') %
            (user.name, company.name if company else 'N/A', ', '.join(self.access_group_ids.mapped('name')))
        )

        return {'type': 'ir.actions.act_window_close'}

    def _create_company(self):
        """Create a dedicated company for the instance"""
        self.ensure_one()

        company = self.env['res.company'].sudo().create({
            'name': self.company_name,
            'partner_id': self.partner_id.id,
        })

        # Add admin user to company
        admin_user = self.env.ref('base.user_admin')
        if admin_user not in company.user_ids:
            company.sudo().write({
                'user_ids': [(4, admin_user.id)]
            })

        return company

    def _assign_groups_to_user(self, user, company=False):
        """Assign groups to user"""
        self.ensure_one()

        # Get internal user group
        internal_user_group = self.env.ref('base.group_user')

        # Combine groups
        groups_to_assign = self.access_group_ids | internal_user_group

        # Prepare user vals
        user_vals = {
            'groups_id': [(6, 0, groups_to_assign.ids)],
        }

        # Set company if provided
        if company:
            user_vals.update({
                'company_id': company.id,
                'company_ids': [(6, 0, [company.id])],
            })

        # Update user
        user.sudo().write(user_vals)
