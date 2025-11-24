# -*- coding: utf-8 -*-
import logging
from werkzeug.urls import url_join

from odoo import models
from odoo.addons.payment_stripe.controllers.main import StripeController

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    def _get_stripe_webhook_url(self):
        """Override to use configured base URL instead of request-based URL"""
        # Get the configured public URL from web.base.url parameter
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        if not base_url:
            _logger.warning(
                "web.base.url parameter not set, falling back to default behavior"
            )
            return super()._get_stripe_webhook_url()

        webhook_url = url_join(base_url, StripeController._webhook_url)

        _logger.info("Using fixed webhook URL: %s", webhook_url)

        return webhook_url

    def get_base_url(self):
        """Override to always use web.base.url parameter in Kubernetes environments"""
        # First try to get the configured public URL
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        if base_url:
            return base_url

        # Fallback to default behavior
        return super().get_base_url()
