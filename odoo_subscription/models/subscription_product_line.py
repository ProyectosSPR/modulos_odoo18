# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SubscriptionProductLine(models.Model):
    _name = 'subscription.product.line'
    _description = 'Subscription Product Line'
    _order = 'sequence, id'

    subscription_id = fields.Many2one('subscription.package', string='Subscription', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Quantity', default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='UoM', related='product_id.uom_id')
    unit_price = fields.Float(string='Unit Price', related='product_id.lst_price')
    discount = fields.Float(string='Discount %', default=0.0)
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    total_amount = fields.Monetary(string='Subtotal', compute='_compute_total_amount', store=True, currency_field='currency_id')
    price_tax = fields.Monetary(string='Tax', compute='_compute_total_amount', store=True, currency_field='currency_id')
    price_total = fields.Monetary(string='Total', compute='_compute_total_amount', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='subscription_id.currency_id')
    sequence = fields.Integer(string='Sequence', default=10)

    @api.depends('product_qty', 'unit_price', 'discount', 'tax_ids')
    def _compute_total_amount(self):
        for line in self:
            price = line.unit_price * (1 - (line.discount or 0.0) / 100.0)
            line.total_amount = price * line.product_qty
            if line.tax_ids:
                tax_results = line.tax_ids.compute_all(price, line.currency_id, line.product_qty, line.product_id, line.subscription_id.partner_id)
                line.price_tax = sum(t.get('amount', 0.0) for t in tax_results.get('taxes', []))
                line.price_total = tax_results.get('total_included', 0.0)
            else:
                line.price_tax = 0.0
                line.price_total = line.total_amount
