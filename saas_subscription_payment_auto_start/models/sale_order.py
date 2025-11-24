# -*- coding: utf-8 -*-
import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        """Override to auto-start subscriptions after they're created from paid orders"""
        _logger.info("=== SALE ORDER CONFIRMATION: _action_confirm called for order(s): %s ===", self.mapped('name'))

        # Call parent to create subscription packages
        res = super()._action_confirm()

        # Auto-start subscriptions if the order has been paid
        for order in self:
            _logger.info(
                "Order %s - State: %s, Transaction states: %s",
                order.name,
                order.state,
                order.transaction_ids.mapped('state') if order.transaction_ids else 'No transactions'
            )

            # Check if order has a completed payment transaction
            paid_transactions = order.transaction_ids.filtered(lambda tx: tx.state == 'done')

            if paid_transactions:
                _logger.info(
                    "Order %s has %d paid transaction(s): %s",
                    order.name, len(paid_transactions), paid_transactions.mapped('reference')
                )

                # Find subscriptions created for this order
                subscriptions = self.env['subscription.package'].search([
                    ('sale_order_id', '=', order.id),
                    ('stage_category', '=', 'draft')
                ])

                _logger.info(
                    "Found %d draft subscriptions for order %s: %s",
                    len(subscriptions), order.name, subscriptions.mapped('name')
                )

                for subscription in subscriptions:
                    try:
                        _logger.info(
                            "Auto-starting subscription %s (ID: %s) for paid order %s",
                            subscription.name, subscription.id, order.name
                        )

                        # Start the subscription - this will trigger Stripe subscription creation
                        subscription.button_start_date()

                        subscription.message_post(
                            body=f"Subscription automatically started after payment confirmation (Order: {order.name})"
                        )

                        _logger.info(
                            "Successfully auto-started subscription %s", subscription.name
                        )

                    except Exception as e:
                        _logger.error(
                            "Failed to auto-start subscription %s: %s",
                            subscription.name, str(e), exc_info=True
                        )
                        subscription.message_post(
                            body=f"Warning: Failed to automatically start subscription: {str(e)}"
                        )
            else:
                _logger.info(
                    "Order %s has no completed payment transactions, skipping auto-start",
                    order.name
                )

        return res
