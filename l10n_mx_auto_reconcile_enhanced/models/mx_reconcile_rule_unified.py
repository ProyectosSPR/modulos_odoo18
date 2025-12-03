# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import re
import logging
from difflib import SequenceMatcher

_logger = logging.getLogger(__name__)

class MxReconcileRuleUnified(models.Model):
    """Sistema unificado de conciliación - Más simple y flexible"""
    _name = 'mx.reconcile.rule.unified'
    _description = 'Regla de Conciliación Unificada'
    _order = 'sequence, name'

    name = fields.Char(
        string='Nombre de la Regla',
        required=True,
        help='Ejemplo: Match por Orden de Venta, Match Directo por Referencia',
    )
    active = fields.Boolean(default=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    # ============ PASO 1: ¿Qué buscar en el Pago? ============
    payment_search_field_id = fields.Many2one(
        'ir.model.fields',
        string='Campo del Pago a Buscar',
        required=True,
        ondelete='set null',
        domain="[('model', 'in', ['account.payment', 'account.bank.statement.line']), "
               "('ttype', 'in', ['char', 'text', 'many2one'])]",
        help='¿En qué campo del pago buscar? Ej: payment_ref, narration, ref',
    )

    extract_pattern = fields.Char(
        string='Patrón de Extracción (Opcional)',
        help='Regex para extraer valor. Ej: r"SO(\d+)" extrae "001234" de "Pago SO001234"',
    )

    # ============ PASO 2: ¿Buscar Directo o por Relación? ============
    match_mode = fields.Selection([
        ('direct', 'Directo: Pago → Factura'),
        ('relation', 'Por Relación: Pago → Documento → Factura'),
        ('relation_reverse', 'Inverso: Documento → Pago → Factura'),
    ], string='Modo de Búsqueda', required=True, default='direct')

    # --- Para búsqueda DIRECTA ---
    invoice_search_field_id = fields.Many2one(
        'ir.model.fields',
        string='Campo de la Factura',
        ondelete='set null',
        domain="[('model', '=', 'account.move'), "
               "('ttype', 'in', ['char', 'text', 'many2one'])]",
        help='Campo de la factura donde buscar la coincidencia',
    )

    # --- Para búsqueda por RELACIÓN ---
    relation_model = fields.Selection([
        ('sale.order', 'Orden de Venta'),
        ('purchase.order', 'Orden de Compra'),
    ], string='Documento Intermedio')

    relation_search_field_id = fields.Many2one(
        'ir.model.fields',
        string='Campo del Documento Intermedio',
        ondelete='set null',
        domain="[('model', '=', relation_model)]",
        help='Campo del documento intermedio donde buscar. Ej: name, client_order_ref',
    )

    relation_to_invoice_field = fields.Char(
        string='Campo a Facturas',
        default='invoice_ids',
        help='Campo que relaciona el documento intermedio con facturas. '
             'Sale Order: invoice_ids, Purchase Order: invoice_ids',
    )

    # ============ PASO 3: ¿Cómo Comparar? ============
    comparison_operator = fields.Selection([
        ('=', '= Igual'),
        ('ilike', 'Contiene (ilike)'),
        ('like', 'Like %valor%'),
        ('in', 'Está en'),
        ('=ilike', '= o Contiene'),
    ], string='Operador de Comparación', required=True, default='ilike')

    case_sensitive = fields.Boolean(string='Sensible a Mayúsculas', default=False)
    remove_spaces = fields.Boolean(string='Eliminar Espacios', default=True)

    # ============ PASO 4: Filtros Adicionales ============
    payment_domain = fields.Char(
        string='Filtro de Pagos',
        default='[]',
        help='Filtro adicional para pagos. Ej: [(\'amount\', \'>\', 1000)]',
    )

    invoice_domain = fields.Char(
        string='Filtro de Facturas',
        default='[]',
        help='Filtro adicional para facturas. Ej: [(\'move_type\', \'=\', \'out_invoice\')]',
    )

    relation_domain = fields.Char(
        string='Filtro de Documentos Intermedios',
        default='[]',
        help='Filtro para órdenes. Ej: [(\'state\', \'=\', \'sale\')]',
    )

    # ============ Configuración ============
    priority = fields.Selection([
        ('high', 'Alta'),
        ('medium', 'Media'),
        ('low', 'Baja'),
    ], default='medium', required=True)

    auto_reconcile = fields.Boolean(
        string='Conciliar Automáticamente',
        default=False,
        help='Si el score es >= 95%, conciliar automáticamente',
    )

    min_score = fields.Float(
        string='Score Mínimo (%)',
        default=70.0,
        help='Score mínimo para considerar un match válido',
    )

    description = fields.Text(string='Descripción')

    @api.constrains('match_mode', 'invoice_search_field_id', 'relation_model')
    def _check_configuration(self):
        for rule in self:
            if rule.match_mode == 'direct' and not rule.invoice_search_field_id:
                raise ValidationError("En modo Directo, debes especificar el campo de la factura")
            if rule.match_mode in ('relation', 'relation_reverse') and not rule.relation_model:
                raise ValidationError("En modo Relación, debes especificar el documento intermedio")

    def apply_rule(self, payments, invoices):
        """
        Aplicar regla unificada

        :param payments: Pagos o líneas bancarias
        :param invoices: Facturas objetivo
        :return: Lista de tuplas (payment, invoice, score, extra_info)
        """
        self.ensure_one()

        _logger.info(f"[REGLA UNIFICADA] Aplicando '{self.name}' - Modo: {self.match_mode}")
        _logger.info(f"  Pagos: {len(payments)}, Facturas: {len(invoices)}")

        # Aplicar filtros a pagos
        payments = self._apply_domain_filter(payments, self.payment_domain)

        # Aplicar filtros a facturas
        invoices = self._apply_domain_filter(invoices, self.invoice_domain)

        _logger.info(f"  Después de filtros - Pagos: {len(payments)}, Facturas: {len(invoices)}")

        if self.match_mode == 'direct':
            return self._apply_direct_match(payments, invoices)
        elif self.match_mode == 'relation':
            return self._apply_relation_match(payments, invoices)
        elif self.match_mode == 'relation_reverse':
            return self._apply_relation_reverse_match(payments, invoices)

        return []

    def _apply_direct_match(self, payments, invoices):
        """Búsqueda directa: Pago → Factura"""
        matches = []

        for payment in payments:
            # Obtener valor del campo del pago
            payment_value = self._get_field_value(payment, self.payment_search_field_id)
            if not payment_value:
                continue

            # Extraer valor si hay patrón
            if self.extract_pattern:
                payment_value = self._extract_with_pattern(payment_value)
                if not payment_value:
                    continue

            # Normalizar
            payment_value = self._normalize_value(payment_value)

            _logger.debug(f"Buscando coincidencia para: {payment_value}")

            # Buscar en facturas
            for invoice in invoices:
                invoice_value = self._get_field_value(invoice, self.invoice_search_field_id)
                if not invoice_value:
                    continue

                invoice_value = self._normalize_value(invoice_value)

                # Comparar
                score = self._compare_values(payment_value, invoice_value)

                if score >= self.min_score:
                    _logger.info(f"  ✓ Match: {payment.id} → {invoice.id} (score: {score}%)")
                    matches.append((payment, invoice, score, f'Directo: {payment_value} = {invoice_value}'))

        _logger.info(f"[DIRECTO] {len(matches)} matches encontrados")
        return matches

    def _apply_relation_match(self, payments, invoices):
        """Búsqueda por relación: Pago → Documento → Factura"""
        matches = []

        for payment in payments:
            # Obtener valor del campo del pago
            payment_value = self._get_field_value(payment, self.payment_search_field_id)
            if not payment_value:
                continue

            # Extraer valor si hay patrón
            if self.extract_pattern:
                payment_value = self._extract_with_pattern(payment_value)
                if not payment_value:
                    continue

            # Normalizar
            payment_value = self._normalize_value(payment_value)

            _logger.debug(f"Buscando {self.relation_model} con: {payment_value}")

            # Construir dominio de búsqueda para documento intermedio
            search_field_name = self.relation_search_field_id.name if self.relation_search_field_id else 'name'
            domain = self._build_search_domain(search_field_name, payment_value)

            # Agregar filtro adicional de documentos
            domain = domain + self._parse_domain(self.relation_domain)

            # Buscar documentos intermedios
            related_docs = self.env[self.relation_model].search(domain)

            if not related_docs:
                _logger.debug(f"  No se encontraron {self.relation_model}")
                continue

            _logger.debug(f"  Encontrados {len(related_docs)} documentos: {related_docs.mapped('name')}")

            # Obtener facturas desde documentos intermedios
            relation_invoices = self.env['account.move']
            for doc in related_docs:
                doc_invoices = getattr(doc, self.relation_to_invoice_field, self.env['account.move'])
                relation_invoices |= doc_invoices

            # Filtrar solo facturas válidas (no borradores, etc)
            relation_invoices = relation_invoices.filtered(
                lambda inv: inv.move_type in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund')
            )

            # Intersección con facturas objetivo
            matching_invoices = relation_invoices & invoices

            _logger.debug(f"  Facturas relacionadas: {len(relation_invoices)}, En target: {len(matching_invoices)}")

            for invoice in matching_invoices:
                score = 85.0  # Score alto por match por relación
                doc_info = f"{self.relation_model}: {related_docs[0].name}"
                _logger.info(f"  ✓ Match por relación: {payment.id} → {invoice.id} via {doc_info}")
                matches.append((payment, invoice, score, doc_info))

        _logger.info(f"[RELACIÓN] {len(matches)} matches encontrados")
        return matches

    def _apply_relation_reverse_match(self, payments, invoices):
        """
        Búsqueda inversa: Documento → Pago → Factura

        Flujo:
        1. Buscar documentos (órdenes de venta/compra) filtrados por relation_domain
        2. Para cada documento, buscar pagos que referencien ese documento
        3. Obtener las facturas del documento
        4. Hacer match: pago encontrado → factura del documento
        """
        matches = []

        _logger.info(f"[RELACIÓN INVERSA] Buscando desde {self.relation_model} → Pagos")

        # Construir dominio para buscar documentos
        order_domain = self._parse_domain(self.relation_domain)

        # Buscar documentos intermedios (órdenes)
        related_docs = self.env[self.relation_model].search(order_domain)

        if not related_docs:
            _logger.info(f"  No se encontraron {self.relation_model} con el filtro")
            return matches

        _logger.info(f"  Encontrados {len(related_docs)} documentos: {related_docs.mapped('name')}")

        # Para cada documento
        for doc in related_docs:
            # Obtener el valor del campo del documento que vamos a buscar en los pagos
            search_field_name = self.relation_search_field_id.name if self.relation_search_field_id else 'name'
            doc_value = getattr(doc, search_field_name, '')

            if not doc_value:
                _logger.debug(f"  Documento {doc.name} no tiene valor en campo {search_field_name}")
                continue

            doc_value = self._normalize_value(str(doc_value))
            _logger.debug(f"  Buscando pagos que referencien: {doc_value}")

            # Buscar pagos que contengan esta referencia
            matching_payments = []
            for payment in payments:
                payment_value = self._get_field_value(payment, self.payment_search_field_id)
                if not payment_value:
                    continue

                # Extraer valor si hay patrón
                if self.extract_pattern:
                    extracted = self._extract_with_pattern(payment_value)
                    if extracted:
                        payment_value = extracted

                payment_value = self._normalize_value(payment_value)

                # Comparar
                score = self._compare_values(doc_value, payment_value)
                if score >= self.min_score:
                    matching_payments.append((payment, score))
                    _logger.debug(f"    ✓ Pago {payment.id} ({payment.payment_ref}) score: {score}%")

            if not matching_payments:
                _logger.debug(f"  No se encontraron pagos para documento {doc.name}")
                continue

            # Obtener facturas del documento
            doc_invoices = getattr(doc, self.relation_to_invoice_field, self.env['account.move'])

            # Filtrar solo facturas válidas
            doc_invoices = doc_invoices.filtered(
                lambda inv: inv.move_type in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund')
            )

            # Intersección con facturas objetivo
            matching_invoices = doc_invoices & invoices

            if not matching_invoices:
                _logger.debug(f"  Documento {doc.name} no tiene facturas en el target")
                continue

            _logger.info(f"  Documento {doc.name}: {len(matching_payments)} pagos, {len(matching_invoices)} facturas")

            # Crear matches: cada pago encontrado con cada factura del documento
            for payment, pay_score in matching_payments:
                for invoice in matching_invoices:
                    final_score = pay_score  # Usar el score de comparación
                    doc_info = f"Orden {doc.name} → {invoice.name}"
                    _logger.info(f"    ✓ Match inverso: {payment.id} → {invoice.id} via {doc_info}")
                    matches.append((payment, invoice, final_score, doc_info))

        _logger.info(f"[RELACIÓN INVERSA] {len(matches)} matches encontrados")
        return matches

    def _get_field_value(self, record, field_id):
        """Obtener valor del campo"""
        if not field_id:
            return ''

        field_name = field_id.name
        value = getattr(record, field_name, False)

        # Si es Many2one, obtener el nombre
        if field_id.ttype == 'many2one' and value:
            return value.name

        return str(value) if value else ''

    def _extract_with_pattern(self, text):
        """Extraer valor usando regex"""
        if not text or not self.extract_pattern:
            return text

        try:
            pattern = re.compile(self.extract_pattern, re.IGNORECASE)
            match = pattern.search(str(text))
            if match:
                # Si hay grupos, tomar el primero
                return match.group(1) if match.groups() else match.group(0)
        except re.error as e:
            _logger.error(f"Error en patrón regex '{self.extract_pattern}': {e}")

        return None

    def _normalize_value(self, value):
        """Normalizar valor para comparación"""
        if not value:
            return ''

        value = str(value)

        if not self.case_sensitive:
            value = value.lower()

        if self.remove_spaces:
            value = value.replace(' ', '')

        return value.strip()

    def _build_search_domain(self, field_name, value):
        """Construir dominio de búsqueda según operador"""
        if self.comparison_operator == '=':
            return [(field_name, '=', value)]
        elif self.comparison_operator == 'ilike':
            return [(field_name, 'ilike', value)]
        elif self.comparison_operator == 'like':
            return [(field_name, 'like', f'%{value}%')]
        elif self.comparison_operator == 'in':
            return [(field_name, 'in', [value])]
        elif self.comparison_operator == '=ilike':
            return ['|', (field_name, '=', value), (field_name, 'ilike', value)]

        return [(field_name, '=', value)]

    def _compare_values(self, val1, val2):
        """Comparar dos valores y retornar score 0-100"""
        if not val1 or not val2:
            return 0.0

        # Igualdad exacta
        if val1 == val2:
            return 100.0

        # Contiene
        if val1 in val2 or val2 in val1:
            match_len = min(len(val1), len(val2))
            max_len = max(len(val1), len(val2))
            return (match_len / max_len) * 100.0

        # Similitud fuzzy
        ratio = SequenceMatcher(None, val1, val2).ratio()
        return ratio * 100.0

    def _apply_domain_filter(self, records, domain_str):
        """Aplicar filtro de domain a recordset"""
        if not domain_str or domain_str == '[]':
            return records

        try:
            domain = eval(domain_str)
            if not domain:
                return records

            # Filtrar usando el domain
            return records.filtered(lambda r: self._match_domain(r, domain))
        except Exception as e:
            _logger.warning(f"Error aplicando domain filter '{domain_str}': {e}")
            return records

    def _parse_domain(self, domain_str):
        """Convertir string a domain list"""
        if not domain_str or domain_str == '[]':
            return []

        try:
            return eval(domain_str)
        except:
            return []

    def _match_domain(self, record, domain):
        """Evaluar si un registro cumple con un domain"""
        for condition in domain:
            if len(condition) != 3:
                continue

            field, operator, value = condition
            record_value = getattr(record, field, None)

            if operator == '=' and record_value != value:
                return False
            elif operator == '!=' and record_value == value:
                return False
            elif operator == '>' and not (record_value and record_value > value):
                return False
            elif operator == '>=' and not (record_value and record_value >= value):
                return False
            elif operator == '<' and not (record_value and record_value < value):
                return False
            elif operator == '<=' and not (record_value and record_value <= value):
                return False
            elif operator == 'in' and record_value not in value:
                return False
            elif operator == 'not in' and record_value in value:
                return False
            elif operator == 'ilike':
                if not (record_value and str(value).lower() in str(record_value).lower()):
                    return False

        return True

    def action_test_rule(self):
        """Abrir wizard de prueba"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Probar Regla',
            'res_model': 'mx.reconcile.rule.test.wizard.unified',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_rule_id': self.id,
            },
        }
