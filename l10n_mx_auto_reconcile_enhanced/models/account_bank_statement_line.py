# -*- coding: utf-8 -*-

from odoo import fields, models, api

class AccountBankStatementLine(models.Model):
    """Extensión de líneas bancarias para conciliación automática"""
    _inherit = 'account.bank.statement.line'

    # Campos de conciliación automática
    reconcile_rule_id = fields.Many2one(
        'mx.reconcile.rule',
        string='Regla de Conciliación',
        help='Regla que generó la sugerencia de conciliación',
    )
    reconcile_match_score = fields.Float(
        string='Score de Coincidencia',
        help='Porcentaje de confianza del match (0-100)',
    )
    reconcile_suggestions = fields.Text(
        string='Sugerencias de Conciliación',
        help='JSON con sugerencias de facturas para conciliar',
    )
    auto_reconciled = fields.Boolean(
        string='Conciliado Automáticamente',
        default=False,
    )
    suggested_invoice_id = fields.Many2one(
        'account.move',
        string='Factura Sugerida',
        help='Factura sugerida por las reglas automáticas',
    )

    def action_auto_reconcile(self):
        """Ejecutar conciliación automática para esta línea"""
        self.ensure_one()
        
        # Buscar facturas sin conciliar
        invoices = self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('company_id', '=', self.company_id.id),
        ])

        # Aplicar reglas directas
        direct_rules = self.env['mx.reconcile.rule'].search([
            ('active', '=', True),
            ('source_model', '=', 'statement_line'),
        ], order='sequence, priority desc')

        best_match = None
        best_score = 0.0
        best_rule = None

        for rule in direct_rules:
            matches = rule.apply_rule(self, invoices)
            for source, invoice, score in matches:
                if score > best_score:
                    best_score = score
                    best_match = invoice
                    best_rule = rule

        # Aplicar reglas por relación
        relation_rules = self.env['mx.reconcile.relation.rule'].search([
            ('active', '=', True),
        ], order='sequence, priority desc')

        for rule in relation_rules:
            matches = rule.apply_relation_rule(self, invoices)
            for source, invoice, score, related_doc in matches:
                if score > best_score:
                    best_score = score
                    best_match = invoice
                    best_rule = rule

        # Actualizar sugerencia
        if best_match:
            self.write({
                'suggested_invoice_id': best_match.id,
                'reconcile_match_score': best_score,
                'reconcile_rule_id': best_rule.id if isinstance(best_rule, type(self.env['mx.reconcile.rule'])) else False,
            })

            # Crear log
            self.env['mx.reconcile.log'].create({
                'statement_line_id': self.id,
                'invoice_id': best_match.id,
                'rule_id': best_rule.id if isinstance(best_rule, type(self.env['mx.reconcile.rule'])) else False,
                'relation_rule_id': best_rule.id if isinstance(best_rule, type(self.env['mx.reconcile.relation.rule'])) else False,
                'rule_type': 'direct' if isinstance(best_rule, type(self.env['mx.reconcile.rule'])) else 'relation',
                'match_score': best_score,
                'state': 'confirmed' if best_score >= 95.0 else 'pending',
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Conciliación Automática',
                'message': f'Sugerencia encontrada con score: {best_score:.1f}%' if best_match else 'No se encontraron coincidencias',
                'type': 'success' if best_match else 'warning',
            }
        }

    def action_show_suggestions(self):
        """Mostrar sugerencias de conciliación"""
        self.ensure_one()
        if not self.suggested_invoice_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sin Sugerencias',
                    'message': 'No hay sugerencias de conciliación para esta línea',
                    'type': 'warning',
                }
            }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Factura Sugerida',
            'res_model': 'account.move',
            'res_id': self.suggested_invoice_id.id,
            'view_mode': 'form',
            'target': 'new',
        }
