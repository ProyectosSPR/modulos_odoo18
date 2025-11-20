# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ImportInvoiceProcessMessage(models.TransientModel):
    _name = 'import.invoice.process.message'
    _description = 'ImportInvoiceProcessMessage'

    name = fields.Char("Name")

    @api.model
    def default_get(self, fields_list):
        _logger.warning('=== WIZARD IMPORT_INVOICE_PROCESS_MESSAGE INICIADO ===')
        _logger.warning('Context received in default_get: %s', list(self._context.keys()))
        if 'not_imported_attachment' in self._context:
            _logger.warning('not_imported_attachment FOUND in context during default_get')
            _logger.warning('Value: %s', self._context.get('not_imported_attachment')[:200])
        return super().default_get(fields_list)
    
    
    def show_created_invoices(self):
        create_invoice_ids = self._context.get('create_invoice_ids', [])
        action = self.env.ref('account.action_move_in_invoice_type').sudo()
        result = action.read()[0]
        result['context'] = {'type': 'in_invoice'}
        result['domain'] = "[('id', 'in', " + str(create_invoice_ids) + ")]"
        return result

    @api.model
    def get_views(self, views, options=None):
        """Override get_views for Odoo 18 compatibility"""
        _logger.warning('=== GET_VIEWS CALLED (Odoo 18) ===')
        _logger.warning('Context keys: %s', list(self._context.keys()))
        _logger.warning('not_imported_attachment in context: %s', 'not_imported_attachment' in self._context)

        res = super().get_views(views, options)
        context = self._context

        _logger.warning('Processing views...')
        _logger.warning('Views in result: %s', list(res.get('views', {}).keys()))

        # Process each view type in the result
        for view_type, view_data in res.get('views', {}).items():
            if view_type == 'form' and 'arch' in view_data:
                _logger.warning('Processing form view in get_views...')

                if context.get('existed_attachment'):
                    _logger.warning('Replacing existed_attachment_content')
                    view_data['arch'] = view_data['arch'].replace("existed_attachment_content", context.get('existed_attachment'))
                else:
                    view_data['arch'] = view_data['arch'].replace("existed_attachment_content", '')

                if context.get('not_imported_attachment'):
                    _logger.warning('Replacing not_imported_attachment_content')
                    _logger.warning('Content to replace: %s', context.get('not_imported_attachment')[:200])
                    view_data['arch'] = view_data['arch'].replace("not_imported_attachment_content",
                                                                   context.get('not_imported_attachment'))
                    _logger.warning('Replacement done. Checking if placeholder still exists: %s',
                                   'not_imported_attachment_content' in view_data['arch'])
                else:
                    _logger.warning('not_imported_attachment NOT in context, replacing with empty')
                    view_data['arch'] = view_data['arch'].replace("not_imported_attachment_content", '')

                if context.get('imported_attachment'):
                    _logger.warning('Replacing imported_attachment_content')
                    view_data['arch'] = view_data['arch'].replace("imported_attachment_content", context.get('imported_attachment'))
                else:
                    view_data['arch'] = view_data['arch'].replace("imported_attachment_content", '')

        return res

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        """Keep get_view for backwards compatibility"""
        _logger.warning('=== GET_VIEW CALLED (Legacy) ===')
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
