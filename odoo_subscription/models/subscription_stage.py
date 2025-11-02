# -*- coding: utf-8 -*-

from odoo import models, fields


class SubscriptionStage(models.Model):
    _name = 'subscription.stage'
    _description = 'Subscription Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    category = fields.Selection([
        ('draft', 'Draft'),
        ('progress', 'In Progress'),
        ('closed', 'Closed'),
    ], string='Category', required=True, default='draft')
    condition = fields.Text(string='Conditions')
    is_fold = fields.Boolean(string='Folded in Kanban', default=False)
