# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import re
import logging

_logger = logging.getLogger(__name__)

class MxReconcileRelationRule(models.Model):
    """Reglas de conciliación a través de documentos relacionados"""
    _name = 'mx.reconcile.relation.rule'
    _description = 'Regla de Conciliación por Relación'
    _order = 'sequence, priority desc, name'

    name = fields.Char(
        string='Nombre de la Regla',
        required=True,
        help='Ejemplo: Buscar por Orden de Venta, Por Orden de Compra',
    )
    active = fields.Boolean(
        default=True,
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
    )

    # Campo en el pago/línea bancaria
    payment_field = fields.Selection([
        ('ref', 'Referencia'),
        ('payment_ref', 'Referencia de Pago'),
        ('narration', 'Descripción'),
    ], string='Campo en Pago', required=True, default='payment_ref')

    # Modelo intermedio
    relation_model = fields.Selection([
        ('sale.order', 'Orden de Venta'),
        ('purchase.order', 'Orden de Compra'),
        ('account.move', 'Factura'),
    ], string='Documento Intermedio', required=True)

    relation_search_field = fields.Selection([
        ('name', 'Número/Nombre'),
        ('client_order_ref', 'Referencia del Cliente'),
        ('partner_ref', 'Referencia del Partner'),
        ('ref', 'Referencia'),
    ], string='Campo de Búsqueda', required=True, default='name')

    # Relación del modelo intermedio a la factura
    invoice_relation_field = fields.Selection([
        ('invoice_ids', 'Facturas (invoice_ids)'),
        ('move_ids', 'Asientos (move_ids)'),
    ], string='Campo de Relación a Factura', required=True, default='invoice_ids')

    # Opciones de búsqueda
    search_type = fields.Selection([
        ('exact', 'Exacto'),
        ('contains', 'Contiene'),
        ('like', 'Similar'),
        ('regex', 'Expresión Regular'),
    ], string='Tipo de Búsqueda', required=True, default='contains')

    extract_pattern = fields.Char(
        string='Patrón de Extracción (Regex)',
        help='Regex para extraer valor del campo. Ejemplo: r"([A-Z]{2,4}\d{5,})" para extraer "DML02542"',
    )

    # Configuración
    auto_reconcile = fields.Boolean(
        string='Conciliar Automáticamente',
        default=False,
    )
    priority = fields.Selection([
        ('high', 'Alta'),
        ('medium', 'Media'),
        ('low', 'Baja'),
    ], string='Prioridad', default='medium', required=True)

    description = fields.Text(
        string='Descripción',
    )

    def apply_relation_rule(self, source_records, target_invoices):
        """
        Buscar matches a través de relaciones
        
        :param source_records: Pagos o líneas bancarias
        :param target_invoices: Facturas objetivo
        :return: Lista de tuplas (source_record, invoice, score, related_doc)
        """
        self.ensure_one()
        matches = []

        for source in source_records:
            # Obtener valor del campo en el pago
            source_value = getattr(source, self.payment_field, '') or ''
            if not source_value:
                continue

            # Extraer referencia si hay patrón
            reference = self._extract_reference(source_value)
            if not reference:
                continue

            # Buscar documentos relacionados
            related_docs = self._find_related_documents(reference)
            if not related_docs:
                continue

            # Obtener facturas desde documentos relacionados
            invoices = self._get_invoices_from_relation(related_docs)
            
            # Filtrar solo las facturas que están en target_invoices
            matching_invoices = invoices & target_invoices

            for invoice in matching_invoices:
                # Score basado en si encontramos el documento
                score = 85.0  # Score alto pero no 100% para revisión
                matches.append((source, invoice, score, related_docs[0]))

        return matches

    def _extract_reference(self, text):
        """Extraer referencia usando regex o búsqueda simple"""
        if not text:
            return None

        text = str(text)

        if self.extract_pattern:
            try:
                pattern = re.compile(self.extract_pattern, re.IGNORECASE)
                match = pattern.search(text)
                if match:
                    return match.group(1) if match.groups() else match.group(0)
            except re.error as e:
                _logger.error(f"Error en patrón regex: {e}")
                return None

        # Si no hay patrón, retornar el texto completo
        return text

    def _find_related_documents(self, reference):
        """Buscar documentos relacionados usando la referencia"""
        if not reference:
            return self.env[self.relation_model]

        domain = self._build_search_domain(reference)
        
        try:
            related_docs = self.env[self.relation_model].search(domain)
            return related_docs
        except Exception as e:
            _logger.error(f"Error buscando documentos relacionados: {e}")
            return self.env[self.relation_model]

    def _build_search_domain(self, reference):
        """Construir dominio de búsqueda según el tipo"""
        field = self.relation_search_field

        if self.search_type == 'exact':
            return [(field, '=', reference)]
        elif self.search_type == 'contains':
            return [(field, 'ilike', reference)]
        elif self.search_type == 'like':
            return [(field, 'like', f'%{reference}%')]
        elif self.search_type == 'regex':
            # Odoo no soporta regex directo, usar ilike como fallback
            return [(field, 'ilike', reference)]
        
        return [(field, '=', reference)]

    def _get_invoices_from_relation(self, related_docs):
        """Obtener facturas desde documentos relacionados"""
        if not related_docs:
            return self.env['account.move']

        invoices = self.env['account.move']
        
        for doc in related_docs:
            try:
                # Obtener facturas según el campo de relación
                if self.invoice_relation_field == 'invoice_ids':
                    invoices |= doc.invoice_ids
                elif self.invoice_relation_field == 'move_ids':
                    # Filtrar solo facturas (no otros tipos de asientos)
                    invoices |= doc.move_ids.filtered(
                        lambda m: m.move_type in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund')
                    )
            except Exception as e:
                _logger.error(f"Error obteniendo facturas de {doc}: {e}")
                continue

        return invoices

    def action_test_rule(self):
        """Probar la regla con datos de ejemplo"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Probar Regla: %s') % self.name,
            'res_model': 'mx.reconcile.relation.rule.test.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_rule_id': self.id},
        }
