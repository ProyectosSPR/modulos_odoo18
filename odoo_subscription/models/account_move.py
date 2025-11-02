# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    subscription_id = fields.Many2one('subscription.package', string='Subscription', readonly=True, copy=False)
