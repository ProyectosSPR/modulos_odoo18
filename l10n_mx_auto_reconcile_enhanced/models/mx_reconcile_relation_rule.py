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
    payment_field_id = fields.Many2one(
        'ir.model.fields',
        string='Campo en Pago',
        required=True,
        ondelete='cascade',
        domain="[('model', 'in', ['account.payment', 'account.bank.statement.line']), ('ttype', 'in', ['char', 'text'])]",
        help='Campo del pago o línea bancaria donde buscar la referencia',
    )

    # Modelo intermedio
    relation_model = fields.Selection([
        ('sale.order', 'Orden de Venta'),
        ('purchase.order', 'Orden de Compra'),
        ('account.move', 'Factura'),
    ], string='Documento Intermedio', required=True)

    relation_search_field_id = fields.Many2one(
        'ir.model.fields',
        string='Campo de Búsqueda',
        required=True,
        ondelete='cascade',
        domain="[('model', '=', relation_model), ('ttype', 'in', ['char', 'text', 'many2one'])]",
        help='Campo del documento intermedio donde buscar la coincidencia',
    )

    # Relación del modelo intermedio a la factura
    invoice_relation_field_id = fields.Many2one(
        'ir.model.fields',
        string='Campo de Relación a Factura',
        required=True,
        ondelete='cascade',
        domain="[('model', '=', relation_model), ('ttype', 'in', ['one2many', 'many2many']), ('relation', '=', 'account.move')]",
        help='Campo del documento intermedio que contiene las facturas relacionadas',
    )

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

    # Filtros Domain
    source_domain_filter = fields.Char(
        string='Filtro de Pagos',
        default='[]',
        help='Domain para filtrar pagos/líneas bancarias',
    )
    
    relation_domain_filter = fields.Char(
        string='Filtro de Documentos',
        default='[]',
        help='Domain para filtrar documentos intermedios (ej. solo órdenes confirmadas)',
    )

    @api.constrains('min_similarity')

    def apply_relation_rule(self, source_records, target_invoices):
        """
        Buscar matches a través de relaciones
        
        :param source_records: Pagos o líneas bancarias
        :param target_invoices: Facturas objetivo
        :return: Lista de tuplas (source_record, invoice, score, related_doc)
        """
        self.ensure_one()
        matches = []

        _logger.info(f"Aplicando regla por relación '{self.name}' - Source: {len(source_records)}, Target: {len(target_invoices)}")

        # Aplicar filtro de pagos si existe
        if self.source_domain_filter and self.source_domain_filter != '[]':
            try:
                domain_filter = eval(self.source_domain_filter)
                # Usar search en lugar de filtered_domain
                filtered_ids = source_records.filtered(lambda r: self._match_domain(r, domain_filter))
                source_records = filtered_ids
            except Exception as e:
                _logger.warning(f"Error aplicando filtro de pagos: {e}")

        for source in source_records:
            # Obtener valor del campo en el pago
            source_value = self._get_field_value(source, self.payment_field_id)
            if not source_value:
                continue

            # Extraer referencia si hay patrón
            reference = self._extract_reference(source_value)
            if not reference:
                _logger.debug(f"No se pudo extraer referencia de: {source_value}")
                continue

            _logger.debug(f"Referencia extraída: {reference}")

            # Buscar documentos relacionados
            related_docs = self._find_related_documents(reference)
            if not related_docs:
                _logger.debug(f"No se encontraron documentos relacionados para: {reference}")
                continue

            _logger.debug(f"Documentos relacionados encontrados: {len(related_docs)}")

            # Obtener facturas desde documentos relacionados
            invoices = self._get_invoices_from_relation(related_docs)
            _logger.debug(f"Facturas desde relación: {len(invoices)}")
            
            # Filtrar solo las facturas que están en target_invoices
            matching_invoices = invoices & target_invoices

            for invoice in matching_invoices:
                # Score basado en si encontramos el documento
                score = 85.0  # Score alto pero no 100% para revisión
                _logger.debug(f"Match por relación: {source.id} -> {invoice.id} (score: {score})")
                matches.append((source, invoice, score, related_docs[0]))

        _logger.info(f"Regla por relación '{self.name}' completada: {len(matches)} matches encontrados")
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
        
        # Agregar filtro de documentos si existe
        if self.relation_domain_filter and self.relation_domain_filter != '[]':
            try:
                extra_domain = eval(self.relation_domain_filter)
                domain = domain + extra_domain
            except Exception as e:
                _logger.warning(f"Error aplicando filtro de documentos: {e}")
        
        try:
            related_docs = self.env[self.relation_model].search(domain)
            return related_docs
        except Exception as e:
            _logger.error(f"Error buscando documentos relacionados: {e}")
            return self.env[self.relation_model]

    def _build_search_domain(self, reference):
        """Construir dominio de búsqueda según el tipo"""
        field_name = self.relation_search_field_id.name if self.relation_search_field_id else 'name'

        if self.search_type == 'exact':
            return [(field_name, '=', reference)]
        elif self.search_type == 'contains':
            return [(field_name, 'ilike', reference)]
        elif self.search_type == 'like':
            return [(field_name, 'like', f'%{reference}%')]
        elif self.search_type == 'regex':
            # Odoo no soporta regex directo, usar ilike como fallback
            return [(field_name, 'ilike', reference)]
        
        return [(field_name, '=', reference)]

    def _get_invoices_from_relation(self, related_docs):
        """Obtener facturas desde documentos relacionados"""
        if not related_docs:
            return self.env['account.move']

        invoices = self.env['account.move']
        relation_field_name = self.invoice_relation_field_id.name if self.invoice_relation_field_id else 'invoice_ids'
        
        for doc in related_docs:
            try:
                # Obtener facturas según el campo de relación
                related_invoices = getattr(doc, relation_field_name, self.env['account.move'])
                
                # Filtrar solo facturas (no otros tipos de asientos)
                if relation_field_name in ['move_ids', 'invoice_ids']:
                    invoices |= related_invoices.filtered(
                        lambda m: m.move_type in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund')
                    )
                else:
                    invoices |= related_invoices
            except Exception as e:
                _logger.error(f"Error obteniendo facturas de {doc}: {e}")
                continue

        return invoices

    def _match_domain(self, record, domain):
        """Evaluar si un registro cumple con un domain (copiado de mx.reconcile.rule)"""
        for condition in domain:
            if len(condition) != 3:
                continue
            field, operator, value = condition
            record_value = getattr(record, field, None)
            
            if operator == '=':
                if record_value != value:
                    return False
            elif operator == '!=':
                if record_value == value:
                    return False
            elif operator == 'in':
                if record_value not in value:
                    return False
            elif operator == 'not in':
                if record_value in value:
                    return False
            # ... otros operadores básicos ...
        return True

