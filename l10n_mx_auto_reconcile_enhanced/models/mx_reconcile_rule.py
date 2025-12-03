# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import re
import logging
from difflib import SequenceMatcher

_logger = logging.getLogger(__name__)

class MxReconcileRule(models.Model):
    """Reglas de conciliación directa entre pagos y facturas"""
    _name = 'mx.reconcile.rule'
    _description = 'Regla de Conciliación Directa'
    _order = 'sequence, priority desc, name'

    name = fields.Char(
        string='Nombre de la Regla',
        required=True,
        help='Ejemplo: Match por Referencia, UUID en Descripción',
    )
    active = fields.Boolean(
        default=True,
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de ejecución (menor = primero)',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
    )

    # Configuración de campos
    source_model = fields.Selection([
        ('payment', 'Pago'),
        ('statement_line', 'Línea Bancaria'),
    ], string='Modelo Origen', required=True, default='statement_line')

    source_field_id = fields.Many2one(
        'ir.model.fields',
        string='Campo Origen',
        required=True,
        domain="[('model', '=', source_model_name), ('ttype', 'in', ['char', 'text', 'many2one'])]",
        help='Campo del pago o línea bancaria a comparar',
    )
    
    source_model_name = fields.Char(
        compute='_compute_model_names',
        store=True,
    )

    target_model = fields.Selection([
        ('invoice', 'Factura'),
    ], string='Modelo Destino', required=True, default='invoice')

    target_field_id = fields.Many2one(
        'ir.model.fields',
        string='Campo Destino',
        required=True,
        domain="[('model', '=', target_model_name), ('ttype', 'in', ['char', 'text', 'many2one'])]",
        help='Campo de la factura a comparar',
    )
    
    target_model_name = fields.Char(
        compute='_compute_model_names',
        store=True,
    )

    # Tipo de comparación
    match_type = fields.Selection([
        ('equals', 'Igualdad Exacta'),
        ('contains', 'Contiene'),
        ('like', 'Similar (con %)'),
        ('in', 'Está en'),
        ('regex', 'Expresión Regular'),
    ], string='Tipo de Comparación', required=True, default='equals')

    case_sensitive = fields.Boolean(
        string='Sensible a Mayúsculas',
        default=False,
    )
    remove_spaces = fields.Boolean(
        string='Eliminar Espacios',
        default=True,
        help='Eliminar espacios antes de comparar',
    )
    remove_special_chars = fields.Boolean(
        string='Eliminar Caracteres Especiales',
        default=False,
        help='Eliminar caracteres especiales como -, _, .',
    )

    # Opciones avanzadas
    min_similarity = fields.Float(
        string='Similitud Mínima (%)',
        default=80.0,
        help='Para fuzzy matching (0-100)',
    )
    regex_pattern = fields.Char(
        string='Patrón Regex',
        help='Expresión regular para extraer valor. Ejemplo: r"orden\s+(\w+)"',
    )

    # Resultados
    priority = fields.Selection([
        ('high', 'Alta'),
        ('medium', 'Media'),
        ('low', 'Baja'),
    ], string='Prioridad', default='medium', required=True)

    auto_reconcile = fields.Boolean(
        string='Conciliar Automáticamente',
        default=False,
        help='Si es True, concilia automáticamente cuando el score sea >= 95%',
    )
    require_manual_review = fields.Boolean(
        string='Requiere Revisión Manual',
        default=True,
        help='Marcar para revisión manual incluso si hay match',
    )

    description = fields.Text(
        string='Descripción',
    )

    # Filtros Domain
    source_domain_filter = fields.Char(
        string='Filtro Adicional de Origen',
        default='[]',
        help='Domain para filtrar automáticamente registros origen. Ejemplo: [(\'amount\', \'>\', 1000)]',
    )
    target_domain_filter = fields.Char(
        string='Filtro Adicional de Facturas',
        default='[]',
        help='Domain para filtrar automáticamente facturas. Ejemplo: [(\'move_type\', \'=\', \'out_invoice\')]',
    )

    @api.depends('source_model', 'target_model')
    def _compute_model_names(self):
        for record in self:
            if record.source_model == 'payment':
                record.source_model_name = 'account.payment'
            elif record.source_model == 'statement_line':
                record.source_model_name = 'account.bank.statement.line'
            else:
                record.source_model_name = False
                
            if record.target_model == 'invoice':
                record.target_model_name = 'account.move'
            else:
                record.target_model_name = False

    @api.constrains('min_similarity')
    def _check_min_similarity(self):
        for record in self:
            if not (0 <= record.min_similarity <= 100):
                raise ValidationError(_('La similitud mínima debe estar entre 0 y 100'))

    def apply_rule(self, source_records, target_records):
        """
        Aplicar esta regla y retornar matches

        :param source_records: Pagos o líneas bancarias
        :param target_records: Facturas
        :return: Lista de tuplas (source_record, target_record, score)
        """
        self.ensure_one()
        matches = []

        _logger.info(f"Aplicando regla '{self.name}' - Source: {len(source_records)}, Target: {len(target_records)}")

        # Aplicar filtros domain si existen
        if self.source_domain_filter and self.source_domain_filter != '[]':
            try:
                domain_filter = eval(self.source_domain_filter)
                # Usar search en lugar de filtered_domain
                filtered_ids = source_records.filtered(lambda r: self._match_domain(r, domain_filter))
                source_records = filtered_ids
                _logger.info(f"Filtro de origen aplicado: {len(source_records)} registros después del filtro")
            except Exception as e:
                _logger.warning(f"Error aplicando filtro de origen: {e}")

        if self.target_domain_filter and self.target_domain_filter != '[]':
            try:
                domain_filter = eval(self.target_domain_filter)
                # Usar search en lugar de filtered_domain
                filtered_ids = target_records.filtered(lambda r: self._match_domain(r, domain_filter))
                target_records = filtered_ids
                _logger.info(f"Filtro de destino aplicado: {len(target_records)} registros después del filtro")
            except Exception as e:
                _logger.warning(f"Error aplicando filtro de destino: {e}")

        for source in source_records:
            source_value = self._get_field_value(source, self.source_field_id)
            if not source_value:
                continue

            source_value = self._normalize_value(source_value)

            for target in target_records:
                target_value = self._get_field_value(target, self.target_field_id)
                if not target_value:
                    continue

                target_value = self._normalize_value(target_value)

                score = self._compare_values(source_value, target_value)
                if score >= self.min_similarity:
                    _logger.debug(f"Match encontrado: {source.id} -> {target.id} (score: {score})")
                    matches.append((source, target, score))

        _logger.info(f"Regla '{self.name}' completada: {len(matches)} matches encontrados")
        return matches

    def _match_domain(self, record, domain):
        """Evaluar si un registro cumple con un domain"""
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
            elif operator == '>':
                if not (record_value and record_value > value):
                    return False
            elif operator == '>=':
                if not (record_value and record_value >= value):
                    return False
            elif operator == '<':
                if not (record_value and record_value < value):
                    return False
            elif operator == '<=':
                if not (record_value and record_value <= value):
                    return False
        return True

    def _get_field_value(self, record, field_id):
        """Obtener valor del campo dinámicamente"""
        if not field_id:
            return ''
            
        field_name = field_id.name
        
        # Manejar campos Many2one (obtener el nombre)
        if field_id.ttype == 'many2one':
            related_record = getattr(record, field_name, False)
            return related_record.name if related_record else ''
        
        # Campos normales
        return getattr(record, field_name, '') or ''

    def _normalize_value(self, value):
        """Normalizar valor según configuración"""
        if not value:
            return ''

        value = str(value)

        if not self.case_sensitive:
            value = value.lower()

        if self.remove_spaces:
            value = value.replace(' ', '')

        if self.remove_special_chars:
            value = re.sub(r'[^a-zA-Z0-9]', '', value)

        return value

    def _compare_values(self, source_value, target_value):
        """
        Comparar dos valores según match_type
        
        :return: Score de 0-100
        """
        if self.match_type == 'equals':
            return 100.0 if source_value == target_value else 0.0

        elif self.match_type == 'contains':
            if source_value in target_value or target_value in source_value:
                # Score basado en la longitud de coincidencia
                match_len = min(len(source_value), len(target_value))
                max_len = max(len(source_value), len(target_value))
                return (match_len / max_len) * 100.0
            return 0.0

        elif self.match_type == 'like':
            # Usar SequenceMatcher para similitud
            ratio = SequenceMatcher(None, source_value, target_value).ratio()
            return ratio * 100.0

        elif self.match_type == 'in':
            # Buscar palabras completas
            source_words = set(source_value.split())
            target_words = set(target_value.split())
            if source_words & target_words:  # Intersección
                common = len(source_words & target_words)
                total = len(source_words | target_words)
                return (common / total) * 100.0
            return 0.0

        elif self.match_type == 'regex':
            if not self.regex_pattern:
                return 0.0
            try:
                pattern = re.compile(self.regex_pattern, re.IGNORECASE if not self.case_sensitive else 0)
                if pattern.search(source_value) and pattern.search(target_value):
                    return 100.0
            except re.error:
                return 0.0
            return 0.0

        return 0.0

