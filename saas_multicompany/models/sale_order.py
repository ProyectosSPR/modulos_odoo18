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

                # Create license tracking
                if product.multicompany_subscription_id:
                    self._create_company_license(company, product)

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
            'subscription_id': product.multicompany_subscription_id.id if product.multicompany_subscription_id else False,
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

        # Build message
        message = _('🏢 Company created: <b>%s</b>') % company.name

        if product.multicompany_subscription_id:
            message += _('<br/>📋 Subscription: <b>%s</b>') % product.multicompany_subscription_id.name
            message += _('<br/>   • Max Users: %s') % product.multicompany_subscription_id.max_users
            message += _('<br/>   • Max Companies: 1 (this company)')
            message += _('<br/>   • Max Storage: %s GB') % product.multicompany_subscription_id.max_storage_gb

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
            # Create user
            user = self.env['res.users'].sudo().create({
                'name': self.partner_id.name,
                'login': self.partner_id.email,
                'email': self.partner_id.email,
                'partner_id': self.partner_id.id,
                'company_id': company.id,
                'company_ids': [(6, 0, [company.id])],
            })
            _logger.info(f"User created: {user.name} for company {company.name}")
            self.message_post(
                body=_('✅ User created: <b>%s</b>') % user.name
            )
        else:
            # Add company to existing user
            user.sudo().write({
                'company_ids': [(4, company.id)],
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

    def _create_company_license(self, company, product):
        """Create initial license record for the company"""
        self.ensure_one()

        if not product.multicompany_subscription_id:
            return False

        # Count current users in this company
        user_count = self.env['res.users'].search_count([
            ('company_ids', 'in', [company.id]),
            ('active', '=', True),
            ('share', '=', False),  # Only internal users
        ])

        # Create license record
        license_vals = {
            'company_id': company.id,
            'client_id': company.saas_client_id.id,
            'subscription_id': product.multicompany_subscription_id.id,
            'date': fields.Date.today(),
            'user_count': user_count,
            'company_count': 1,
            'storage_gb': 0.0,  # Initial
        }

        license = self.env['saas.license'].create(license_vals)

        _logger.info(f"License tracking started for company {company.name}")

        message = _('📋 License tracking started')
        if license.is_billable:
            message += _('<br/>⚠️ Usage already exceeds limits!')

        self.message_post(body=message)

        return license

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
