# -*- coding: utf-8 -*-
import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _create_subscription_from_sale_order(self, order):
        """Helper method to create subscription from sale order if it doesn't exist

        This can be called from other modules to ensure a subscription exists
        before payment is processed.
        """
        # Check if subscription already exists
        existing_sub = self.env['subscription.package'].search([
            ('sale_order_id', '=', order.id)
        ], limit=1)

        if existing_sub:
            _logger.info(
                "Subscription %s already exists for sale order %s",
                existing_sub.name, order.name
            )
            return existing_sub

        # Check if order has subscription products
        has_subscription_products = any(
            line.product_id.product_tmpl_id.is_subscription
            for line in order.order_line
            if line.product_id
        )

        if not has_subscription_products:
            _logger.info(
                "Sale order %s has no subscription products", order.name
            )
            return self.env['subscription.package']

        # Create subscription
        # Note: This is a basic implementation - you may need to customize
        # based on how you want to map sale orders to subscriptions

        _logger.info(
            "Creating subscription package for sale order %s", order.name
        )

        # You would implement the actual subscription creation logic here
        # This is just a placeholder to show where it would go

        return self.env['subscription.package']
