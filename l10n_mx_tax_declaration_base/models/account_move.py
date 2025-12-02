# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class AccountMove(models.Model):
    """Extensión de facturas para declaraciones fiscales"""
    _inherit = 'account.move'

    # Campos para marcado de facturas en declaraciones
    include_in_tax_declaration = fields.Boolean(
        string='Incluir en Declaración Fiscal',
        default=False,
        copy=False,
        tracking=True,
        help='Marcar para incluir esta factura en las declaraciones fiscales',
    )

    tax_declaration_period = fields.Date(
        string='Período Fiscal',
        copy=False,
        tracking=True,
        help='Período fiscal al que corresponde esta factura',
    )

    tax_declaration_status = fields.Selection([
        ('pending', 'Pendiente de Declarar'),
        ('included', 'Incluida en Declaración'),
        ('excluded', 'Excluida de Declaración'),
        ('declared', 'Declarada'),
    ], string='Estado de Declaración',
        default='pending',
        copy=False,
        tracking=True,
    )

    tax_declaration_notes = fields.Text(
        string='Notas de Declaración',
        copy=False,
        help='Notas o comentarios sobre esta factura para efectos fiscales',
    )

    # Campo relacionado para facilitar búsquedas
    tax_declaration_month = fields.Integer(
        string='Mes Fiscal',
        compute='_compute_tax_declaration_month',
        store=True,
    )
    tax_declaration_year = fields.Integer(
        string='Año Fiscal',
        compute='_compute_tax_declaration_year',
        store=True,
    )

    @api.depends('tax_declaration_period')
    def _compute_tax_declaration_month(self):
        for record in self:
            if record.tax_declaration_period:
                record.tax_declaration_month = record.tax_declaration_period.month
            else:
                record.tax_declaration_month = 0

    @api.depends('tax_declaration_period')
    def _compute_tax_declaration_year(self):
        for record in self:
            if record.tax_declaration_period:
                record.tax_declaration_year = record.tax_declaration_period.year
            else:
                record.tax_declaration_year = 0

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-marcar facturas para declaración según configuración de obligaciones"""
        records = super().create(vals_list)

        for record in records:
            # Solo aplicar a facturas de cliente y proveedor
            if record.move_type in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund'):
                self._auto_mark_for_declaration(record)

        return records

    def write(self, vals):
        """Auto-marcar facturas cuando cambia su estado"""
        res = super().write(vals)

        # Si se confirma la factura, verificar auto-marcado
        if vals.get('state') == 'posted':
            for record in self:
                if record.move_type in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund'):
                    if not record.include_in_tax_declaration:
                        self._auto_mark_for_declaration(record)

        return res

    def _auto_mark_for_declaration(self, invoice):
        """Marcar automáticamente factura según configuración de obligaciones"""
        # Buscar obligaciones activas de la compañía con auto-marcado
        obligations = self.env['mx.tax.obligation'].search([
            ('company_id', '=', invoice.company_id.id),
            ('active', '=', True),
            ('auto_include_invoices', '=', True),
        ])

        for obligation in obligations:
            # Verificar si el tipo de factura coincide con el filtro
            should_include = False

            if obligation.invoice_type_filter == 'all':
                should_include = True
            elif obligation.invoice_type_filter == invoice.move_type:
                should_include = True

            if should_include:
                # Determinar el período fiscal
                period_date = invoice.invoice_date or invoice.date or fields.Date.today()

                invoice.write({
                    'include_in_tax_declaration': True,
                    'tax_declaration_period': period_date,
                    'tax_declaration_status': 'pending',
                })
                break  # Solo necesitamos marcar una vez

    def action_mark_for_declaration(self):
        """Acción para marcar facturas manualmente"""
        self.ensure_one()
        return {
            'name': _('Marcar para Declaración'),
            'type': 'ir.actions.act_window',
            'res_model': 'mx.tax.declaration.mark.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_ids': [(6, 0, self.ids)],
            },
        }

    def action_exclude_from_declaration(self):
        """Excluir facturas de declaraciones"""
        self.write({
            'include_in_tax_declaration': False,
            'tax_declaration_status': 'excluded',
        })

    def action_include_in_declaration(self):
        """Incluir facturas en declaraciones"""
        for record in self:
            if not record.tax_declaration_period:
                period_date = record.invoice_date or record.date or fields.Date.today()
                record.tax_declaration_period = period_date

        self.write({
            'include_in_tax_declaration': True,
            'tax_declaration_status': 'pending',
        })
