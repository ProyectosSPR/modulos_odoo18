# -*- coding: utf-8 -*-

from odoo import models, fields

DEFAULT_CFDI_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    l10n_mx_edi_cfdi_uuid = fields.Char(string='Folio Fiscal Sync', copy=False, readonly=True,
        help='Folio in electronic invoice, is returned by SAT when send to stamp.',) #compute='_compute_cfdi_values', store=True
    attachment_id = fields.Many2one("ir.attachment", 'Attachment Sync')

