# -*- coding: utf-8 -*-

from odoo import fields, models

class AccountPayment(models.Model):
    """Extensión de pagos para gestión de deducibilidad"""
    _inherit = 'account.payment'

    # Campos de deducibilidad
    is_deductible = fields.Boolean(
        string='Es Deducible',
        default=True,
        help='Indica si este pago es deducible fiscalmente',
    )
    deductible_reason = fields.Selection([
        ('no_invoice', 'Sin Factura'),
        ('personal', 'Gasto Personal'),
        ('not_business', 'No Relacionado con Negocio'),
        ('duplicate', 'Duplicado'),
        ('other', 'Otro'),
    ], string='Razón de No Deducibilidad')

    non_deductible_notes = fields.Text(
        string='Notas de No Deducibilidad',
        help='Justificación adicional de por qué no es deducible',
    )

    # Campos de conciliación
    reconcile_rule_id = fields.Many2one(
        'mx.reconcile.rule',
        string='Regla de Conciliación',
    )
    reconcile_match_score = fields.Float(
        string='Score de Coincidencia',
    )
    
    # Campo temporal para el wizard
    mark_non_deductible = fields.Boolean(
        string='Marcar como No Deducible',
        default=False,
        help='Campo temporal para selección en wizard',
    )

    def action_mark_non_deductible(self):
        """Abrir wizard para marcar como no deducible"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Marcar como No Deducible',
            'res_model': 'mx.mark.non.deductible.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payment_ids': [(6, 0, self.ids)],
            }
        }
