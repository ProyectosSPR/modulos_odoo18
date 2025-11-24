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

    def _stripe_get_or_create_price(self, provider_id, unit_price, currency_id, plan_id=None, recurrence_period=None):
        """Get or create a price in Stripe for this product

        :param provider_id: payment.provider record for Stripe
        :param unit_price: Price amount
        :param currency_id: res.currency record
        :param plan_id: subscription.package.plan record (optional, for recurring interval from plan)
        :param recurrence_period: recurrence.period record (optional, overrides plan interval)
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

        # Determine recurring interval
        # Priority: recurrence_period (from subscription) > plan.renewal_period
        interval = None

        if recurrence_period:
            # Use recurrence_period from subscription (if provided)
            interval = self._stripe_get_interval_from_recurrence_period(recurrence_period)
        elif plan_id:
            # Fallback to plan's renewal settings
            interval = self._stripe_get_interval_from_plan(plan_id)

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
            "Created Stripe price %s for product %s with amount %s %s (interval: %s)",
            stripe_price_id, self.name, unit_price, currency_id.name,
            interval if interval else 'one-time'
        )

        return stripe_price_id

    def _stripe_get_interval_from_plan(self, plan):
        """Convert Odoo subscription plan to Stripe interval

        :param plan: subscription.package.plan record
        :return: dict with 'interval' and optional 'interval_count'
        """
        # Map subscription plan renewal_period to Stripe intervals
        # Stripe supports: day, week, month, year

        if not plan or not plan.renewal_period:
            _logger.warning("No renewal period found in plan, defaulting to month")
            return {'interval': 'month', 'interval_count': 1}

        renewal_period = plan.renewal_period
        renewal_value = int(plan.renewal_value) if plan.renewal_value else 1

        # Ensure renewal_value is at least 1
        if renewal_value < 1:
            renewal_value = 1

        # Map plan's renewal_period to Stripe intervals
        interval_mapping = {
            'days': 'day',
            'weeks': 'week',
            'months': 'month',
            'years': 'year',
        }

        stripe_interval = interval_mapping.get(renewal_period)

        if not stripe_interval:
            _logger.warning(
                "Could not map renewal period '%s' to Stripe interval, defaulting to month",
                renewal_period
            )
            return {'interval': 'month', 'interval_count': 1}

        _logger.info(
            "Mapped plan renewal period '%s' (value: %s) to Stripe interval '%s' with count %s",
            renewal_period, renewal_value, stripe_interval, renewal_value
        )

        return {'interval': stripe_interval, 'interval_count': renewal_value}

    def _stripe_get_interval_from_recurrence_period(self, recurrence_period):
        """Convert recurrence.period record to Stripe interval

        :param recurrence_period: recurrence.period record
        :return: dict with 'interval' and optional 'interval_count'
        """
        if not recurrence_period:
            return None

        # Map recurrence_period.unit to Stripe intervals
        unit = recurrence_period.unit
        duration = int(recurrence_period.duration) if recurrence_period.duration else 1

        # Ensure duration is at least 1
        if duration < 1:
            duration = 1

        interval_mapping = {
            'hours': None,  # Stripe doesn't support hourly subscriptions
            'days': 'day',
            'weeks': 'week',
            'months': 'month',
            'years': 'year',
        }

        stripe_interval = interval_mapping.get(unit)

        if not stripe_interval:
            _logger.warning(
                "Cannot map recurrence period unit '%s' to Stripe interval (not supported)",
                unit
            )
            return None

        _logger.info(
            "Mapped recurrence period '%s' (unit: %s, duration: %s) to Stripe interval '%s' with count %s",
            recurrence_period.name, unit, duration, stripe_interval, duration
        )

        return {'interval': stripe_interval, 'interval_count': duration}

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
