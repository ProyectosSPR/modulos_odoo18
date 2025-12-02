# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class MxTaxDeclaration(models.Model):
    """Declaración Fiscal SAT - Modelo permanente"""
    _name = 'mx.tax.declaration'
    _description = 'Declaración Fiscal SAT'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'period_start desc, id desc'

    name = fields.Char(
        string='Nombre',
        compute='_compute_name',
        store=True,
        readonly=True,
    )

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )

    # Período fiscal
    period_start = fields.Date(
        string='Fecha Inicio',
        required=True,
        tracking=True,
    )
    period_end = fields.Date(
        string='Fecha Fin',
        required=True,
        tracking=True,
    )
    period_name = fields.Char(
        string='Período',
        compute='_compute_period_name',
        store=True,
    )

    # Obligaciones fiscales
    obligation_ids = fields.Many2many(
        'mx.tax.obligation',
        string='Obligaciones Fiscales',
        required=True,
        tracking=True,
    )
    obligation_count = fields.Integer(
        string='Número de Obligaciones',
        compute='_compute_obligation_count',
    )

    # Estado
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('calculated', 'Calculado'),
        ('reviewed', 'Revisado'),
        ('filed', 'Presentado al SAT'),
        ('paid', 'Pagado'),
        ('cancel', 'Cancelado'),
    ], string='Estado',
        default='draft',
        required=True,
        tracking=True,
    )

    # Líneas de facturas incluidas
    invoice_line_ids = fields.One2many(
        'mx.tax.declaration.invoice.line',
        'declaration_id',
        string='Facturas Incluidas',
    )
    invoice_count = fields.Integer(
        string='Número de Facturas',
        compute='_compute_invoice_count',
    )

    # Resultados de cálculos
    calculation_result_ids = fields.One2many(
        'mx.tax.declaration.calculation.result',
        'declaration_id',
        string='Resultados de Cálculos',
    )

    # Montos totales (computados desde las líneas)
    total_income = fields.Monetary(
        string='Total Ingresos',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
    )
    total_expense = fields.Monetary(
        string='Total Egresos',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
    )
    total_tax_collected = fields.Monetary(
        string='Impuestos Cobrados',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
    )
    total_tax_paid = fields.Monetary(
        string='Impuestos Pagados',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
    )
    total_payable = fields.Monetary(
        string='Total a Pagar',
        compute='_compute_total_payable',
        store=True,
        currency_field='currency_id',
        help='Monto total a pagar al SAT según los cálculos',
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='company_id.currency_id',
        store=True,
    )

    # Fechas importantes
    deadline_date = fields.Date(
        string='Fecha Límite de Pago',
        compute='_compute_deadline_date',
        store=True,
        tracking=True,
    )
    filed_date = fields.Date(
        string='Fecha de Presentación',
        tracking=True,
    )
    payment_date = fields.Date(
        string='Fecha de Pago',
        tracking=True,
    )

    # Archivos generados
    report_pdf = fields.Binary(
        string='Reporte PDF',
        attachment=True,
    )
    report_pdf_filename = fields.Char(
        string='Nombre del PDF',
    )
    report_excel = fields.Binary(
        string='Reporte Excel',
        attachment=True,
    )
    report_excel_filename = fields.Char(
        string='Nombre del Excel',
    )

    # Notas
    notes = fields.Html(
        string='Notas',
        tracking=True,
    )

    # Usuario que creó
    user_id = fields.Many2one(
        'res.users',
        string='Creado por',
        default=lambda self: self.env.user,
        tracking=True,
    )

    @api.depends('company_id', 'period_start', 'period_end')
    def _compute_name(self):
        for record in self:
            if record.company_id and record.period_start and record.period_end:
                period_str = f"{record.period_start.strftime('%m/%Y')}"
                if record.period_start.month != record.period_end.month:
                    period_str = f"{record.period_start.strftime('%m/%Y')} - {record.period_end.strftime('%m/%Y')}"
                record.name = f"Declaración {period_str} - {record.company_id.name}"
            else:
                record.name = _('Nueva Declaración Fiscal')

    @api.depends('period_start', 'period_end')
    def _compute_period_name(self):
        for record in self:
            if record.period_start and record.period_end:
                if record.period_start == record.period_end:
                    record.period_name = record.period_start.strftime('%B %Y')
                elif record.period_start.month == record.period_end.month:
                    record.period_name = record.period_start.strftime('%B %Y')
                else:
                    record.period_name = f"{record.period_start.strftime('%B')} - {record.period_end.strftime('%B %Y')}"
            else:
                record.period_name = ''

    @api.depends('obligation_ids')
    def _compute_obligation_count(self):
        for record in self:
            record.obligation_count = len(record.obligation_ids)

    @api.depends('invoice_line_ids')
    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.invoice_line_ids.filtered(lambda l: l.included))

    @api.depends('invoice_line_ids', 'invoice_line_ids.included',
                 'invoice_line_ids.amount_untaxed', 'invoice_line_ids.amount_tax')
    def _compute_totals(self):
        for record in self:
            included_lines = record.invoice_line_ids.filtered(lambda l: l.included)

            # Separar por tipo de factura
            income_lines = included_lines.filtered(
                lambda l: l.invoice_id.move_type in ('out_invoice', 'out_refund')
            )
            expense_lines = included_lines.filtered(
                lambda l: l.invoice_id.move_type in ('in_invoice', 'in_refund')
            )

            # Calcular totales
            record.total_income = sum(income_lines.mapped('amount_untaxed'))
            record.total_expense = sum(expense_lines.mapped('amount_untaxed'))
            record.total_tax_collected = sum(income_lines.mapped('amount_tax'))
            record.total_tax_paid = sum(expense_lines.mapped('amount_tax'))

    @api.depends('calculation_result_ids', 'calculation_result_ids.result')
    def _compute_total_payable(self):
        for record in self:
            # Sumar todos los resultados que sean montos finales
            final_amounts = record.calculation_result_ids.filtered(
                lambda r: r.calculation_rule_id.is_final_amount
            )
            record.total_payable = sum(final_amounts.mapped('result'))

    @api.depends('period_end', 'obligation_ids')
    def _compute_deadline_date(self):
        for record in self:
            if record.period_end and record.obligation_ids:
                # Usar el día límite de la primera obligación
                # (podrías mejorar esto para tomar el mínimo)
                deadline_day = record.obligation_ids[0].deadline_day

                # La fecha límite es normalmente el mes siguiente
                next_month = record.period_end + relativedelta(months=1)
                try:
                    record.deadline_date = next_month.replace(day=deadline_day)
                except ValueError:
                    # Si el día no existe en ese mes, usar el último día
                    record.deadline_date = next_month.replace(day=1) + relativedelta(months=1, days=-1)
            else:
                record.deadline_date = False

    @api.constrains('period_start', 'period_end')
    def _check_period_dates(self):
        for record in self:
            if record.period_start and record.period_end:
                if record.period_start > record.period_end:
                    raise ValidationError(_('La fecha de inicio debe ser anterior a la fecha de fin.'))

    def action_calculate(self):
        """Ejecutar cálculos fiscales"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Solo se pueden calcular declaraciones en estado Borrador.'))

        # Eliminar cálculos anteriores
        self.calculation_result_ids.unlink()

        # Obtener facturas incluidas
        invoices = self.invoice_line_ids.filtered(lambda l: l.included).mapped('invoice_id')

        # Ejecutar cálculos por obligación
        for obligation in self.obligation_ids:
            self._execute_calculations_for_obligation(obligation, invoices)

        self.state = 'calculated'
        self.message_post(body=_('Cálculos fiscales ejecutados correctamente.'))

    def _execute_calculations_for_obligation(self, obligation, invoices):
        """Ejecutar reglas de cálculo de una obligación"""
        rules = obligation.calculation_rule_ids.sorted('sequence')
        results = {}

        for rule in rules:
            try:
                result = rule.calculate(
                    invoices=invoices,
                    period_start=self.period_start,
                    period_end=self.period_end,
                    rules_results=results,
                )

                results[rule.id] = result

                # Guardar resultado
                self.env['mx.tax.declaration.calculation.result'].create({
                    'declaration_id': self.id,
                    'calculation_rule_id': rule.id,
                    'obligation_id': obligation.id,
                    'result': result,
                })

                _logger.info(f"Regla '{rule.name}' ejecutada: {result}")

            except Exception as e:
                _logger.error(f"Error ejecutando regla '{rule.name}': {str(e)}")
                raise UserError(
                    _('Error al ejecutar la regla de cálculo "%s": %s') % (rule.name, str(e))
                )

    def action_review(self):
        """Marcar como revisada"""
        self.ensure_one()
        if self.state != 'calculated':
            raise UserError(_('Solo se pueden revisar declaraciones en estado Calculado.'))

        self.state = 'reviewed'
        self.message_post(body=_('Declaración revisada y aprobada.'))

    def action_file(self):
        """Marcar como presentada al SAT"""
        self.ensure_one()
        if self.state != 'reviewed':
            raise UserError(_('Solo se pueden presentar declaraciones en estado Revisado.'))

        self.state = 'filed'
        self.filed_date = fields.Date.today()
        self.message_post(body=_('Declaración presentada al SAT el %s.') % self.filed_date)

    def action_pay(self):
        """Marcar como pagada"""
        self.ensure_one()
        if self.state != 'filed':
            raise UserError(_('Solo se pueden marcar como pagadas las declaraciones presentadas.'))

        self.state = 'paid'
        self.payment_date = fields.Date.today()
        self.message_post(body=_('Declaración pagada el %s.') % self.payment_date)

    def action_cancel(self):
        """Cancelar declaración"""
        self.ensure_one()
        if self.state == 'paid':
            raise UserError(_('No se puede cancelar una declaración pagada.'))

        self.state = 'cancel'
        self.message_post(body=_('Declaración cancelada.'))

    def action_reset_to_draft(self):
        """Regresar a borrador"""
        self.ensure_one()
        if self.state not in ('calculated', 'reviewed', 'cancel'):
            raise UserError(_('No se puede regresar a borrador desde el estado actual.'))

        self.state = 'draft'
        self.message_post(body=_('Declaración regresada a borrador.'))

    def action_view_invoices(self):
        """Ver facturas incluidas"""
        self.ensure_one()
        invoice_ids = self.invoice_line_ids.filtered(lambda l: l.included).mapped('invoice_id').ids

        return {
            'name': _('Facturas de la Declaración'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoice_ids)],
            'context': {'create': False},
        }

    def action_generate_pdf(self):
        """Generar reporte PDF"""
        self.ensure_one()
        # TODO: Implementar generación de PDF
        # Este método se implementará en el módulo de reportes
        raise UserError(_('La generación de PDF se implementará en el módulo de reportes.'))

    def action_generate_excel(self):
        """Generar reporte Excel"""
        self.ensure_one()
        # TODO: Implementar generación de Excel
        # Este método se implementará en el módulo de reportes
        raise UserError(_('La generación de Excel se implementará en el módulo de reportes.'))

    def unlink(self):
        """No permitir eliminar declaraciones presentadas"""
        for record in self:
            if record.state in ('filed', 'paid'):
                raise UserError(
                    _('No se puede eliminar una declaración que ya fue presentada al SAT. '
                      'Cancele la declaración primero.')
                )
        return super().unlink()
