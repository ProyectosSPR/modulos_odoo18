# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval
import logging

_logger = logging.getLogger(__name__)


class MxTaxCalculationRule(models.Model):
    """Reglas de cálculo dinámico para obligaciones fiscales"""
    _name = 'mx.tax.calculation.rule'
    _description = 'Regla de Cálculo Fiscal'
    _order = 'obligation_id, sequence, name'

    name = fields.Char(
        string='Nombre de la Regla',
        required=True,
        help='Ejemplo: IVA Causado, IVA Acreditable, Base Gravable ISR',
    )
    obligation_id = fields.Many2one(
        'mx.tax.obligation',
        string='Obligación Fiscal',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de ejecución de las reglas',
    )
    active = fields.Boolean(
        default=True,
    )

    # Tipo de operación
    calculation_type = fields.Selection([
        ('simple_sum', 'Suma Simple'),
        ('simple_subtract', 'Resta Simple'),
        ('filtered_sum', 'Suma con Filtros'),
        ('filtered_subtract', 'Resta con Filtros'),
        ('multiply', 'Multiplicación'),
        ('divide', 'División'),
        ('percentage', 'Porcentaje'),
        ('formula', 'Fórmula Personalizada (Python)'),
    ], string='Tipo de Cálculo', required=True, default='filtered_sum')

    # Para sumas/restas simples y con filtros
    source_model = fields.Selection([
        ('account.move', 'Facturas'),
        ('account.move.line', 'Líneas de Factura'),
        ('account.payment', 'Pagos'),
    ], string='Modelo Origen', default='account.move')

    field_to_sum = fields.Selection([
        ('amount_untaxed', 'Subtotal (Sin impuestos)'),
        ('amount_tax', 'Impuestos'),
        ('amount_total', 'Total'),
        ('amount_residual', 'Saldo Pendiente'),
    ], string='Campo a Sumar')

    # Filtros tipo dominio de Odoo
    domain_filter = fields.Text(
        string='Filtro (Dominio Odoo)',
        default='[]',
        help='Ejemplo: [(\'move_type\', \'=\', \'out_invoice\'), (\'state\', \'=\', \'posted\')]',
    )

    # Para operaciones matemáticas
    operand_1 = fields.Many2one(
        'mx.tax.calculation.rule',
        string='Operando 1',
        help='Primera regla de cálculo para operaciones matemáticas',
    )
    operand_2 = fields.Many2one(
        'mx.tax.calculation.rule',
        string='Operando 2',
        help='Segunda regla de cálculo para operaciones matemáticas',
    )
    operand_value = fields.Float(
        string='Valor Fijo',
        help='Valor fijo para multiplicar, dividir o calcular porcentaje',
    )

    # Fórmula personalizada (Python con safe_eval)
    python_formula = fields.Text(
        string='Fórmula Python',
        help='''Fórmula Python segura. Variables disponibles:
        - invoices: facturas filtradas
        - payments: pagos filtrados
        - rules: dict con resultados de otras reglas por ID
        - company: compañía actual
        - period_start: fecha inicio del período
        - period_end: fecha fin del período

        Ejemplo: sum(inv.amount_untaxed for inv in invoices if inv.move_type == 'out_invoice')
        ''',
    )

    # Resultado
    result_type = fields.Selection([
        ('amount', 'Monto Monetario'),
        ('percentage', 'Porcentaje'),
        ('quantity', 'Cantidad'),
    ], string='Tipo de Resultado', default='amount')

    # Configuración visual
    show_in_report = fields.Boolean(
        string='Mostrar en Reporte',
        default=True,
    )
    is_subtotal = fields.Boolean(
        string='Es Subtotal',
        help='Marcar si este cálculo es un subtotal que se usa en otros cálculos',
    )
    is_final_amount = fields.Boolean(
        string='Es Monto Final a Pagar',
        help='Marcar si este es el monto final a pagar de esta obligación',
    )

    description = fields.Text(
        string='Descripción',
        help='Descripción de qué calcula esta regla',
    )

    @api.constrains('domain_filter')
    def _check_domain_filter(self):
        """Validar que el dominio sea válido"""
        for record in self:
            if record.domain_filter:
                try:
                    safe_eval(record.domain_filter)
                except Exception as e:
                    raise ValidationError(
                        _('El filtro de dominio no es válido: %s') % str(e)
                    )

    @api.constrains('python_formula', 'calculation_type')
    def _check_python_formula(self):
        """Validar que la fórmula Python sea válida"""
        for record in self:
            if record.calculation_type == 'formula' and record.python_formula:
                try:
                    # Validación sintáctica básica
                    compile(record.python_formula, '<string>', 'eval')
                except SyntaxError as e:
                    raise ValidationError(
                        _('La fórmula Python tiene errores de sintaxis: %s') % str(e)
                    )

    def calculate(self, invoices=None, payments=None, period_start=None, period_end=None, rules_results=None):
        """
        Ejecutar el cálculo de esta regla

        :param invoices: recordset de facturas filtradas
        :param payments: recordset de pagos filtrados
        :param period_start: fecha inicio del período
        :param period_end: fecha fin del período
        :param rules_results: diccionario con resultados de otras reglas {rule_id: result}
        :return: resultado numérico del cálculo
        """
        self.ensure_one()

        if invoices is None:
            invoices = self.env['account.move']
        if payments is None:
            payments = self.env['account.payment']
        if rules_results is None:
            rules_results = {}

        try:
            if self.calculation_type == 'simple_sum':
                return self._calculate_simple_sum(invoices)

            elif self.calculation_type == 'simple_subtract':
                return self._calculate_simple_subtract(invoices)

            elif self.calculation_type == 'filtered_sum':
                filtered_invoices = self._apply_domain_filter(invoices)
                return self._calculate_simple_sum(filtered_invoices)

            elif self.calculation_type == 'filtered_subtract':
                filtered_invoices = self._apply_domain_filter(invoices)
                return self._calculate_simple_subtract(filtered_invoices)

            elif self.calculation_type == 'multiply':
                return self._calculate_multiply(rules_results)

            elif self.calculation_type == 'divide':
                return self._calculate_divide(rules_results)

            elif self.calculation_type == 'percentage':
                return self._calculate_percentage(rules_results)

            elif self.calculation_type == 'formula':
                return self._calculate_formula(invoices, payments, period_start, period_end, rules_results)

            else:
                return 0.0

        except Exception as e:
            _logger.error(f"Error calculando regla {self.name}: {str(e)}")
            raise UserError(
                _('Error al calcular la regla "%s": %s') % (self.name, str(e))
            )

    def _apply_domain_filter(self, records):
        """Aplicar filtro de dominio a un recordset"""
        if not self.domain_filter or self.domain_filter == '[]':
            return records

        try:
            domain = safe_eval(self.domain_filter)
            return records.filtered_domain(domain)
        except Exception as e:
            _logger.error(f"Error aplicando filtro de dominio: {str(e)}")
            return records

    def _calculate_simple_sum(self, invoices):
        """Calcular suma simple del campo configurado"""
        if not self.field_to_sum or not invoices:
            return 0.0

        return sum(invoices.mapped(self.field_to_sum))

    def _calculate_simple_subtract(self, invoices):
        """Calcular resta simple del campo configurado (útil para devoluciones)"""
        if not self.field_to_sum or not invoices:
            return 0.0

        # Restar facturas de tipo refund
        refunds = invoices.filtered(lambda inv: inv.move_type in ('out_refund', 'in_refund'))
        regular = invoices - refunds

        return sum(regular.mapped(self.field_to_sum)) - sum(refunds.mapped(self.field_to_sum))

    def _calculate_multiply(self, rules_results):
        """Multiplicar dos operandos o un operando por un valor fijo"""
        if self.operand_1 and self.operand_2:
            val1 = rules_results.get(self.operand_1.id, 0.0)
            val2 = rules_results.get(self.operand_2.id, 0.0)
            return val1 * val2
        elif self.operand_1 and self.operand_value:
            val1 = rules_results.get(self.operand_1.id, 0.0)
            return val1 * self.operand_value
        return 0.0

    def _calculate_divide(self, rules_results):
        """Dividir dos operandos o un operando por un valor fijo"""
        if self.operand_1 and self.operand_2:
            val1 = rules_results.get(self.operand_1.id, 0.0)
            val2 = rules_results.get(self.operand_2.id, 0.0)
            return val1 / val2 if val2 != 0 else 0.0
        elif self.operand_1 and self.operand_value:
            val1 = rules_results.get(self.operand_1.id, 0.0)
            return val1 / self.operand_value if self.operand_value != 0 else 0.0
        return 0.0

    def _calculate_percentage(self, rules_results):
        """Calcular porcentaje de un operando"""
        if self.operand_1 and self.operand_value:
            val1 = rules_results.get(self.operand_1.id, 0.0)
            return val1 * (self.operand_value / 100.0)
        return 0.0

    def _calculate_formula(self, invoices, payments, period_start, period_end, rules_results):
        """Ejecutar fórmula Python personalizada con safe_eval"""
        if not self.python_formula:
            return 0.0

        # Contexto seguro para safe_eval
        eval_context = {
            'invoices': invoices,
            'payments': payments,
            'rules': rules_results,
            'company': self.obligation_id.company_id,
            'period_start': period_start,
            'period_end': period_end,
            'sum': sum,
            'len': len,
            'abs': abs,
            'min': min,
            'max': max,
            'round': round,
        }

        try:
            result = safe_eval(self.python_formula, eval_context, mode='eval', nocopy=True)
            return float(result) if result is not None else 0.0
        except Exception as e:
            _logger.error(f"Error ejecutando fórmula Python: {str(e)}")
            raise UserError(
                _('Error ejecutando fórmula Python en regla "%s": %s') % (self.name, str(e))
            )
