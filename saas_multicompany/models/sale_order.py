# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    has_multicompany_products = fields.Boolean(
        string='Has Multi-Company Products',
        compute='_compute_has_multicompany_products',
        store=True
    )

    @api.depends('order_line', 'order_line.product_id', 'order_line.product_id.is_module_access')
    def _compute_has_multicompany_products(self):
        for order in self:
            order.has_multicompany_products = any(
                line.product_id.product_tmpl_id.is_module_access
                for line in order.order_line
            )

    def action_confirm(self):
        """Override to create companies for multi-company products"""
        res = super(SaleOrder, self).action_confirm()

        for order in self:
            if order.has_multicompany_products:
                order._process_multicompany_products()

        return res

    def _process_multicompany_products(self):
        """Process multi-company products and create companies"""
        self.ensure_one()

        for line in self.order_line:
            product = line.product_id.product_tmpl_id

            if product.is_module_access and product.auto_create_company:
                # Get or create SaaS client
                saas_client = self._get_or_create_saas_client()

                # Create company for this client
                company = self._create_saas_company(saas_client, product)

                # Assign user to company
                user = self._assign_user_to_company(company, product)

    def _create_saas_company(self, saas_client, product):
        """Create a company for the SaaS client"""
        self.ensure_one()

        # Generate unique company name
        base_name = saas_client.name
        company_name = base_name
        counter = 1

        while self.env['res.company'].search([('name', '=', company_name)]):
            company_name = f"{base_name} ({counter})"
            counter += 1

        # Prepare company values
        company_vals = {
            'name': company_name,
            'partner_id': self.partner_id.id,
            'saas_client_id': saas_client.id,
            'is_saas_company': True,
            # Note: subscription_id can be assigned later manually in the company
        }

        # Copy from template if provided
        if product.company_template_id:
            template = product.company_template_id
            company_vals.update({
                'currency_id': template.currency_id.id,
                'country_id': template.country_id.id,
                'email': template.email,
                'phone': template.phone,
                'website': template.website,
                'vat': self.partner_id.vat or template.vat,
            })

        # Create company
        company = self.env['res.company'].sudo().create(company_vals)

        _logger.info(f"SaaS Company created: {company.name} for client {saas_client.name}")

        # Assign company to all administrators
        self._assign_company_to_admins(company)

        # Build message
        message = _('🏢 Company created: <b>%s</b><br/>') % company.name
        message += _('ℹ️ Assign a subscription package to the company to enable license tracking')

        self.message_post(body=message)

        return company

    def _assign_user_to_company(self, company, product):
        """Assign user to company with permissions"""
        self.ensure_one()

        # Get or create user for partner
        user = self.env['res.users'].search([
            ('partner_id', '=', self.partner_id.id)
        ], limit=1)

        if not user:
            # Create user - ONLY assign the new company, NOT the main company (id=1)
            user = self.env['res.users'].sudo().create({
                'name': self.partner_id.name,
                'login': self.partner_id.email,
                'email': self.partner_id.email,
                'partner_id': self.partner_id.id,
                'company_id': company.id,
                'company_ids': [(6, 0, [company.id])],  # Only new company, not main company
            })
            _logger.info(f"User created: {user.name} for company {company.name}")
            self.message_post(
                body=_('✅ User created: <b>%s</b>') % user.name
            )
        else:
            # Remove main company (id=1) if present and add only the new company
            current_companies = user.company_ids.ids

            # Remove main company (id=1) from the list
            if 1 in current_companies:
                current_companies.remove(1)

            # Add the new company
            if company.id not in current_companies:
                current_companies.append(company.id)

            user.sudo().write({
                'company_ids': [(6, 0, current_companies)],
            })

            # If restrict_to_company, set as default
            if product.restrict_to_company:
                user.sudo().write({
                    'company_id': company.id,
                })

            _logger.info(f"User {user.name} assigned to company {company.name}")

        # Assign permissions if configured
        if product.assign_permissions and product.permission_group_ids:
            self._apply_groups_to_user(user, product.permission_group_ids)

        message = _('👤 User <b>%s</b> assigned to company <b>%s</b>') % (
            user.name,
            company.name
        )

        if product.restrict_to_company:
            message += _('<br/>🔒 Access restricted to this company only')

        self.message_post(body=message)

        return user

    def _assign_company_to_admins(self, company):
        """Assign newly created company to all administrator users"""
        self.ensure_one()

        # Get all users with Administrator / Settings group
        admin_group = self.env.ref('base.group_system', raise_if_not_found=False)

        if admin_group:
            admin_users = self.env['res.users'].sudo().search([
                ('groups_id', 'in', [admin_group.id]),
                ('active', '=', True),
            ])

            assigned_count = 0
            for admin in admin_users:
                # Add company to admin's company_ids if not already present
                if company.id not in admin.company_ids.ids:
                    admin.write({
                        'company_ids': [(4, company.id)],
                    })
                    assigned_count += 1
                    _logger.info(f"Company {company.name} assigned to admin {admin.name}")

            if assigned_count > 0:
                self.message_post(
                    body=_('✅ Company assigned to <b>%s</b> administrator(s)') % assigned_count
                )

    def _apply_groups_to_user(self, user, groups):
        """Apply security groups to user"""
        self.ensure_one()

        if groups:
            user.sudo().write({
                'groups_id': [(4, group.id) for group in groups],
            })
            _logger.info(f"Groups applied to user {user.name}: {groups.mapped('name')}")

    def _get_or_create_saas_client(self):
        """Get existing or create new SaaS client (reuse from saas_management)"""
        self.ensure_one()

        # Search for existing client
        saas_client = self.env['saas.client'].search([
            ('partner_id', '=', self.partner_id.id)
        ], limit=1)

        if not saas_client:
            # Create new SaaS client
            saas_client = self.env['saas.client'].create({
                'name': self.partner_id.name,
                'partner_id': self.partner_id.id,
                'state': 'active',
                'activated_date': fields.Date.today(),
            })
            self.message_post(
                body=_('✅ SaaS Client created: %s') % saas_client.name
            )

        return saas_client
