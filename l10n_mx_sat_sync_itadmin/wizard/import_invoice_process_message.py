# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ImportInvoiceProcessMessage(models.TransientModel):
    _name = 'import.invoice.process.message'
    _description = 'ImportInvoiceProcessMessage'

    name = fields.Char("Name")
    
    
    def show_created_invoices(self):
        create_invoice_ids = self._context.get('create_invoice_ids', [])
        action = self.env.ref('account.action_move_in_invoice_type').sudo()
        result = action.read()[0]
        result['context'] = {'type': 'in_invoice'}
        result['domain'] = "[('id', 'in', " + str(create_invoice_ids) + ")]"
        return result

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        _logger.warning('=== GET_VIEW CALLED ===')
        _logger.warning('view_type: %s', view_type)
        _logger.warning('Context keys: %s', list(self._context.keys()))
        _logger.warning('not_imported_attachment in context: %s', 'not_imported_attachment' in self._context)

        res = super().get_view(view_id, view_type, **options)

        if view_type == 'form':
            context = self._context
            _logger.warning('Processing form view...')

            if context.get('existed_attachment'):
                _logger.warning('Replacing existed_attachment_content')
                res['arch'] = res['arch'].replace("existed_attachment_content", context.get('existed_attachment'))
            else:
                res['arch'] = res['arch'].replace("existed_attachment_content", '')

            if context.get('not_imported_attachment'):
                _logger.warning('Replacing not_imported_attachment_content')
                _logger.warning('Content to replace: %s', context.get('not_imported_attachment')[:200])
                res['arch'] = res['arch'].replace("not_imported_attachment_content",
                                                  context.get('not_imported_attachment'))
                _logger.warning('Replacement done. Checking if placeholder still exists: %s',
                               'not_imported_attachment_content' in res['arch'])
            else:
                _logger.warning('not_imported_attachment NOT in context, replacing with empty')
                res['arch'] = res['arch'].replace("not_imported_attachment_content", '')

            if context.get('imported_attachment'):
                _logger.warning('Replacing imported_attachment_content')
                res['arch'] = res['arch'].replace("imported_attachment_content", context.get('imported_attachment'))
            else:
                res['arch'] = res['arch'].replace("imported_attachment_content", '')

        return res
