# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class MxReconcileRuleTestWizardUnified(models.TransientModel):
    """Wizard para probar reglas unificadas"""
    _name = 'mx.reconcile.rule.test.wizard.unified'
    _description = 'Probar Regla de Conciliación Unificada'

    rule_id = fields.Many2one(
        'mx.reconcile.rule.unified',
        string='Regla',
        required=True,
        readonly=True,
    )

    # Período de prueba
    date_from = fields.Date(
        string='Fecha Desde',
        default=fields.Date.context_today,
        required=True,
    )
    date_to = fields.Date(
        string='Fecha Hasta',
        default=fields.Date.context_today,
        required=True,
    )

    # Resultados
    total_payments = fields.Integer(string='Total Pagos/Líneas', readonly=True)
    total_invoices = fields.Integer(string='Total Facturas', readonly=True)
    total_matches = fields.Integer(string='Total Matches', readonly=True)
    match_percentage = fields.Float(
        string='% Match',
        readonly=True,
        compute='_compute_match_percentage',
    )

    # Líneas con match
    matched_line_ids = fields.Many2many(
        'account.bank.statement.line',
        'mx_unified_test_line_rel',
        'wizard_id',
        'line_id',
        string='Líneas con Match',
        readonly=True,
    )

    # Detalles
    match_detail_ids = fields.One2many(
        'mx.reconcile.rule.test.match.unified',
        'wizard_id',
        string='Detalles de Matches',
    )

    @api.depends('total_payments', 'total_matches')
    def _compute_match_percentage(self):
        for wizard in self:
            if wizard.total_payments > 0:
                wizard.match_percentage = (wizard.total_matches / wizard.total_payments) * 100
            else:
                wizard.match_percentage = 0.0

    def action_test_rule(self):
        """Ejecutar prueba de la regla"""
        self.ensure_one()

        # Limpiar resultados anteriores
        self.match_detail_ids.unlink()

        # Obtener pagos/líneas del período
        payment_domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]
        payments = self.env['account.bank.statement.line'].search(payment_domain)

        # Obtener facturas objetivo
        invoice_domain = [
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
        ]
        invoices = self.env['account.move'].search(invoice_domain)

        # Aplicar regla
        matches = self.rule_id.apply_rule(payments, invoices)

        # Crear detalles y actualizar líneas
        match_details = []
        matched_line_ids = []

        for payment, invoice, score, extra_info in matches:
            matched_line_ids.append(payment.id)

            # Actualizar línea con sugerencia
            payment.write({
                'suggested_invoice_id': invoice.id,
                'reconcile_match_score': score,
            })

            # Crear detalle
            match_details.append((0, 0, {
                'payment_id': payment.id,
                'invoice_id': invoice.id,
                'match_score': score,
                'match_info': extra_info,
            }))

        # Actualizar wizard
        self.write({
            'total_payments': len(payments),
            'total_invoices': len(invoices),
            'total_matches': len(matches),
            'matched_line_ids': [(6, 0, matched_line_ids)],
            'match_detail_ids': match_details,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_open_reconcile_view(self):
        """Abrir vista de conciliación OCA"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Vista de Conciliación',
            'res_model': 'account.bank.statement.line',
            'view_mode': 'kanban,list',
            'views': [
                (self.env.ref('account_reconcile_oca.bank_statement_line_reconcile_view').id, 'kanban'),
            ],
            'domain': [('id', 'in', self.matched_line_ids.ids)],
            'context': {
                'view_ref': 'account_reconcile_oca.bank_statement_line_form_reconcile_view',
            },
            'target': 'current',
        }


class MxReconcileRuleTestMatchUnified(models.TransientModel):
    """Detalle de cada match"""
    _name = 'mx.reconcile.rule.test.match.unified'
    _description = 'Detalle de Match Unificado'

    wizard_id = fields.Many2one(
        'mx.reconcile.rule.test.wizard.unified',
        required=True,
        ondelete='cascade',
    )

    payment_id = fields.Many2one(
        'account.bank.statement.line',
        string='Pago/Línea',
        required=True,
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Factura',
        required=True,
    )
    match_score = fields.Float(string='Score %', digits=(5, 2))
    match_info = fields.Char(string='Información del Match')

    # Campos relacionados para mostrar
    payment_date = fields.Date(related='payment_id.date', string='Fecha')
    payment_ref = fields.Char(related='payment_id.payment_ref', string='Ref Pago')
    payment_amount = fields.Monetary(
        related='payment_id.amount',
        string='Monto Pago',
        currency_field='currency_id',
    )

    invoice_name = fields.Char(related='invoice_id.name', string='Factura')
    invoice_partner = fields.Char(
        related='invoice_id.partner_id.name',
        string='Partner',
    )
    invoice_amount = fields.Monetary(
        related='invoice_id.amount_total',
        string='Total Factura',
        currency_field='currency_id',
    )

    currency_id = fields.Many2one(related='payment_id.currency_id')
