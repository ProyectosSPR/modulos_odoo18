# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SubscriptionMetering(models.Model):
    _name = 'subscription.metering'
    _description = 'Subscription Usage Metering'
    _order = 'date desc'

    subscription_id = fields.Many2one('subscription.package', string='Subscription', required=True, ondelete='cascade', index=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    metric_type = fields.Selection([
        ('users', 'Active Users'),
        ('storage', 'Storage (GB)'),
        ('api_calls', 'API Calls'),
        ('custom', 'Custom Metric'),
    ], string='Metric Type', required=True)
    metric_value = fields.Float(string='Value', required=True)
    unit_price = fields.Monetary(string='Unit Price', currency_field='currency_id')
    total_amount = fields.Monetary(string='Total', compute='_compute_total_amount', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='subscription_id.currency_id')
    invoiced = fields.Boolean(string='Invoiced', default=False)
    invoice_id = fields.Many2one('account.move', string='Invoice')
    notes = fields.Text(string='Notes')

    @api.depends('metric_value', 'unit_price')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.metric_value * rec.unit_price
