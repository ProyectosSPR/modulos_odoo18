# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import re
from difflib import SequenceMatcher

class MxReconcileRuleTestWizard(models.TransientModel):
    """Wizard para probar reglas de conciliación con configuración flexible"""
    _name = 'mx.reconcile.rule.test.wizard'
    _description = 'Probar Regla de Conciliación'

    rule_id = fields.Many2one(
        'mx.reconcile.rule',
        string='Regla Base',
        required=True,
        readonly=True,
    )

    # ===== CONFIGURACIÓN FLEXIBLE =====
    # Campos editables para experimentar
    source_field = fields.Selection([
        ('ref', 'Referencia'),
        ('payment_ref', 'Referencia de Pago'),
        ('narration', 'Descripción'),
        ('partner_name', 'Nombre del Partner'),
    ], string='Campo Origen (Línea Bancaria)', required=True)

    target_field = fields.Selection([
        ('ref', 'Referencia'),
        ('name', 'Número'),
        ('l10n_mx_edi_cfdi_uuid', 'UUID Fiscal'),
        ('partner_name', 'Nombre del Cliente/Proveedor'),
        ('invoice_origin', 'Documento Origen'),
    ], string='Campo Destino (Factura)', required=True)

    match_type = fields.Selection([
        ('equals', 'Igualdad Exacta'),
        ('contains', 'Contiene'),
        ('like', 'Similar (con %)'),
        ('regex', 'Expresión Regular'),
    ], string='Tipo de Comparación', required=True, default='contains')

    min_similarity = fields.Float(
        string='Similitud Mínima (%)',
        default=80.0,
    )

    case_sensitive = fields.Boolean(
        string='Sensible a Mayúsculas',
        default=False,
    )

    # Filtros
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

    source_domain = fields.Char(
        string='Filtro de Origen',
        default="[]",
        help="Domain para filtrar líneas bancarias. Ejemplo: [('amount', '>', 1000)]",
    )
    target_domain = fields.Char(
        string='Filtro de Facturas',
        default="[]",
        help="Domain para filtrar facturas. Ejemplo: [('move_type', '=', 'out_invoice')]",
    )

    # Resultados
    total_source = fields.Integer(string='Total Líneas', readonly=True)
    total_target = fields.Integer(string='Total Facturas', readonly=True)
    total_matches = fields.Integer(string='Total Matches', readonly=True)
    match_percentage = fields.Float(string='% Match', readonly=True, compute='_compute_match_percentage')

    matched_line_ids = fields.Many2many(
        'account.bank.statement.line',
        'mx_rule_test_line_rel',
        'wizard_id',
        'line_id',
        string='Líneas con Match',
        readonly=True,
    )

    # Tabla de resultados detallados
    match_detail_ids = fields.One2many(
        'mx.reconcile.rule.test.match',
        'wizard_id',
        string='Detalles de Coincidencias',
    )

    @api.model
    def default_get(self, fields_list):
        """Cargar valores por defecto de la regla"""
        res = super().default_get(fields_list)
        if res.get('rule_id'):
            rule = self.env['mx.reconcile.rule'].browse(res['rule_id'])
            res.update({
                'source_field': rule.source_field,
                'target_field': rule.target_field,
                'match_type': rule.match_type,
                'min_similarity': rule.min_similarity,
                'case_sensitive': rule.case_sensitive,
            })
        return res

    @api.depends('total_source', 'total_matches')
    def _compute_match_percentage(self):
        for wizard in self:
            wizard.match_percentage = (wizard.total_matches / wizard.total_source * 100) if wizard.total_source else 0

    def action_test_rule(self):
        """Ejecutar test con la configuración actual"""
        self.ensure_one()

        # Limpiar resultados anteriores
        self.match_detail_ids.unlink()

        # Obtener registros
        source_domain = self._get_source_domain()
        source_records = self.env['account.bank.statement.line'].search(source_domain)

        target_domain = self._get_target_domain()
        target_records = self.env['account.move'].search(target_domain)

        # Buscar matches usando la configuración del wizard
        matches = self._find_matches(source_records, target_records)

        # Crear detalles de matches
        match_details = []
        matched_line_ids = []
        for source, target, score in matches:
            matched_line_ids.append(source.id)

            # Actualizar línea con sugerencia
            source.write({
                'suggested_invoice_id': target.id,
                'reconcile_match_score': score,
            })

            # Crear detalle
            match_details.append((0, 0, {
                'line_id': source.id,
                'invoice_id': target.id,
                'match_score': score,
                'source_value': self._get_field_value(source, self.source_field),
                'target_value': self._get_field_value(target, self.target_field),
            }))

        self.write({
            'total_source': len(source_records),
            'total_target': len(target_records),
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

    def _get_source_domain(self):
        """Construir domain para líneas bancarias"""
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

    def _find_matches(self, source_records, target_records):
        """Buscar matches con la configuración actual"""
        matches = []
        for source in source_records:
            source_value = self._get_field_value(source, self.source_field)
            if not source_value:
                continue

            source_value = self._normalize_value(source_value)

            for target in target_records:
                target_value = self._get_field_value(target, self.target_field)
                if not target_value:
                    continue

                target_value = self._normalize_value(target_value)
                score = self._compare_values(source_value, target_value)

                if score >= self.min_similarity:
                    matches.append((source, target, score))

        return matches

    def _get_field_value(self, record, field_name):
        """Obtener valor del campo"""
        if field_name == 'partner_name':
            return record.partner_id.name if record.partner_id else ''
        return getattr(record, field_name, '') or ''

    def _normalize_value(self, value):
        """Normalizar valor"""
        if not value:
            return ''
        value = str(value)
        if not self.case_sensitive:
            value = value.lower()
        return value

    def _compare_values(self, source_value, target_value):
        """Comparar dos valores"""
        if self.match_type == 'equals':
            return 100.0 if source_value == target_value else 0.0
        elif self.match_type == 'contains':
            if source_value in target_value or target_value in source_value:
                match_len = min(len(source_value), len(target_value))
                max_len = max(len(source_value), len(target_value))
                return (match_len / max_len) * 100.0
            return 0.0
        elif self.match_type == 'like':
            ratio = SequenceMatcher(None, source_value, target_value).ratio()
            return ratio * 100.0
        elif self.match_type == 'regex':
            # Búsqueda simple por contención para regex
            if source_value in target_value or target_value in source_value:
                return 90.0
            return 0.0
        return 0.0

    def action_open_reconcile_view(self):
        """Abrir vista de conciliación OCA"""
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


class MxReconcileRuleTestMatch(models.TransientModel):
    """Detalle de cada match encontrado"""
    _name = 'mx.reconcile.rule.test.match'
    _description = 'Detalle de Match de Prueba'

    wizard_id = fields.Many2one('mx.reconcile.rule.test.wizard', required=True, ondelete='cascade')
    line_id = fields.Many2one('account.bank.statement.line', string='Línea Bancaria', required=True)
    invoice_id = fields.Many2one('account.move', string='Factura', required=True)
    match_score = fields.Float(string='Score %', digits=(5, 2))
    source_value = fields.Char(string='Valor Origen')
    target_value = fields.Char(string='Valor Destino')

    # Campos relacionados para mostrar en la tabla
    line_date = fields.Date(related='line_id.date', string='Fecha')
    line_amount = fields.Monetary(related='line_id.amount', string='Monto', currency_field='currency_id')
    line_ref = fields.Char(related='line_id.payment_ref', string='Referencia')
    invoice_name = fields.Char(related='invoice_id.name', string='Factura')
    invoice_amount = fields.Monetary(related='invoice_id.amount_total', string='Total Factura', currency_field='currency_id')
    currency_id = fields.Many2one(related='line_id.currency_id')
