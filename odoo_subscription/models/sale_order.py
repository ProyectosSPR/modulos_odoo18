# -*- coding: utf-8 -*-

from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    subscription_id = fields.Many2one('subscription.package', string='Subscription', readonly=True, copy=False)
    is_subscription = fields.Boolean(string='Has Subscription', compute='_compute_is_subscription', store=True)

    def _compute_is_subscription(self):
        for order in self:
            order.is_subscription = bool(order.subscription_id)
