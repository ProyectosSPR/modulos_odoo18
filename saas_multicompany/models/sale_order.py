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

                # Get or create company for this client
                company = self._get_or_create_saas_company(saas_client, product)

                # Assign user to company (only if company was created or user not assigned)
                user = self._assign_user_to_company(company, product)

                # Create licenses if product requires them (one per quantity)
                if product.requires_license:
                    self._create_licenses(company, saas_client, product, line)

    def _get_or_create_saas_company(self, saas_client, product):
        """Get existing or create a company for the SaaS client"""
        self.ensure_one()

        # First, check if company already exists for this client
        existing_company = self.env['res.company'].search([
            ('saas_client_id', '=', saas_client.id),
            ('is_saas_company', '=', True)
        ], limit=1)

        if existing_company:
            _logger.info(f"Using existing company: {existing_company.name} for client {saas_client.name}")
            return existing_company

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
            # Create user - Assign new company as primary, keep main company (id=1) as secondary
            # This allows user to see orders created in main company (e.g., from ecommerce)
            user = self.env['res.users'].sudo().create({
                'name': self.partner_id.name,
                'login': self.partner_id.email,
                'email': self.partner_id.email,
                'partner_id': self.partner_id.id,
                'company_id': company.id,
                'company_ids': [(6, 0, [company.id, 1])],  # New company + main company
            })
            _logger.info(f"User created: {user.name} for company {company.name}")
            self.message_post(
                body=_('✅ User created: <b>%s</b>') % user.name
            )
        else:
            # Add new company as primary, keep main company (id=1) as secondary

            # Ensure main company (id=1) and new company are both present
            company_ids_to_assign = [company.id]
            if 1 not in company_ids_to_assign:
                company_ids_to_assign.append(1)

            # Update user: new company as primary, main as secondary
            user.sudo().write({
                'company_ids': [(6, 0, company_ids_to_assign)],
                'company_id': company.id,  # Set new company as default
            })

            _logger.info(f"User {user.name} assigned to company {company.name}, main company kept as secondary")

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
            # Remove portal and public groups to convert user to Internal User
            portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
            public_group = self.env.ref('base.group_public', raise_if_not_found=False)

            groups_to_remove = []
            if portal_group and portal_group in user.groups_id:
                groups_to_remove.append((3, portal_group.id))
            if public_group and public_group in user.groups_id:
                groups_to_remove.append((3, public_group.id))

            # Add internal user group explicitly
            internal_user_group = self.env.ref('base.group_user', raise_if_not_found=False)

            # Prepare write operations: remove portal/public, add internal + requested groups
            write_vals = {
                'groups_id': groups_to_remove +
                             ([(4, internal_user_group.id)] if internal_user_group else []) +
                             [(4, group.id) for group in groups],
            }

            user.sudo().write(write_vals)
            _logger.info(f"User {user.name} converted to Internal User. Groups applied: {groups.mapped('name')}")

    def _create_licenses(self, company, saas_client, product, order_line):
        """Create license records and users based on product quantity"""
        self.ensure_one()

        quantity = int(order_line.product_uom_qty)

        if quantity <= 0:
            return

        # Get subscription from company if available
        subscription = company.subscription_id if company.subscription_id else False

        # Get the buyer/owner user to use as template
        owner_user = self.env['res.users'].search([
            ('partner_id', '=', self.partner_id.id)
        ], limit=1)

        if not owner_user:
            _logger.warning(f"Owner user not found for partner {self.partner_id.name}")
            return

        # Count existing internal users for this company (not portal, not admins of other companies)
        existing_company_users = self.env['res.users'].search([
            ('company_id', '=', company.id),  # Main company is this one
            ('active', '=', True),
            ('share', '=', False),  # Only internal users
        ])

        # Count existing licenses to know how many users we should have
        existing_licenses = self.env['saas.license'].search_count([
            ('company_id', '=', company.id),
        ])

        # Total licenses after this purchase
        total_licenses_after = existing_licenses + quantity

        # Total users we need (1 user per license)
        users_needed = total_licenses_after - len(existing_company_users)

        # Create licenses and users
        licenses_created = 0
        users_created = 0

        for i in range(quantity):
            # Create license
            license_vals = {
                'company_id': company.id,
                'client_id': saas_client.id,
                'subscription_id': subscription.id if subscription else False,
                'date': fields.Date.today(),
                'user_count': 1,
                'company_count': 1,
                'storage_gb': 0.0,
            }

            license = self.env['saas.license'].sudo().create(license_vals)
            licenses_created += 1
            _logger.info(f"License {i+1}/{quantity} created for company {company.name}: {license.name}")

        # Create users for licenses that don't have one yet
        for i in range(users_needed):
            user_number = len(existing_company_users) + i + 1
            new_user = self._create_license_user(company, saas_client, product, owner_user, user_number)
            if new_user:
                users_created += 1

        # Post message to sale order
        message = _('📜 Created <b>%s</b> license(s) and <b>%s</b> user(s) for company <b>%s</b>') % (
            licenses_created,
            users_created,
            company.name
        )
        self.message_post(body=message)

        return licenses_created

    def _create_license_user(self, company, saas_client, product, template_user, user_number):
        """Create a new user for a license, copying configuration from template user"""
        self.ensure_one()

        # Generate unique username based on company and number
        base_login = f"{company.name.lower().replace(' ', '_')}_user{user_number}"
        login = base_login
        counter = 1

        while self.env['res.users'].search([('login', '=', login)]):
            login = f"{base_login}_{counter}"
            counter += 1

        # Create partner for the new user
        partner_vals = {
            'name': f"{saas_client.name} - Usuario {user_number}",
            'email': f"{login}@{company.name.lower().replace(' ', '')}.local",
            'company_id': company.id,
        }

        partner = self.env['res.partner'].sudo().create(partner_vals)

        # Create user with same groups as template
        user_vals = {
            'name': f"{saas_client.name} - Usuario {user_number}",
            'login': login,
            'email': partner.email,
            'partner_id': partner.id,
            'company_id': company.id,
            'company_ids': [(6, 0, [company.id])],
            'groups_id': [(6, 0, template_user.groups_id.ids)],  # Copy all groups from template
        }

        try:
            user = self.env['res.users'].sudo().create(user_vals)
            _logger.info(f"License user created: {user.name} (login: {login}) for company {company.name}")

            self.message_post(
                body=_('👤 User <b>%s</b> created (Login: <b>%s</b>)') % (user.name, login)
            )

            return user
        except Exception as e:
            _logger.error(f"Failed to create license user: {str(e)}")
            return False

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
