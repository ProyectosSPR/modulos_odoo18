# -*- coding: utf-8 -*-
import logging
from werkzeug.urls import url_encode, url_join

from odoo import models
from odoo.addons.payment_stripe.controllers.main import StripeController

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_processing_values(self, processing_values):
        """Override to force correct public URL in Kubernetes"""
        res = super()._get_specific_processing_values(processing_values)

        if self.provider_code != 'stripe' or self.operation == 'online_token':
            return res

        # Get the configured public URL from web.base.url parameter
        # instead of relying on HTTP headers which may be internal in Kubernetes
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        if not base_url:
            _logger.warning(
                "web.base.url parameter not set, falling back to provider base URL"
            )
            base_url = self.provider_id.get_base_url()

        # Rebuild return_url with the correct base URL
        return_url = url_join(
            base_url,
            f'{StripeController._return_url}?{url_encode({"reference": self.reference})}',
        )

        # Update the return_url in processing values
        res['return_url'] = return_url

        _logger.info(
            "Fixed Stripe return URL for transaction %s: %s",
            self.reference, return_url
        )

        return res
