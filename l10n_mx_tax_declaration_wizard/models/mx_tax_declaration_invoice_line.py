# -*- coding: utf-8 -*-

from odoo import fields, models, api


class MxTaxDeclarationInvoiceLine(models.Model):
    """Líneas de facturas en una declaración fiscal"""
    _name = 'mx.tax.declaration.invoice.line'
    _description = 'Línea de Factura en Declaración'
    _order = 'invoice_date desc, id desc'

    declaration_id = fields.Many2one(
        'mx.tax.declaration',
        string='Declaración',
        required=True,
        ondelete='cascade',
        index=True,
    )

    invoice_id = fields.Many2one(
        'account.move',
        string='Factura',
        required=True,
        ondelete='restrict',
        index=True,
    )

    # Campos denormalizados para performance y reporte
    invoice_date = fields.Date(
        string='Fecha',
        related='invoice_id.invoice_date',
        store=True,
        readonly=True,
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente/Proveedor',
        related='invoice_id.partner_id',
        store=True,
        readonly=True,
    )

    move_type = fields.Selection(
        related='invoice_id.move_type',
        string='Tipo',
        store=True,
        readonly=True,
    )

    ref = fields.Char(
        string='Referencia',
        related='invoice_id.ref',
        store=True,
        readonly=True,
    )

    # UUID del CFDI (si aplica)
    l10n_mx_edi_cfdi_uuid = fields.Char(
        string='UUID',
        related='invoice_id.l10n_mx_edi_cfdi_uuid',
        store=True,
        readonly=True,
    )

    # Montos
    amount_untaxed = fields.Monetary(
        string='Subtotal',
        related='invoice_id.amount_untaxed',
        store=True,
        readonly=True,
        currency_field='currency_id',
    )

    amount_tax = fields.Monetary(
        string='Impuestos',
        related='invoice_id.amount_tax',
        store=True,
        readonly=True,
        currency_field='currency_id',
    )

    amount_total = fields.Monetary(
        string='Total',
        related='invoice_id.amount_total',
        store=True,
        readonly=True,
        currency_field='currency_id',
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='invoice_id.currency_id',
        store=True,
        readonly=True,
    )

    # Control de inclusión
    included = fields.Boolean(
        string='Incluida',
        default=True,
        help='Si está marcada, esta factura se incluye en los cálculos de la declaración',
    )

    exclusion_reason = fields.Text(
        string='Motivo de Exclusión',
        help='Razón por la cual esta factura fue excluida de la declaración',
    )

    # Estado de la factura
    invoice_state = fields.Selection(
        related='invoice_id.state',
        string='Estado Factura',
        store=True,
        readonly=True,
    )

    # Información fiscal adicional
    tax_declaration_status = fields.Selection(
        related='invoice_id.tax_declaration_status',
        string='Estado Declaración',
        store=True,
        readonly=True,
    )

    def action_view_invoice(self):
        """Ver la factura relacionada"""
        self.ensure_one()
        return {
            'name': _('Factura'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_exclude(self):
        """Excluir factura de la declaración"""
        self.write({'included': False})

    def action_include(self):
        """Incluir factura en la declaración"""
        self.write({'included': True, 'exclusion_reason': False})

    _sql_constraints = [
        ('declaration_invoice_unique',
         'unique(declaration_id, invoice_id)',
         'Esta factura ya está incluida en esta declaración'),
    ]
