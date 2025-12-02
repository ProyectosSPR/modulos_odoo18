# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    """Extensión de attachments para marcar facturas importadas"""
    _inherit = 'ir.attachment'

    auto_mark_for_tax_declaration = fields.Boolean(
        string='Auto-marcar para Declaración',
        default=False,
        help='Indica si las facturas creadas desde este XML se deben marcar para declaración',
    )

    def action_mark_related_invoices_for_declaration(self):
        """Marcar facturas relacionadas con este attachment para declaración"""
        self.ensure_one()

        # Buscar facturas relacionadas
        invoices = self.env['account.move'].search([
            '|',
            ('folio_fiscal', '=', self.uuid),
            ('message_main_attachment_id', '=', self.id),
        ])

        if not invoices:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sin facturas'),
                    'message': _('No se encontraron facturas relacionadas con este XML'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Marcar facturas
        period_date = fields.Date.today()
        for invoice in invoices:
            if invoice.invoice_date:
                period_date = invoice.invoice_date
            elif invoice.date:
                period_date = invoice.date

            invoice.write({
                'include_in_tax_declaration': True,
                'tax_declaration_period': period_date,
                'tax_declaration_status': 'pending',
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Éxito'),
                'message': _('%s factura(s) marcada(s) para declaración') % len(invoices),
                'type': 'success',
                'sticky': False,
            }
        }
