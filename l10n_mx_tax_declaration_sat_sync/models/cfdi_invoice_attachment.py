# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class CfdiInvoiceAttachment(models.TransientModel):
    """Extensión del wizard de importación de facturas SAT"""
    _inherit = 'cfdi.invoice.attachment'

    # Configuración para declaraciones fiscales
    auto_mark_for_declaration = fields.Boolean(
        string='Auto-marcar para Declaración',
        default=True,
        help='Marcar automáticamente las facturas importadas para incluir en declaraciones fiscales',
    )

    tax_declaration_period = fields.Date(
        string='Período Fiscal por Defecto',
        help='Período fiscal a asignar a las facturas importadas',
    )

    def import_xml_file(self):
        """Override del método de importación para agregar marcado fiscal"""
        # Guardar configuración en contexto
        ctx = self._context.copy()
        ctx.update({
            'auto_mark_for_declaration': self.auto_mark_for_declaration,
            'tax_declaration_period': self.tax_declaration_period,
        })

        # Ejecutar importación original
        res = super(CfdiInvoiceAttachment, self.with_context(ctx)).import_xml_file()

        # Si se crearon facturas, marcarlas para declaración
        if self.auto_mark_for_declaration:
            self._mark_imported_invoices_for_declaration()

        return res

    def _mark_imported_invoices_for_declaration(self):
        """Marcar facturas recién importadas para declaración"""
        # Buscar facturas creadas recientemente
        # Este método se puede mejorar para obtener las facturas exactas creadas
        ctx = self._context.copy()
        active_ids = ctx.get('active_ids', [])

        if not active_ids:
            return

        # Obtener attachments procesados
        attachments = self.env['ir.attachment'].browse(active_ids)

        # Buscar facturas relacionadas con estos attachments
        # Filtrar attachments que tengan UUID
        uuids = attachments.filtered(lambda a: a.cfdi_uuid).mapped('cfdi_uuid')

        domain = [
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'posted'),
            ('include_in_tax_declaration', '=', False),
        ]

        # Buscar por UUID si existen
        if uuids:
            domain.append(('l10n_mx_edi_cfdi_uuid', 'in', uuids))
        else:
            # Si no hay UUIDs, no buscar facturas
            invoices = self.env['account.move']
            return

        invoices = self.env['account.move'].search(domain)

        if not invoices:
            return

        # Determinar período fiscal
        period_date = self.tax_declaration_period or fields.Date.today()

        # Marcar facturas
        for invoice in invoices:
            # Solo marcar si aún no está marcada
            if not invoice.include_in_tax_declaration:
                # Usar la fecha de la factura si no hay período configurado
                if not self.tax_declaration_period:
                    period_date = invoice.invoice_date or invoice.date or fields.Date.today()

                invoice.write({
                    'include_in_tax_declaration': True,
                    'tax_declaration_period': period_date,
                    'tax_declaration_status': 'pending',
                })

        _logger.info(f"Marcadas {len(invoices)} facturas para declaración fiscal")
