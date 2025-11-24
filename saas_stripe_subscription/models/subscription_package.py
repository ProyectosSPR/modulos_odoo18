# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SubscriptionPackage(models.Model):
    _inherit = 'subscription.package'

    # Stripe Integration Fields
    stripe_subscription_id = fields.Char(
        string='Stripe Subscription ID',
        readonly=True,
        copy=False,
        help='The ID of the subscription in Stripe'
    )
    stripe_customer_id = fields.Char(
        string='Stripe Customer ID',
        readonly=True,
        copy=False,
        help='The ID of the customer in Stripe'
    )
    payment_provider_id = fields.Many2one(
        'payment.provider',
        string='Payment Provider',
        domain=[('code', '=', 'stripe')],
        help='The Stripe payment provider to use for this subscription'
    )
    stripe_sync_enabled = fields.Boolean(
        string='Sync with Stripe',
        default=True,
        help='Enable automatic synchronization with Stripe'
    )
    stripe_subscription_status = fields.Char(
        string='Stripe Status',
        readonly=True,
        help='Current status of the subscription in Stripe'
    )
    is_test_subscription = fields.Boolean(
        string='Test Subscription',
        compute='_compute_is_test_subscription',
        store=True,
        help='Whether this subscription uses Stripe test mode'
    )

    @api.depends('payment_provider_id', 'payment_provider_id.state')
    def _compute_is_test_subscription(self):
        """Determine if subscription is in test mode based on payment provider state"""
        for record in self:
            record.is_test_subscription = (
                record.payment_provider_id.state == 'test'
                if record.payment_provider_id
                else False
            )

    def _get_default_stripe_provider(self):
        """Get the default enabled Stripe payment provider"""
        provider = self.env['payment.provider'].search([
            ('code', '=', 'stripe'),
            ('state', 'in', ['enabled', 'test'])
        ], limit=1)
        return provider

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default payment provider"""
        for vals in vals_list:
            if not vals.get('payment_provider_id') and vals.get('stripe_sync_enabled', True):
                provider = self._get_default_stripe_provider()
                if provider:
                    vals['payment_provider_id'] = provider.id
        return super().create(vals_list)

    def button_start_date(self):
        """Override to sync subscription creation with Stripe"""
        res = super().button_start_date()

        for record in self:
            if record.stripe_sync_enabled and record.payment_provider_id:
                try:
                    record._stripe_create_subscription()
                except Exception as e:
                    _logger.error(
                        "Failed to create Stripe subscription for %s: %s",
                        record.name, str(e)
                    )
                    raise UserError(_(
                        "Failed to create subscription in Stripe:\n%s\n\n"
                        "The subscription was created in Odoo but not in Stripe. "
                        "Please check your Stripe configuration and try again.",
                        str(e)
                    ))
        return res

    def set_close(self):
        """Override to sync subscription cancellation with Stripe"""
        for record in self:
            if record.stripe_sync_enabled and record.stripe_subscription_id:
                try:
                    record._stripe_cancel_subscription()
                except Exception as e:
                    _logger.error(
                        "Failed to cancel Stripe subscription for %s: %s",
                        record.name, str(e)
                    )
                    # Don't block the closure in Odoo, just log the error
                    record.message_post(
                        body=_("Warning: Failed to cancel subscription in Stripe: %s", str(e))
                    )
        return super().set_close()

    def write(self, vals):
        """Override write to detect product line changes and sync with Stripe"""
        res = super().write(vals)

        # Check if product lines were modified
        if 'product_line_ids' in vals:
            for record in self:
                if (record.stripe_sync_enabled and
                    record.stripe_subscription_id and
                    record.stage_category == 'progress'):
                    try:
                        record._stripe_update_subscription()
                    except Exception as e:
                        _logger.error(
                            "Failed to update Stripe subscription for %s: %s",
                            record.name, str(e)
                        )
                        record.message_post(
                            body=_("Warning: Failed to update subscription in Stripe: %s", str(e))
                        )
        return res

    def _stripe_create_subscription(self):
        """Create a subscription in Stripe"""
        self.ensure_one()

        if not self.payment_provider_id:
            raise UserError(_("No Stripe payment provider configured for this subscription."))

        if self.stripe_subscription_id:
            raise UserError(_("This subscription is already synced with Stripe."))

        if not self.product_line_ids:
            raise UserError(_("Cannot create Stripe subscription without products."))

        # Create or get Stripe customer
        customer_id = self._stripe_get_or_create_customer()

        # Prepare subscription items from product lines
        subscription_items = self._stripe_prepare_subscription_items()

        # Create subscription in Stripe
        payload = {
            'customer': customer_id,
            'items': subscription_items,
            'description': self.name or f'Subscription {self.reference_code}',
            'metadata[odoo_subscription_id]': str(self.id),
            'metadata[odoo_subscription_ref]': self.reference_code or '',
        }

        # Add trial period if applicable
        if self.start_date and self.next_invoice_date:
            trial_end = int(self.next_invoice_date.strftime('%s'))
            payload['trial_end'] = trial_end

        response = self.payment_provider_id._stripe_make_request(
            'subscriptions',
            payload=payload
        )

        # Store Stripe references
        self.write({
            'stripe_subscription_id': response.get('id'),
            'stripe_customer_id': customer_id,
            'stripe_subscription_status': response.get('status'),
        })

        self.message_post(
            body=_("Subscription created in Stripe with ID: %s", response.get('id'))
        )

        _logger.info(
            "Created Stripe subscription %s for Odoo subscription %s",
            response.get('id'), self.id
        )

    def _stripe_cancel_subscription(self):
        """Cancel a subscription in Stripe"""
        self.ensure_one()

        if not self.stripe_subscription_id:
            _logger.warning("Attempted to cancel non-existent Stripe subscription for %s", self.name)
            return

        # Cancel the subscription in Stripe
        response = self.payment_provider_id._stripe_make_request(
            f'subscriptions/{self.stripe_subscription_id}',
            method='DELETE'
        )

        self.write({
            'stripe_subscription_status': response.get('status'),
        })

        self.message_post(
            body=_("Subscription cancelled in Stripe")
        )

        _logger.info(
            "Cancelled Stripe subscription %s for Odoo subscription %s",
            self.stripe_subscription_id, self.id
        )

    def _stripe_update_subscription(self):
        """Update a subscription in Stripe with new product lines"""
        self.ensure_one()

        if not self.stripe_subscription_id:
            _logger.warning("Attempted to update non-existent Stripe subscription for %s", self.name)
            return

        # Get current subscription from Stripe
        current_subscription = self.payment_provider_id._stripe_make_request(
            f'subscriptions/{self.stripe_subscription_id}',
            method='GET'
        )

        # Prepare new subscription items
        new_items = self._stripe_prepare_subscription_items()

        # Update each subscription item
        # First, cancel all existing items
        for item in current_subscription.get('items', {}).get('data', []):
            self.payment_provider_id._stripe_make_request(
                f'subscription_items/{item["id"]}',
                method='DELETE'
            )

        # Then add new items
        for item_data in new_items:
            payload = {
                'subscription': self.stripe_subscription_id,
                'price': item_data['price'],
                'quantity': item_data['quantity'],
            }
            self.payment_provider_id._stripe_make_request(
                'subscription_items',
                payload=payload
            )

        self.message_post(
            body=_("Subscription updated in Stripe")
        )

        _logger.info(
            "Updated Stripe subscription %s for Odoo subscription %s",
            self.stripe_subscription_id, self.id
        )

    def _stripe_get_or_create_customer(self):
        """Get existing Stripe customer or create a new one"""
        self.ensure_one()

        # Check if customer already exists
        if self.stripe_customer_id:
            return self.stripe_customer_id

        # Check if partner already has a Stripe customer ID
        # (from previous payment transactions)
        if self.partner_id.commercial_partner_id:
            existing_token = self.env['payment.token'].search([
                ('partner_id', '=', self.partner_id.commercial_partner_id.id),
                ('provider_id', '=', self.payment_provider_id.id),
                ('provider_ref', '!=', False)
            ], limit=1)
            if existing_token and existing_token.provider_ref:
                return existing_token.provider_ref

        # Create new customer in Stripe
        customer_payload = {
            'name': self.partner_id.name,
            'email': self.partner_id.email or '',
            'phone': self.partner_id.phone or '',
            'description': f'Odoo Partner: {self.partner_id.name} (ID: {self.partner_id.id})',
            'metadata[odoo_partner_id]': str(self.partner_id.id),
        }

        # Add address if available
        if self.partner_id.street:
            customer_payload['address[line1]'] = self.partner_id.street
        if self.partner_id.street2:
            customer_payload['address[line2]'] = self.partner_id.street2
        if self.partner_id.city:
            customer_payload['address[city]'] = self.partner_id.city
        if self.partner_id.state_id:
            customer_payload['address[state]'] = self.partner_id.state_id.name
        if self.partner_id.zip:
            customer_payload['address[postal_code]'] = self.partner_id.zip
        if self.partner_id.country_id:
            customer_payload['address[country]'] = self.partner_id.country_id.code

        response = self.payment_provider_id._stripe_make_request(
            'customers',
            payload=customer_payload
        )

        _logger.info(
            "Created Stripe customer %s for partner %s",
            response.get('id'), self.partner_id.id
        )

        return response.get('id')

    def _stripe_prepare_subscription_items(self):
        """Prepare subscription items payload for Stripe from product lines"""
        self.ensure_one()
        items = []

        for line in self.product_line_ids:
            # Get or create Stripe price for this product
            # Pass both the plan and the subscription's recurrence_period
            price_id = line.product_id._stripe_get_or_create_price(
                self.payment_provider_id,
                line.unit_price,
                self.currency_id,
                plan_id=self.plan_id,
                recurrence_period=self.recurrence_period_id
            )

            items.append({
                'price': price_id,
                'quantity': int(line.product_qty),
            })

        return items

    def action_sync_stripe_status(self):
        """Manual action to sync subscription status from Stripe"""
        self.ensure_one()

        if not self.stripe_subscription_id:
            raise UserError(_("This subscription is not linked to Stripe."))

        response = self.payment_provider_id._stripe_make_request(
            f'subscriptions/{self.stripe_subscription_id}',
            method='GET'
        )

        self.write({
            'stripe_subscription_status': response.get('status'),
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Stripe status updated: %s', response.get('status')),
                'type': 'success',
                'sticky': False,
            }
        }
