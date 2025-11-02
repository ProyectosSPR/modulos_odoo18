# -*- coding: utf-8 -*-

from odoo import models, fields


class SubscriptionStopReason(models.Model):
    _name = 'subscription.stop.reason'
    _description = 'Subscription Stop Reason'
    _order = 'sequence, name'

    name = fields.Char(string='Reason', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
