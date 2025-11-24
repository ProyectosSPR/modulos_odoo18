# -*- coding: utf-8 -*-
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _set_done(self, state_message=None, extra_allowed_states=()):
        """Override to auto-start subscriptions when payment is marked as done"""
        _logger.info("=== PAYMENT AUTO-START: _set_done called for transaction(s): %s ===", self.mapped('reference'))

        # Call parent to update state to done
        res = super()._set_done(state_message=state_message, extra_allowed_states=extra_allowed_states)

        # Auto-start subscriptions for transactions that were successfully set to done
        for tx in res:
            _logger.info(
                "Payment transaction %s - state: %s, has sale_order_ids: %s",
                tx.reference, tx.state, bool(tx.sale_order_ids)
            )
            if tx.state == 'done' and tx.sale_order_ids:
                _logger.info(
                    "Payment transaction %s is done with sale orders: %s",
                    tx.reference, tx.sale_order_ids.mapped('name')
                )
                tx._auto_start_subscriptions()

        return res

    def _auto_start_subscriptions(self):
        """Automatically start subscriptions associated with paid sale orders"""
        self.ensure_one()

        _logger.info(
            "=== Searching for subscriptions linked to sale orders: %s ===",
            self.sale_order_ids.ids
        )

        # Find subscriptions linked to this transaction's sale orders
        subscriptions = self.env['subscription.package'].search([
            ('sale_order_id', 'in', self.sale_order_ids.ids),
            ('stage_category', '=', 'draft'),
        ])

        _logger.info(
            "Found %s draft subscriptions for transaction %s",
            len(subscriptions), self.reference
        )

        if not subscriptions:
            _logger.warning(
                "No draft subscriptions found for transaction %s (sale orders: %s)",
                self.reference, self.sale_order_ids.mapped('name')
            )
            # Also check if there are ANY subscriptions linked (not just draft)
            all_subscriptions = self.env['subscription.package'].search([
                ('sale_order_id', 'in', self.sale_order_ids.ids)
            ])
            _logger.info(
                "Total subscriptions found for these sale orders: %s (states: %s)",
                len(all_subscriptions), all_subscriptions.mapped('stage_category')
            )
            return

        for subscription in subscriptions:
            try:
                _logger.info(
                    "Auto-starting subscription %s (ID: %s) for paid transaction %s",
                    subscription.name, subscription.id, self.reference
                )

                # Call the start button method
                subscription.button_start_date()

                subscription.message_post(
                    body=f"Subscription automatically started after payment confirmation (Transaction: {self.reference})"
                )

                _logger.info(
                    "Successfully auto-started subscription %s", subscription.name
                )

            except Exception as e:
                _logger.error(
                    "Failed to auto-start subscription %s: %s",
                    subscription.name, str(e), exc_info=True
                )
                # Don't raise - we don't want to block the payment flow
                subscription.message_post(
                    body=f"Warning: Failed to automatically start subscription: {str(e)}"
                )
