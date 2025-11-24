# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    stripe_product_id = fields.Char(
        string='Stripe Product ID',
        readonly=True,
        copy=False,
        help='The ID of the product in Stripe'
    )
    stripe_auto_sync = fields.Boolean(
        string='Auto-sync with Stripe',
        default=False,
        help='Automatically create/update this product in Stripe when used in subscriptions'
    )

    def _stripe_get_or_create_product(self, provider_id):
        """Get or create a product in Stripe

        :param provider_id: payment.provider record for Stripe
        :return: Stripe product ID
        """
        self.ensure_one()

        # Return existing product if already synced
        if self.stripe_product_id:
            return self.stripe_product_id

        # Create new product in Stripe
        payload = {
            'name': self.name,
            'description': self.description_sale or self.name,
            'metadata[odoo_product_id]': str(self.id),
            'metadata[odoo_product_ref]': self.default_code or '',
        }

        response = provider_id._stripe_make_request(
            'products',
            payload=payload
        )

        stripe_product_id = response.get('id')

        # Store Stripe product ID
        self.write({'stripe_product_id': stripe_product_id})

        _logger.info(
            "Created Stripe product %s for Odoo product %s (%s)",
            stripe_product_id, self.id, self.name
        )

        return stripe_product_id

    def _stripe_get_or_create_price(self, provider_id, unit_price, currency_id, plan_id=None):
        """Get or create a price in Stripe for this product

        :param provider_id: payment.provider record for Stripe
        :param unit_price: Price amount
        :param currency_id: res.currency record
        :param plan_id: subscription.package.plan record (optional, for recurring interval)
        :return: Stripe price ID
        """
        self.ensure_one()

        # Get or create the product first
        stripe_product_id = self._stripe_get_or_create_product(provider_id)

        # Convert price to cents (Stripe uses smallest currency unit)
        unit_amount = int(unit_price * 100)

        # Prepare price payload
        payload = {
            'product': stripe_product_id,
            'unit_amount': unit_amount,
            'currency': currency_id.name.lower(),
            'metadata[odoo_product_id]': str(self.id),
        }

        # Add recurring interval if plan is provided
        if plan_id and plan_id.recurrence_period_id:
            interval = self._stripe_get_interval_from_period(plan_id.recurrence_period_id)
            if interval:
                payload['recurring[interval]'] = interval['interval']
                if interval.get('interval_count'):
                    payload['recurring[interval_count]'] = interval['interval_count']

        response = provider_id._stripe_make_request(
            'prices',
            payload=payload
        )

        stripe_price_id = response.get('id')

        _logger.info(
            "Created Stripe price %s for product %s with amount %s %s",
            stripe_price_id, self.name, unit_price, currency_id.name
        )

        return stripe_price_id

    def _stripe_get_interval_from_period(self, recurrence_period):
        """Convert Odoo recurrence period to Stripe interval

        :param recurrence_period: recurrence.period record
        :return: dict with 'interval' and optional 'interval_count'
        """
        # Map Odoo UOM to Stripe intervals
        # Stripe supports: day, week, month, year

        if not recurrence_period or not recurrence_period.period_uom:
            return None

        uom_name = recurrence_period.period_uom.name.lower()
        period_value = recurrence_period.period_value or 1

        # Map common periods
        if 'day' in uom_name or 'dia' in uom_name:
            return {'interval': 'day', 'interval_count': period_value}
        elif 'week' in uom_name or 'semana' in uom_name:
            return {'interval': 'week', 'interval_count': period_value}
        elif 'month' in uom_name or 'mes' in uom_name:
            return {'interval': 'month', 'interval_count': period_value}
        elif 'year' in uom_name or 'año' in uom_name or 'year' in uom_name:
            return {'interval': 'year', 'interval_count': period_value}
        else:
            # Default to month if can't determine
            _logger.warning(
                "Could not map recurrence period UOM '%s' to Stripe interval, defaulting to month",
                uom_name
            )
            return {'interval': 'month', 'interval_count': 1}

    def action_sync_to_stripe(self):
        """Manual action to sync product to Stripe"""
        self.ensure_one()

        # Get default Stripe provider
        provider = self.env['payment.provider'].search([
            ('code', '=', 'stripe'),
            ('state', 'in', ['enabled', 'test'])
        ], limit=1)

        if not provider:
            raise UserError(_("No active Stripe payment provider found."))

        # Create or update product in Stripe
        self._stripe_get_or_create_product(provider)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Product synced to Stripe successfully'),
                'type': 'success',
                'sticky': False,
            }
        }


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _stripe_get_or_create_product(self, provider_id):
        """Delegate to product template"""
        return self.product_tmpl_id._stripe_get_or_create_product(provider_id)

    def _stripe_get_or_create_price(self, provider_id, unit_price, currency_id, plan_id=None):
        """Delegate to product template"""
        return self.product_tmpl_id._stripe_get_or_create_price(
            provider_id, unit_price, currency_id, plan_id
        )
