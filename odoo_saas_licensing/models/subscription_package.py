# -*- coding: utf-8 -*-

from odoo import models, fields


class SubscriptionPackage(models.Model):
    _inherit = 'subscription.package'

    # Licensing Integration
    license_ids = fields.One2many('saas.license', 'subscription_id', string='Licenses')
    license_count = fields.Integer(string='Licenses', compute='_compute_license_count')

    def _compute_license_count(self):
        for rec in self:
            rec.license_count = len(rec.license_ids)
