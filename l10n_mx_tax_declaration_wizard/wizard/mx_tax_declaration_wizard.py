# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date
import logging

_logger = logging.getLogger(__name__)


class MxTaxDeclarationWizard(models.TransientModel):
    """Wizard multi-paso para crear declaraciones fiscales"""
    _name = 'mx.tax.declaration.wizard'
    _description = 'Wizard de Declaración Fiscal'

    # ===================
    # ESTADO DEL WIZARD
    # ===================
    state = fields.Selection([
        ('step1_config', 'Paso 1: Configuración'),
        ('step2_invoices', 'Paso 2: Facturas'),
        ('step3_reconcile', 'Paso 3: Conciliación'),
        ('step4_calculate', 'Paso 4: Cálculos'),
        ('step5_review', 'Paso 5: Revisión Final'),
        ('step6_done', 'Completado'),
    ], string='Paso', default='step1_config', required=True)

    # ===================
    # PASO 1: CONFIGURACIÓN
    # ===================
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
    )

    period_start = fields.Date(
        string='Fecha Inicio',
        required=True,
        default=lambda self: date.today().replace(day=1),
    )

    period_end = fields.Date(
        string='Fecha Fin',
        required=True,
    )

    obligation_ids = fields.Many2many(
        'mx.tax.obligation',
        string='Obligaciones Fiscales',
        domain="[('company_id', '=', company_id), ('active', '=', True)]",
    )

    # ===================
    # PASO 2: FACTURAS
    # ===================
    invoice_ids = fields.Many2many(
        'account.move',
        'wizard_declaration_invoice_rel',
        'wizard_id',
        'invoice_id',
        string='Facturas',
        domain="[('include_in_tax_declaration', '=', True), "
               "('tax_declaration_period', '>=', period_start), "
               "('tax_declaration_period', '<=', period_end), "
               "('company_id', '=', company_id), "
               "('state', '=', 'posted')]",
    )

    invoice_count = fields.Integer(
        string='Total Facturas',
        compute='_compute_invoice_stats',
    )

    total_invoiced = fields.Monetary(
        string='Total Facturado',
        compute='_compute_invoice_stats',
        currency_field='currency_id',
    )

    # Filtros para paso 2
    filter_move_type = fields.Selection([
        ('all', 'Todas'),
        ('out_invoice', 'Facturas de Cliente'),
        ('in_invoice', 'Facturas de Proveedor'),
        ('out_refund', 'NC Cliente'),
        ('in_refund', 'NC Proveedor'),
    ], string='Filtrar por Tipo', default='all')

    # ===================
    # PASO 3: CONCILIACIÓN
    # ===================
    skip_reconciliation = fields.Boolean(
        string='Omitir Conciliación',
        default=False,
        help='Marcar si no necesitas conciliar pagos con facturas',
    )

    reconciled_count = fields.Integer(
        string='Facturas Conciliadas',
        compute='_compute_reconciliation_stats',
    )

    unreconciled_count = fields.Integer(
        string='Facturas Sin Conciliar',
        compute='_compute_reconciliation_stats',
    )

    # ===================
    # PASO 4: CÁLCULOS
    # ===================
    calculation_ids = fields.One2many(
        'mx.tax.declaration.wizard.calculation',
        'wizard_id',
        string='Resultados de Cálculos',
    )

    calculations_executed = fields.Boolean(
        string='Cálculos Ejecutados',
        default=False,
    )

    # ===================
    # PASO 5: REVISIÓN
    # ===================
    total_payable = fields.Monetary(
        string='Total a Pagar',
        compute='_compute_total_payable',
        currency_field='currency_id',
    )

    # ===================
    # PASO 6: RESULTADO
    # ===================
    declaration_id = fields.Many2one(
        'mx.tax.declaration',
        string='Declaración Creada',
        readonly=True,
    )

    # ===================
    # CAMPOS COMUNES
    # ===================
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Moneda',
    )

    notes = fields.Html(
        string='Notas',
    )

    # ===================
    # COMPUTES
    # ===================
    @api.depends('invoice_ids')
    def _compute_invoice_stats(self):
        for wizard in self:
            wizard.invoice_count = len(wizard.invoice_ids)
            wizard.total_invoiced = sum(wizard.invoice_ids.mapped('amount_total'))

    @api.depends('invoice_ids', 'invoice_ids.amount_residual')
    def _compute_reconciliation_stats(self):
        for wizard in self:
            wizard.reconciled_count = len(wizard.invoice_ids.filtered(lambda inv: inv.amount_residual == 0))
            wizard.unreconciled_count = len(wizard.invoice_ids.filtered(lambda inv: inv.amount_residual != 0))

    @api.depends('calculation_ids', 'calculation_ids.result')
    def _compute_total_payable(self):
        for wizard in self:
            final_calculations = wizard.calculation_ids.filtered(lambda c: c.is_final_amount)
            wizard.total_payable = sum(final_calculations.mapped('result'))

    # ===================
    # VALIDACIONES
    # ===================
    @api.constrains('period_start', 'period_end')
    def _check_period_dates(self):
        for wizard in self:
            if wizard.period_start and wizard.period_end:
                if wizard.period_start > wizard.period_end:
                    raise ValidationError(_('La fecha de inicio debe ser anterior a la fecha de fin.'))

    # ===================
    # PASO 1: CONFIGURACIÓN
    # ===================
    @api.onchange('period_start')
    def _onchange_period_start(self):
        """Auto-calcular fecha fin al seleccionar inicio"""
        if self.period_start:
            # Por defecto, fin del mes
            from dateutil.relativedelta import relativedelta
            self.period_end = self.period_start + relativedelta(day=31)

    def action_next_step1(self):
        """Validar y pasar al paso 2"""
        self.ensure_one()

        if not self.obligation_ids:
            raise UserError(_('Debe seleccionar al menos una obligación fiscal.'))

        # Cargar facturas del período
        invoice_domain = [
            ('include_in_tax_declaration', '=', True),
            ('tax_declaration_period', '>=', self.period_start),
            ('tax_declaration_period', '<=', self.period_end),
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'posted'),
        ]

        invoices = self.env['account.move'].search(invoice_domain)

        if not invoices:
            raise UserError(
                _('No se encontraron facturas marcadas para declaración en el período seleccionado.\n\n'
                  'Período: %s - %s\n'
                  'Compañía: %s') % (self.period_start, self.period_end, self.company_id.name)
            )

        self.invoice_ids = [(6, 0, invoices.ids)]
        self.state = 'step2_invoices'

        return self._reopen_wizard()

    # ===================
    # PASO 2: FACTURAS
    # ===================
    @api.onchange('filter_move_type')
    def _onchange_filter_move_type(self):
        """Filtrar facturas por tipo"""
        if self.filter_move_type and self.filter_move_type != 'all':
            base_domain = [
                ('include_in_tax_declaration', '=', True),
                ('tax_declaration_period', '>=', self.period_start),
                ('tax_declaration_period', '<=', self.period_end),
                ('company_id', '=', self.company_id.id),
                ('state', '=', 'posted'),
                ('move_type', '=', self.filter_move_type),
            ]
            invoices = self.env['account.move'].search(base_domain)
            self.invoice_ids = [(6, 0, invoices.ids)]

    def action_add_invoices(self):
        """Abrir selector para agregar más facturas"""
        self.ensure_one()
        return {
            'name': _('Agregar Facturas'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [
                ('company_id', '=', self.company_id.id),
                ('state', '=', 'posted'),
                ('move_type', 'in', ('out_invoice', 'in_invoice', 'out_refund', 'in_refund')),
            ],
            'target': 'new',
            'context': {
                'search_default_posted': 1,
            },
        }

    def action_next_step2(self):
        """Validar y pasar al paso 3"""
        self.ensure_one()

        if not self.invoice_ids:
            raise UserError(_('Debe seleccionar al menos una factura.'))

        self.state = 'step3_reconcile'
        return self._reopen_wizard()

    def action_back_step2(self):
        """Regresar al paso 1"""
        self.ensure_one()
        self.state = 'step1_config'
        return self._reopen_wizard()

    # ===================
    # PASO 3: CONCILIACIÓN
    # ===================
    def action_open_reconcile_widget(self):
        """Abrir widget de conciliación (si está instalado)"""
        self.ensure_one()

        # Verificar si está instalado el módulo de conciliación OCA
        if not self.env['ir.module.module'].search([
            ('name', '=', 'account_reconcile_oca'),
            ('state', '=', 'installed')
        ]):
            raise UserError(
                _('El módulo de conciliación bancaria (account_reconcile_oca) no está instalado.\n\n'
                  'Puede omitir este paso marcando "Omitir Conciliación".')
            )

        # TODO: Integrar con el widget de conciliación
        # Por ahora, abrir vista de facturas para conciliación manual
        return {
            'name': _('Conciliar Facturas'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'target': 'current',
        }

    def action_next_step3(self):
        """Validar y pasar al paso 4"""
        self.ensure_one()

        if not self.skip_reconciliation and self.unreconciled_count > 0:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Advertencia'),
                'res_model': 'mx.tax.declaration.wizard.confirm',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_wizard_id': self.id,
                    'default_message': _(
                        'Hay %d facturas sin conciliar.\n\n'
                        '¿Desea continuar de todas formas?'
                    ) % self.unreconciled_count,
                },
            }

        self.state = 'step4_calculate'
        return self._reopen_wizard()

    def action_back_step3(self):
        """Regresar al paso 2"""
        self.ensure_one()
        self.state = 'step2_invoices'
        return self._reopen_wizard()

    # ===================
    # PASO 4: CÁLCULOS
    # ===================
    def action_execute_calculations(self):
        """Ejecutar todos los cálculos fiscales"""
        self.ensure_one()

        # Limpiar cálculos anteriores
        self.calculation_ids.unlink()

        results_dict = {}

        # Ejecutar cálculos por obligación
        for obligation in self.obligation_ids:
            rules = obligation.calculation_rule_ids.sorted('sequence')

            if not rules:
                _logger.warning(f"Obligación '{obligation.name}' no tiene reglas de cálculo configuradas")
                continue

            for rule in rules:
                try:
                    # Ejecutar cálculo
                    result = rule.calculate(
                        invoices=self.invoice_ids,
                        period_start=self.period_start,
                        period_end=self.period_end,
                        rules_results=results_dict,
                    )

                    results_dict[rule.id] = result

                    # Crear línea de resultado en wizard
                    self.env['mx.tax.declaration.wizard.calculation'].create({
                        'wizard_id': self.id,
                        'calculation_rule_id': rule.id,
                        'obligation_id': obligation.id,
                        'result': result,
                    })

                    _logger.info(f"Cálculo ejecutado: {rule.name} = {result}")

                except Exception as e:
                    _logger.error(f"Error ejecutando regla '{rule.name}': {str(e)}")
                    raise UserError(
                        _('Error al ejecutar la regla de cálculo "%s":\n\n%s') % (rule.name, str(e))
                    )

        self.calculations_executed = True

        return self._reopen_wizard()

    def action_next_step4(self):
        """Validar y pasar al paso 5"""
        self.ensure_one()

        if not self.calculations_executed:
            raise UserError(_('Debe ejecutar los cálculos antes de continuar.'))

        if not self.calculation_ids:
            raise UserError(_('No se generaron resultados de cálculos. Verifique su configuración.'))

        self.state = 'step5_review'
        return self._reopen_wizard()

    def action_back_step4(self):
        """Regresar al paso 3"""
        self.ensure_one()
        self.state = 'step3_reconcile'
        return self._reopen_wizard()

    # ===================
    # PASO 5: REVISIÓN FINAL
    # ===================
    def action_create_declaration(self):
        """Crear la declaración fiscal permanente"""
        self.ensure_one()

        if not self.calculations_executed:
            raise UserError(_('Debe ejecutar los cálculos antes de crear la declaración.'))

        # Crear declaración
        declaration = self.env['mx.tax.declaration'].create({
            'company_id': self.company_id.id,
            'period_start': self.period_start,
            'period_end': self.period_end,
            'obligation_ids': [(6, 0, self.obligation_ids.ids)],
            'state': 'calculated',
            'notes': self.notes or '',
            'user_id': self.env.user.id,
        })

        # Crear líneas de facturas
        for invoice in self.invoice_ids:
            self.env['mx.tax.declaration.invoice.line'].create({
                'declaration_id': declaration.id,
                'invoice_id': invoice.id,
                'included': True,
            })

        # Copiar resultados de cálculos
        for calc in self.calculation_ids:
            self.env['mx.tax.declaration.calculation.result'].create({
                'declaration_id': declaration.id,
                'calculation_rule_id': calc.calculation_rule_id.id,
                'obligation_id': calc.obligation_id.id,
                'result': calc.result,
            })

        # Marcar facturas como declaradas
        self.invoice_ids.write({'tax_declaration_status': 'declared'})

        # Guardar referencia a la declaración
        self.declaration_id = declaration.id
        self.state = 'step6_done'

        # Enviar mensaje de éxito
        message = _('Declaración fiscal creada correctamente.\n\n'
                    'Período: %s - %s\n'
                    'Total a pagar: %s %s') % (
            self.period_start,
            self.period_end,
            self.total_payable,
            self.currency_id.symbol
        )
        declaration.message_post(body=message)

        return self._reopen_wizard()

    def action_back_step5(self):
        """Regresar al paso 4"""
        self.ensure_one()
        self.state = 'step4_calculate'
        return self._reopen_wizard()

    # ===================
    # PASO 6: COMPLETADO
    # ===================
    def action_view_declaration(self):
        """Ver la declaración creada"""
        self.ensure_one()
        return {
            'name': _('Declaración Fiscal'),
            'type': 'ir.actions.act_window',
            'res_model': 'mx.tax.declaration',
            'res_id': self.declaration_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_close(self):
        """Cerrar el wizard"""
        return {'type': 'ir.actions.act_window_close'}

    # ===================
    # UTILIDADES
    # ===================
    def _reopen_wizard(self):
        """Reabrir el wizard en el mismo paso"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class MxTaxDeclarationWizardCalculation(models.TransientModel):
    """Resultados temporales de cálculos en el wizard"""
    _name = 'mx.tax.declaration.wizard.calculation'
    _description = 'Cálculo Temporal del Wizard'
    _order = 'obligation_id, sequence'

    wizard_id = fields.Many2one(
        'mx.tax.declaration.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )

    calculation_rule_id = fields.Many2one(
        'mx.tax.calculation.rule',
        string='Regla de Cálculo',
        required=True,
    )

    obligation_id = fields.Many2one(
        'mx.tax.obligation',
        string='Obligación',
        required=True,
    )

    rule_name = fields.Char(
        related='calculation_rule_id.name',
        string='Regla',
    )

    sequence = fields.Integer(
        related='calculation_rule_id.sequence',
    )

    result = fields.Monetary(
        string='Resultado',
        required=True,
        currency_field='currency_id',
    )

    is_final_amount = fields.Boolean(
        related='calculation_rule_id.is_final_amount',
        string='Monto Final',
    )

    show_in_report = fields.Boolean(
        related='calculation_rule_id.show_in_report',
    )

    currency_id = fields.Many2one(
        related='wizard_id.currency_id',
    )


class MxTaxDeclarationWizardConfirm(models.TransientModel):
    """Wizard de confirmación para advertencias"""
    _name = 'mx.tax.declaration.wizard.confirm'
    _description = 'Confirmación de Advertencia'

    wizard_id = fields.Many2one(
        'mx.tax.declaration.wizard',
        string='Wizard Principal',
        required=True,
    )

    message = fields.Text(
        string='Mensaje',
        readonly=True,
    )

    def action_confirm(self):
        """Confirmar y continuar"""
        self.wizard_id.state = 'step4_calculate'
        return self.wizard_id._reopen_wizard()

    def action_cancel(self):
        """Cancelar"""
        return {'type': 'ir.actions.act_window_close'}
