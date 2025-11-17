# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    has_saas_products = fields.Boolean(
        string='Has SaaS Products',
        compute='_compute_has_saas_products',
        store=True
    )

    saas_client_id = fields.Many2one(
        'saas.client',
        string='SaaS Client',
        compute='_compute_saas_client_id',
        store=True
    )

    @api.depends('order_line', 'order_line.product_id', 'order_line.product_id.is_saas_instance')
    def _compute_has_saas_products(self):
        for order in self:
            order.has_saas_products = any(
                line.product_id.product_tmpl_id.is_saas_instance
                for line in order.order_line
            )

    @api.depends('partner_id')
    def _compute_saas_client_id(self):
        for order in self:
            saas_client = self.env['saas.client'].search([
                ('partner_id', '=', order.partner_id.id)
            ], limit=1)
            order.saas_client_id = saas_client.id if saas_client else False

    def action_confirm(self):
        """Override to create SaaS instances"""
        res = super(SaleOrder, self).action_confirm()

        for order in self:
            if order.has_saas_products:
                # Create or get SaaS client
                saas_client = order._get_or_create_saas_client()

                # Process SaaS products
                order._process_saas_products(saas_client)

        return res

    def _get_or_create_saas_client(self):
        """Get existing or create new SaaS client"""
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

    def _process_saas_products(self, saas_client):
        """Process SaaS products and create instances if needed"""
        self.ensure_one()

        for line in self.order_line:
            product = line.product_id.product_tmpl_id

            if product.is_saas_instance and product.auto_create_instance:
                # Create instance
                instance = self._create_saas_instance(saas_client, product)

                self.message_post(
                    body=_('🖥️ SaaS Instance created: <b>%s</b> (%s)') % (
                        instance.name,
                        instance.full_url
                    )
                )

    def _create_saas_instance(self, saas_client, product):
        """Create a SaaS instance"""
        self.ensure_one()

        # Generate unique subdomain
        base_subdomain = saas_client.partner_id.name.lower().replace(' ', '-')
        subdomain = base_subdomain
        counter = 1

        while self.env['saas.instance'].search([('subdomain', '=', subdomain)]):
            subdomain = f"{base_subdomain}-{counter}"
            counter += 1

        # Create instance
        instance = self.env['saas.instance'].create({
            'name': f"{saas_client.name} - {product.name}",
            'subdomain': subdomain,
            'client_id': saas_client.id,
            'state': 'trial',
            'trial_end_date': fields.Date.today() + fields.timedelta(days=product.trial_days or 7),
        })

        return instance
