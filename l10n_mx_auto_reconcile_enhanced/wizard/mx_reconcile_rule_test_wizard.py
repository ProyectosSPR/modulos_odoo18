# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class MxReconcileRuleTestWizard(models.TransientModel):
    """Wizard para probar reglas de conciliación y ver preview"""
    _name = 'mx.reconcile.rule.test.wizard'
    _description = 'Probar Regla de Conciliación'

    rule_id = fields.Many2one(
        'mx.reconcile.rule',
        string='Regla',
        required=True,
        readonly=True,
    )

    # Filtros para el test
    date_from = fields.Date(
        string='Fecha Desde',
        default=fields.Date.context_today,
    )
    date_to = fields.Date(
        string='Fecha Hasta',
        default=fields.Date.context_today,
    )

    # Filtros adicionales (domain)
    source_domain = fields.Char(
        string='Filtro de Origen',
        default="[]",
        help="Domain para filtrar líneas bancarias/pagos. Ejemplo: [('amount', '>', 1000)]",
    )
    target_domain = fields.Char(
        string='Filtro de Facturas',
        default="[]",
        help="Domain para filtrar facturas. Ejemplo: [('move_type', '=', 'out_invoice')]",
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

    # IDs de resultados para mostrar en vista
    matched_line_ids = fields.Many2many(
        'account.bank.statement.line',
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

        # Obtener registros origen
        source_domain = self._get_source_domain()
        source_records = self._get_source_records(source_domain)

        # Obtener facturas objetivo
        target_domain = self._get_target_domain()
        target_records = self._get_target_records(target_domain)

        # Aplicar regla
        matches = self.rule_id.apply_rule(source_records, target_records)

        # Actualizar estadísticas
        matched_line_ids = []
        for source, target, score in matches:
            matched_line_ids.append(source.id)
            # Actualizar la línea con la sugerencia
            source.write({
                'suggested_invoice_id': target.id,
                'reconcile_match_score': score,
                'reconcile_rule_id': self.rule_id.id,
            })

        self.write({
            'total_source': len(source_records),
            'total_target': len(target_records),
            'total_matches': len(matches),
            'matched_line_ids': [(6, 0, matched_line_ids)],
        })

        # Retornar el mismo wizard para mostrar resultados
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

    def _get_source_domain(self):
        """Construir domain para registros origen"""
        try:
            custom_domain = eval(self.source_domain) if self.source_domain else []
        except:
            custom_domain = []

        base_domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]

        return base_domain + custom_domain

    def _get_target_domain(self):
        """Construir domain para facturas"""
        try:
            custom_domain = eval(self.target_domain) if self.target_domain else []
        except:
            custom_domain = []

        base_domain = [
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
        ]

        return base_domain + custom_domain

    def _get_source_records(self, domain):
        """Obtener registros origen según el tipo"""
        if self.rule_id.source_model == 'statement_line':
            return self.env['account.bank.statement.line'].search(domain)
        else:  # payment
            return self.env['account.payment'].search(domain)

    def _get_target_records(self, domain):
        """Obtener facturas objetivo"""
        return self.env['account.move'].search(domain)
