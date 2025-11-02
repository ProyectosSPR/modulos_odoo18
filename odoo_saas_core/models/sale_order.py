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
    # Note: instance_count will be added by odoo_subscription module
    # when it extends sale.order with subscription_id field

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
        """Process SaaS products and create instances if needed"""
        self.ensure_one()

        for line in self.order_line:
            product = line.product_id.product_tmpl_id

            if product.is_saas_product and product.create_instance:
                # Create instance
                instance_vals = self._prepare_instance_vals(line, saas_customer)
                instance = self.env['saas.instance'].create(instance_vals)

                self.message_post(
                    body=_('SaaS Instance created: %s (%s)') % (instance.name, instance.full_url)
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
