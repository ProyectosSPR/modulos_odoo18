# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ImportInvoiceProcessMessage(models.TransientModel):
    _name = 'import.invoice.process.message'
    _description = 'ImportInvoiceProcessMessage'

    name = fields.Char("Name")
    existed_attachment_html = fields.Html(string="XML Existentes", readonly=True)
    not_imported_attachment_html = fields.Html(string="XML No Importados", readonly=True)
    imported_attachment_html = fields.Html(string="XML Importados", readonly=True)

    @api.model
    def default_get(self, fields_list):
        _logger.warning('=== WIZARD IMPORT_INVOICE_PROCESS_MESSAGE INICIADO ===')
        _logger.warning('Context received in default_get: %s', list(self._context.keys()))

        res = super().default_get(fields_list)

        # Populate fields from context
        if 'existed_attachment' in self._context:
            res['existed_attachment_html'] = self._context['existed_attachment']
            _logger.warning('existed_attachment populated in fields')

        if 'not_imported_attachment' in self._context:
            res['not_imported_attachment_html'] = self._context['not_imported_attachment']
            _logger.warning('not_imported_attachment populated in fields')
            _logger.warning('Value: %s', self._context.get('not_imported_attachment')[:200])

        if 'imported_attachment' in self._context:
            res['imported_attachment_html'] = self._context['imported_attachment']
            _logger.warning('imported_attachment populated in fields')

        return res
    
    
    def show_created_invoices(self):
        create_invoice_ids = self._context.get('create_invoice_ids', [])
        action = self.env.ref('account.action_move_in_invoice_type').sudo()
        result = action.read()[0]
        result['context'] = {'type': 'in_invoice'}
        result['domain'] = "[('id', 'in', " + str(create_invoice_ids) + ")]"
        return result

