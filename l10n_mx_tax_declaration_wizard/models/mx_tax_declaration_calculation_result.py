# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class MxTaxDeclarationCalculationResult(models.Model):
    """Resultados de cálculos fiscales en una declaración"""
    _name = 'mx.tax.declaration.calculation.result'
    _description = 'Resultado de Cálculo Fiscal'
    _order = 'obligation_id, sequence, id'

    declaration_id = fields.Many2one(
        'mx.tax.declaration',
        string='Declaración',
        required=True,
        ondelete='cascade',
        index=True,
    )

    calculation_rule_id = fields.Many2one(
        'mx.tax.calculation.rule',
        string='Regla de Cálculo',
        required=True,
        ondelete='restrict',
    )

    obligation_id = fields.Many2one(
        'mx.tax.obligation',
        string='Obligación Fiscal',
        required=True,
        ondelete='restrict',
        index=True,
    )

    # Campos relacionados para facilitar vistas
    rule_name = fields.Char(
        string='Nombre Regla',
        related='calculation_rule_id.name',
        store=True,
        readonly=True,
    )

    sequence = fields.Integer(
        string='Secuencia',
        related='calculation_rule_id.sequence',
        store=True,
        readonly=True,
    )

    calculation_type = fields.Selection(
        related='calculation_rule_id.calculation_type',
        string='Tipo de Cálculo',
        store=True,
        readonly=True,
    )

    # Resultado
    result = fields.Monetary(
        string='Resultado',
        required=True,
        currency_field='currency_id',
    )

    result_type = fields.Selection(
        related='calculation_rule_id.result_type',
        string='Tipo de Resultado',
        store=True,
        readonly=True,
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='declaration_id.currency_id',
        store=True,
        readonly=True,
    )

    # Flags para presentación
    show_in_report = fields.Boolean(
        string='Mostrar en Reporte',
        related='calculation_rule_id.show_in_report',
        store=True,
        readonly=True,
    )

    is_subtotal = fields.Boolean(
        string='Es Subtotal',
        related='calculation_rule_id.is_subtotal',
        store=True,
        readonly=True,
    )

    is_final_amount = fields.Boolean(
        string='Es Monto Final',
        related='calculation_rule_id.is_final_amount',
        store=True,
        readonly=True,
    )

    # Metadata
    calculation_date = fields.Datetime(
        string='Fecha de Cálculo',
        default=fields.Datetime.now,
        readonly=True,
    )

    # Override manual
    is_manual_override = fields.Boolean(
        string='Ajuste Manual',
        default=False,
        help='Indica si este resultado fue ajustado manualmente',
    )

    original_result = fields.Monetary(
        string='Resultado Original',
        currency_field='currency_id',
        help='Resultado original antes del ajuste manual',
    )

    manual_reason = fields.Text(
        string='Justificación del Ajuste',
        help='Razón del ajuste manual',
    )

    notes = fields.Text(
        string='Notas',
    )

    def action_manual_override(self):
        """Abrir wizard para ajuste manual"""
        self.ensure_one()
        return {
            'name': _('Ajustar Resultado Manualmente'),
            'type': 'ir.actions.act_window',
            'res_model': 'mx.tax.calculation.manual.override.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_result_id': self.id,
                'default_original_result': self.result,
            },
        }

    def action_revert_override(self):
        """Revertir ajuste manual"""
        self.ensure_one()
        if self.is_manual_override and self.original_result:
            self.write({
                'result': self.original_result,
                'is_manual_override': False,
                'original_result': 0.0,
                'manual_reason': False,
            })

    @api.model_create_multi
    def create(self, vals_list):
        """Al crear, si no es override manual, guardar resultado original"""
        for vals in vals_list:
            if not vals.get('is_manual_override'):
                vals['original_result'] = vals.get('result', 0.0)
        return super().create(vals_list)

    _sql_constraints = [
        ('declaration_rule_unique',
         'unique(declaration_id, calculation_rule_id)',
         'Esta regla de cálculo ya existe en esta declaración'),
    ]
