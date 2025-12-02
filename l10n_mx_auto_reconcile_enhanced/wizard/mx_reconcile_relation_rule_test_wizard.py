# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class MxReconcileRelationRuleTestWizard(models.TransientModel):
    """Wizard para probar reglas de conciliación por relación"""
    _name = 'mx.reconcile.relation.rule.test.wizard'
    _description = 'Probar Regla de Conciliación por Relación'

    rule_id = fields.Many2one(
        'mx.reconcile.relation.rule',
        string='Regla',
        required=True,
        readonly=True,
    )

    # Filtros
    date_from = fields.Date(
        string='Fecha Desde',
        default=fields.Date.context_today,
    )
    date_to = fields.Date(
        string='Fecha Hasta',
        default=fields.Date.context_today,
    )

    # Resultados
    total_source = fields.Integer(
        string='Total Líneas/Pagos',
        readonly=True,
    )
    total_target = fields.Integer(
        string='Total Facturas',
        readonly=True,
    )
    total_matches = fields.Integer(
        string='Total Matches',
        readonly=True,
    )
    match_percentage = fields.Float(
        string='% de Match',
        readonly=True,
        compute='_compute_match_percentage',
    )

    matched_line_ids = fields.Many2many(
        'account.bank.statement.line',
        'mx_rel_rule_test_line_rel',
        'wizard_id',
        'line_id',
        string='Líneas con Match',
        readonly=True,
    )

    @api.depends('total_source', 'total_matches')
    def _compute_match_percentage(self):
        for wizard in self:
            if wizard.total_source > 0:
                wizard.match_percentage = (wizard.total_matches / wizard.total_source) * 100
            else:
                wizard.match_percentage = 0.0

    def action_test_rule(self):
        """Ejecutar test de la regla"""
        self.ensure_one()

        # Obtener líneas bancarias del período
        source_domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]
        source_records = self.env['account.bank.statement.line'].search(source_domain)

        # Obtener facturas objetivo
        target_domain = [
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
        ]
        target_records = self.env['account.move'].search(target_domain)

        # Aplicar regla por relación
        matches = self.rule_id.apply_relation_rule(source_records, target_records)

        # Actualizar líneas con sugerencias
        matched_line_ids = []
        for source, target, score, related_doc in matches:
            matched_line_ids.append(source.id)
            source.write({
                'suggested_invoice_id': target.id,
                'reconcile_match_score': score,
            })

        self.write({
            'total_source': len(source_records),
            'total_target': len(target_records),
            'total_matches': len(matches),
            'matched_line_ids': [(6, 0, matched_line_ids)],
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_open_reconcile_view(self):
        """Abrir vista de conciliación OCA con los matches"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Vista Previa de Conciliación',
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
