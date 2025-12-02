# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class MxMarkNonDeductibleWizard(models.TransientModel):
    """Wizard para marcar pagos como no deducibles manualmente"""
    _name = 'mx.mark.non.deductible.wizard'
    _description = 'Marcar Pagos No Deducibles'

    payment_ids = fields.Many2many(
        'account.payment',
        string='Pagos',
    )
    statement_line_ids = fields.Many2many(
        'account.bank.statement.line',
        string='Líneas Bancarias',
    )

    # Configuración
    deductible_reason = fields.Selection([
        ('no_invoice', 'Sin Factura'),
        ('personal', 'Gasto Personal'),
        ('not_business', 'No Relacionado con Negocio'),
        ('duplicate', 'Duplicado'),
        ('other', 'Otro'),
    ], string='Razón', required=True, default='no_invoice')

    notes = fields.Text(
        string='Justificación',
        help='Justificación adicional (opcional)',
    )

    @api.model
    def default_get(self, fields_list):
        """Cargar pagos desde líneas bancarias si no hay pagos directos"""
        res = super().default_get(fields_list)
        
        if 'statement_line_ids' in res and res.get('statement_line_ids'):
            # Obtener pagos relacionados con las líneas bancarias
            line_ids = res['statement_line_ids'][0][2] if res['statement_line_ids'] else []
            if line_ids:
                lines = self.env['account.bank.statement.line'].browse(line_ids)
                payments = lines.mapped('payment_id').filtered(lambda p: p)
                if payments:
                    res['payment_ids'] = [(6, 0, payments.ids)]
        
        return res

    def action_mark_all(self):
        """Marcar todos los pagos como no deducibles"""
        if not self.payment_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Advertencia',
                    'message': 'No hay pagos para marcar',
                    'type': 'warning',
                }
            }

        self.payment_ids.write({
            'is_deductible': False,
            'deductible_reason': self.deductible_reason,
            'non_deductible_notes': self.notes,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Éxito',
                'message': f'{len(self.payment_ids)} pago(s) marcado(s) como no deducible(s)',
                'type': 'success',
                'sticky': False,
            }
        }
