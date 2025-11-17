# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # SaaS Integration
    is_saas_order = fields.Boolean(
        string='Is SaaS Order',
        compute='_compute_is_saas_order',
        store=True
    )
    saas_customer_id = fields.Many2one(
        'saas.customer',
        string='SaaS Customer',
        compute='_compute_saas_customer_id',
        store=True
    )
    saas_instance_count = fields.Integer(
        string='SaaS Instances',
        compute='_compute_saas_instance_count'
    )
    saas_instance_ids = fields.One2many(
        'saas.instance',
        compute='_compute_saas_instances',
        string='SaaS Instances'
    )

    @api.depends('order_line', 'order_line.product_id', 'order_line.product_id.is_saas_product')
    def _compute_is_saas_order(self):
        for order in self:
            order.is_saas_order = any(
                line.product_id.is_saas_product for line in order.order_line
            )

    @api.depends('partner_id')
    def _compute_saas_customer_id(self):
        for order in self:
            saas_customer = self.env['saas.customer'].search([
                ('partner_id', '=', order.partner_id.id)
            ], limit=1)
            order.saas_customer_id = saas_customer.id if saas_customer else False

    def _compute_saas_instances(self):
        """Compute SaaS instances related to this order"""
        for order in self:
            # Find instances created from this customer
            if order.saas_customer_id:
                instances = self.env['saas.instance'].search([
                    ('customer_id', '=', order.saas_customer_id.id)
                ])
                order.saas_instance_ids = instances
            else:
                order.saas_instance_ids = False

    @api.depends('saas_instance_ids')
    def _compute_saas_instance_count(self):
        """Count SaaS instances"""
        for order in self:
            order.saas_instance_count = len(order.saas_instance_ids)

    def action_confirm(self):
        """Override to create SaaS customers and instances"""
        res = super(SaleOrder, self).action_confirm()

        for order in self:
            if order.is_saas_order:
                # Create or get SaaS customer
                saas_customer = order._get_or_create_saas_customer()

                # Process SaaS products
                order._process_saas_products(saas_customer)

        return res

    def _get_or_create_saas_customer(self):
        """Get existing or create new SaaS customer"""
        self.ensure_one()

        # Search for existing customer
        saas_customer = self.env['saas.customer'].search([
            ('partner_id', '=', self.partner_id.id)
        ], limit=1)

        if not saas_customer:
            # Create new SaaS customer
            saas_customer = self.env['saas.customer'].create({
                'name': self.partner_id.name,
                'partner_id': self.partner_id.id,
                'company_name': self.partner_id.commercial_company_name or self.partner_id.name,
                'tax_code': self.partner_id.vat or '',
                'email': self.partner_id.email or '',
                'phone': self.partner_id.phone or '',
                'contact_name': self.partner_id.name,
                'contact_email': self.partner_id.email or '',
                'contact_phone': self.partner_id.phone or '',
                'address': self.partner_id.contact_address or '',
                'state': 'active',
            })
            self.message_post(
                body=_('SaaS Customer created: %s') % saas_customer.name
            )

        return saas_customer

    def _process_saas_products(self, saas_customer):
        """Process SaaS products and create instances/assign permissions if needed"""
        self.ensure_one()

        for line in self.order_line:
            product = line.product_id.product_tmpl_id

            if not product.is_saas_product:
                continue

            # Process based on provisioning policy
            if product.saas_creation_policy == 'create_instance' and product.create_instance:
                # Create instance
                instance_vals = self._prepare_instance_vals(line, saas_customer)
                instance = self.env['saas.instance'].create(instance_vals)

                self.message_post(
                    body=_('SaaS Instance created: %s (%s)') % (instance.name, instance.full_url)
                )

            elif product.saas_creation_policy == 'create_user':
                # Assign permissions to user
                self._assign_product_permissions(product, saas_customer)

    def _assign_product_permissions(self, product, saas_customer):
        """Assign permissions from product to customer's user"""
        self.ensure_one()

        # Get or create user for partner
        partner = saas_customer.partner_id
        user = partner.user_ids.filtered(lambda u: u.active)[:1]

        if not user:
            # Create user if doesn't exist
            user = self.env['res.users'].sudo().create({
                'name': partner.name,
                'login': partner.email or f'{partner.name.lower().replace(" ", ".")}@example.com',
                'partner_id': partner.id,
                'company_id': self.company_id.id,
                'company_ids': [(6, 0, [self.company_id.id])],
            })
            self.message_post(
                body=_('User created for partner: %s (Login: %s)') % (user.name, user.login)
            )

        # Get groups to assign (from product)
        groups_to_assign = product.access_group_ids

        if groups_to_assign:
            # ADDITIVE assignment - preserve existing groups
            existing_groups = user.groups_id
            all_groups = existing_groups | groups_to_assign

            user.sudo().write({
                'groups_id': [(6, 0, all_groups.ids)],
            })

            self.message_post(
                body=_('Permissions assigned to user %s:<br/>Groups: %s<br/>Modules: %s') % (
                    user.name,
                    ', '.join(groups_to_assign.mapped('name')),
                    ', '.join(product.module_access_ids.mapped('name')) if product.module_access_ids else 'All'
                )
            )

    def _prepare_instance_vals(self, order_line, saas_customer):
        """Prepare values for instance creation"""
        self.ensure_one()
        product = order_line.product_id.product_tmpl_id

        # Generate subdomain from customer name
        base_subdomain = saas_customer.partner_id.name.lower().replace(' ', '-')
        subdomain = base_subdomain

        # Ensure unique subdomain
        counter = 1
        while self.env['saas.instance'].search([('subdomain', '=', subdomain)]):
            subdomain = f"{base_subdomain}-{counter}"
            counter += 1

        vals = {
            'name': f"{saas_customer.name} - {product.name}",
            'subdomain': subdomain,
            'customer_id': saas_customer.id,
            'service_package_id': product.saas_package_id.id if product.saas_package_id else False,
            'odoo_version': product.default_odoo_version or '18.0',
            'status': 'trial',
            'billing_cycle': 'monthly',
        }

        return vals

    def action_view_saas_instances(self):
        """View SaaS instances created from this order"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('SaaS Instances'),
            'res_model': 'saas.instance',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.saas_instance_ids.ids)],
            'context': {'default_customer_id': self.saas_customer_id.id},
        }

    def action_view_saas_customer(self):
        """View SaaS customer record"""
        self.ensure_one()
        if not self.saas_customer_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('SaaS Customer'),
            'res_model': 'saas.customer',
            'view_mode': 'form',
            'res_id': self.saas_customer_id.id,
        }
