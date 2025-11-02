# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_subscription = fields.Boolean(string='Subscription Product', default=False)
    subscription_plan_id = fields.Many2one('subscription.plan', string='Default Plan')
