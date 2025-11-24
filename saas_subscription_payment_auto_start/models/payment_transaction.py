# -*- coding: utf-8 -*-
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _reconcile_after_done(self):
        """Override to auto-start subscriptions after payment is done"""
        res = super()._reconcile_after_done()

        for tx in self:
            if tx.state == 'done' and tx.sale_order_ids:
                tx._auto_start_subscriptions()

        return res

    def _auto_start_subscriptions(self):
        """Automatically start subscriptions associated with paid sale orders"""
        self.ensure_one()

        # Find subscriptions linked to this transaction's sale orders
        subscriptions = self.env['subscription.package'].search([
            ('sale_order_id', 'in', self.sale_order_ids.ids),
            ('stage_category', '=', 'draft'),
        ])

        if not subscriptions:
            _logger.info(
                "No draft subscriptions found for transaction %s", self.reference
            )
            return

        for subscription in subscriptions:
            try:
                _logger.info(
                    "Auto-starting subscription %s for paid transaction %s",
                    subscription.name, self.reference
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
                    subscription.name, str(e)
                )
                # Don't raise - we don't want to block the payment flow
                subscription.message_post(
                    body=f"Warning: Failed to automatically start subscription: {str(e)}"
                )
