# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class MxAutoReconcileWizard(models.TransientModel):
    """Wizard de conciliación automática"""
    _name = 'mx.auto.reconcile.wizard'
    _description = 'Wizard de Conciliación Automática'

    date_from = fields.Date(
        string='Fecha Desde',
        required=True,
        default=fields.Date.context_today,
    )
    date_to = fields.Date(
        string='Fecha Hasta',
        required=True,
        default=fields.Date.context_today,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
    )
    journal_ids = fields.Many2many(
        'account.journal',
        string='Diarios',
        domain="[('type', '=', 'bank')]",
    )

    tax_declaration_wizard_id = fields.Many2one(
        'mx.tax.declaration.wizard',
        string='Wizard de Declaración',
        ondelete='cascade',
    )

    # Opciones
    source_type = fields.Selection([
        ('statement_lines', 'Líneas Bancarias'),
        ('payments', 'Pagos'),
        ('both', 'Ambos'),
    ], string='Tipo de Origen', default='statement_lines', required=True)

    only_unreconciled = fields.Boolean(
        string='Solo No Conciliados',
        default=True,
    )
    apply_direct_rules = fields.Boolean(
        string='Aplicar Reglas Directas',
        default=True,
    )
    apply_relation_rules = fields.Boolean(
        string='Aplicar Reglas por Relación',
        default=True,
    )
    min_match_score = fields.Float(
        string='Score Mínimo (%)',
        default=80.0,
        help='Score mínimo para considerar un match',
    )

    # Resultados (Computed)
    total_processed = fields.Integer(
        string='Total Procesados',
        compute='_compute_results',
        store=True,
    )
    total_matched = fields.Integer(
        string='Total con Match',
        compute='_compute_results',
        store=True,
    )
    total_auto_reconciled = fields.Integer(
        string='Auto-Conciliados',
        compute='_compute_results',
        store=True,
    )
    total_suggestions = fields.Integer(
        string='Sugerencias',
        compute='_compute_results',
        store=True,
    )
    total_unmatched = fields.Integer(
        string='Sin Match',
        compute='_compute_results',
        store=True,
    )

    # Relaciones
    log_ids = fields.One2many(
        'mx.reconcile.log',
        'id',  # Temporal, se llenará dinámicamente
        string='Log de Conciliaciones',
    )
    suggestion_ids = fields.Many2many(
        'account.bank.statement.line',
        string='Líneas con Sugerencias',
    )
    unmatched_ids = fields.Many2many(
        'account.bank.statement.line',
        'mx_reconcile_wizard_unmatched_rel',
        string='Líneas Sin Match',
    )

    @api.depends('suggestion_ids', 'unmatched_ids')
    def _compute_results(self):
        for wizard in self:
            wizard.total_suggestions = len(wizard.suggestion_ids)
            wizard.total_unmatched = len(wizard.unmatched_ids)
            wizard.total_matched = wizard.total_suggestions
            wizard.total_auto_reconciled = 0  # Se calculará después
            wizard.total_processed = wizard.total_matched + wizard.total_unmatched

    def action_run_reconciliation(self):
        """Ejecutar proceso de conciliación automática"""
        self.ensure_one()

        _logger.info("=" * 80)
        _logger.info("INICIANDO PROCESO DE CONCILIACIÓN AUTOMÁTICA")
        _logger.info(f"Período: {self.date_from} - {self.date_to}")
        _logger.info(f"Compañía: {self.company_id.name}")
        _logger.info("=" * 80)

        # Obtener items sin conciliar
        items = self._get_unreconciled_items()
        _logger.info(f"Items sin conciliar encontrados: {len(items)}")
        
        if not items:
            raise UserError(_('No se encontraron items sin conciliar en el período seleccionado.\n\n'
                            'Período: %s - %s\n'
                            'Compañía: %s') % (self.date_from, self.date_to, self.company_id.name))

        # Obtener facturas objetivo
        invoices = self._get_target_invoices()
        _logger.info(f"Facturas objetivo encontradas: {len(invoices)}")
        
        if not invoices:
            raise UserError(_('No se encontraron facturas para conciliar.\n\n'
                            'Verifique que existan facturas publicadas con estado de pago "No Pagado" o "Parcialmente Pagado".'))

        # Aplicar reglas
        all_matches = []
        
        if self.apply_direct_rules:
            _logger.info("Aplicando reglas directas...")
            direct_matches = self._apply_direct_rules(items, invoices)
            _logger.info(f"Reglas directas: {len(direct_matches)} matches encontrados")
            all_matches.extend(direct_matches)

        if self.apply_relation_rules:
            _logger.info("Aplicando reglas por relación...")
            relation_matches = self._apply_relation_rules(items, invoices)
            _logger.info(f"Reglas por relación: {len(relation_matches)} matches encontrados")
            all_matches.extend(relation_matches)

        _logger.info(f"Total de matches encontrados: {len(all_matches)}")

        # Clasificar resultados
        self._classify_results(items, all_matches)

        _logger.info("=" * 80)
        _logger.info("PROCESO DE CONCILIACIÓN COMPLETADO")
        _logger.info(f"Procesados: {self.total_processed}")
        _logger.info(f"Sugerencias: {self.total_suggestions}")
        _logger.info(f"Sin match: {self.total_unmatched}")
        _logger.info("=" * 80)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Conciliación Completada',
                'message': f'Procesados: {self.total_processed} | Sugerencias: {self.total_suggestions} | Sin match: {self.total_unmatched}',
                'type': 'success',
                'sticky': True,
            }
        }

    def _get_unreconciled_items(self):
        """Obtener items sin conciliar"""
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('company_id', '=', self.company_id.id),
        ]

        if self.only_unreconciled:
            domain.append(('is_reconciled', '=', False))

        if self.journal_ids:
            domain.append(('journal_id', 'in', self.journal_ids.ids))

        return self.env['account.bank.statement.line'].search(domain)

    def _get_target_invoices(self):
        """Obtener facturas objetivo para conciliar"""
        return self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('company_id', '=', self.company_id.id),
        ])

    def _apply_direct_rules(self, items, invoices):
        """Aplicar reglas directas"""
        rules = self.env['mx.reconcile.rule'].search([
            ('active', '=', True),
            ('source_model', '=', 'statement_line'),
        ], order='sequence, priority desc')

        all_matches = []
        for rule in rules:
            matches = rule.apply_rule(items, invoices)
            for source, invoice, score in matches:
                if score >= self.min_match_score:
                    all_matches.append({
                        'source': source,
                        'invoice': invoice,
                        'score': score,
                        'rule': rule,
                        'rule_type': 'direct',
                    })
        return all_matches

    def _apply_relation_rules(self, items, invoices):
        """Aplicar reglas por relación"""
        rules = self.env['mx.reconcile.relation.rule'].search([
            ('active', '=', True),
        ], order='sequence, priority desc')

        all_matches = []
        for rule in rules:
            matches = rule.apply_relation_rule(items, invoices)
            for source, invoice, score, related_doc in matches:
                if score >= self.min_match_score:
                    all_matches.append({
                        'source': source,
                        'invoice': invoice,
                        'score': score,
                        'rule': rule,
                        'rule_type': 'relation',
                        'related_doc': related_doc,
                    })
        return all_matches

    def _classify_results(self, items, matches):
        """Clasificar resultados en sugerencias y sin match"""
        matched_items = set()
        suggestions = self.env['account.bank.statement.line']

        for match in matches:
            source = match['source']
            matched_items.add(source.id)
            
            # Actualizar línea con sugerencia
            source.write({
                'suggested_invoice_id': match['invoice'].id,
                'reconcile_match_score': match['score'],
                'reconcile_rule_id': match['rule'].id if match['rule_type'] == 'direct' else False,
            })

            suggestions |= source

            # Crear log
            self.env['mx.reconcile.log'].create({
                'statement_line_id': source.id,
                'invoice_id': match['invoice'].id,
                'rule_id': match['rule'].id if match['rule_type'] == 'direct' else False,
                'relation_rule_id': match['rule'].id if match['rule_type'] == 'relation' else False,
                'rule_type': match['rule_type'],
                'match_score': match['score'],
                'state': 'confirmed' if match['score'] >= 95.0 else 'pending',
            })

        # Items sin match
        unmatched = items.filtered(lambda i: i.id not in matched_items)

        self.write({
            'suggestion_ids': [(6, 0, suggestions.ids)],
            'unmatched_ids': [(6, 0, unmatched.ids)],
        })

    def action_open_full_reconcile_view(self):
        """Abrir vista completa de conciliación OCA"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Conciliación Bancaria',
            'res_model': 'account.bank.statement.line',
            'view_mode': 'kanban,list',
            'view_id': self.env.ref('account_reconcile_oca.bank_statement_line_reconcile_view').id,
            'domain': [
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
                ('is_reconciled', '=', False),
            ],
            'context': {
                'search_default_not_reconciled': True,
                'view_ref': 'account_reconcile_oca.bank_statement_line_form_reconcile_view',
            },
            'target': 'current',
        }

    def action_review_suggestions(self):
        """Abrir vista OCA con sugerencias"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Revisar Sugerencias de Conciliación',
            'res_model': 'account.bank.statement.line',
            'view_mode': 'kanban',
            'view_id': self.env.ref('account_reconcile_oca.bank_statement_line_reconcile_view').id,
            'domain': [('id', 'in', self.suggestion_ids.ids)],
            'context': {
                'view_ref': 'account_reconcile_oca.bank_statement_line_form_reconcile_view',
            },
            'target': 'new',
        }

    def action_mark_non_deductible_wizard(self):
        """Abrir wizard para marcar no deducibles"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Marcar Pagos No Deducibles',
            'res_model': 'mx.mark.non.deductible.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_statement_line_ids': [(6, 0, self.unmatched_ids.ids)],
            }
        }
