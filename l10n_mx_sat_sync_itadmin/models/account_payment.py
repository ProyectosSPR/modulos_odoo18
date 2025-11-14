# -*- coding: utf-8 -*-

from odoo import models, fields

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    attachment_id = fields.Many2one("ir.attachment", 'Attachment Sync')

