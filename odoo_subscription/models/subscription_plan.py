# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SubscriptionPlan(models.Model):
    _name = 'subscription.plan'
    _description = 'Subscription Plan'
    _order = 'name'

    name = fields.Char(string='Plan Name', required=True)
    short_code = fields.Char(string='Code', compute='_compute_short_code', store=True)
    renewal_value = fields.Integer(string='Renewal Value', default=1)
    renewal_period = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years'),
    ], string='Renewal Period', default='months', required=True)
    renewal_time = fields.Integer(string='Renewal (Days)', compute='_compute_renewal_time', store=True)
    limit_choice = fields.Selection([
        ('ones', 'Single Billing'),
        ('manual', 'Until Manually Closed'),
        ('custom', 'Custom Limit'),
    ], string='Billing Limit', default='manual', required=True)
    limit_count = fields.Integer(string='Renewal Count', default=12)
    days_to_end = fields.Integer(string='Days to End', compute='_compute_days_to_end', store=True)
    invoice_mode = fields.Selection([
        ('manual', 'Manual'),
        ('draft_invoice', 'Auto Draft Invoice'),
    ], string='Invoice Mode', default='draft_invoice')
    journal_id = fields.Many2one('account.journal', string='Journal', domain="[('type','=','sale')]")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    terms_and_conditions = fields.Text(string='Terms & Conditions')
    subscription_count = fields.Integer(string='Subscriptions', compute='_compute_subscription_count')
    active = fields.Boolean(default=True)

    @api.depends('name')
    def _compute_short_code(self):
        for rec in self:
            if rec.name:
                words = rec.name.split()[:3]
                rec.short_code = ''.join([w[0].upper() for w in words if w])
            else:
                rec.short_code = ''

    @api.depends('renewal_value', 'renewal_period')
    def _compute_renewal_time(self):
        for rec in self:
            multiplier = {'days': 1, 'weeks': 7, 'months': 30, 'years': 365}
            rec.renewal_time = rec.renewal_value * multiplier.get(rec.renewal_period, 30)

    @api.depends('limit_choice', 'limit_count', 'renewal_time')
    def _compute_days_to_end(self):
        for rec in self:
            if rec.limit_choice == 'custom':
                rec.days_to_end = rec.renewal_time * rec.limit_count
            else:
                rec.days_to_end = 0

    def _compute_subscription_count(self):
        for rec in self:
            rec.subscription_count = self.env['subscription.package'].search_count([('plan_id', '=', rec.id)])

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.short_code} - {rec.name}" if rec.short_code else rec.name
            result.append((rec.id, name))
        return result
