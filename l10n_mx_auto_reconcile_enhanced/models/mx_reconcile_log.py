# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class MxReconcileLog(models.Model):
    """Log de conciliaciones automáticas para auditoría"""
    _name = 'mx.reconcile.log'
    _description = 'Log de Conciliación Automática'
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Nombre',
        compute='_compute_name',
        store=True,
    )
    date = fields.Datetime(
        string='Fecha',
        default=fields.Datetime.now,
        required=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='Usuario',
        default=lambda self: self.env.user,
        required=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
        required=True,
    )

    # Documentos conciliados
    payment_id = fields.Many2one(
        'account.payment',
        string='Pago',
    )
    statement_line_id = fields.Many2one(
        'account.bank.statement.line',
        string='Línea Bancaria',
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Factura',
        required=True,
    )

    # Regla utilizada
    rule_id = fields.Many2one(
        'mx.reconcile.rule',
        string='Regla Directa',
    )
    relation_rule_id = fields.Many2one(
        'mx.reconcile.relation.rule',
        string='Regla por Relación',
    )
    rule_type = fields.Selection([
        ('direct', 'Directa'),
        ('relation', 'Por Relación'),
    ], string='Tipo de Regla', required=True)

    # Detalles del match
    match_score = fields.Float(
        string='Score de Coincidencia',
        help='Porcentaje de confianza (0-100)',
    )
    matched_value = fields.Char(
        string='Valor que Coincidió',
        help='Valor que generó el match',
    )
    source_field = fields.Char(
        string='Campo Origen',
    )
    target_field = fields.Char(
        string='Campo Destino',
    )
    related_document = fields.Char(
        string='Documento Relacionado',
        help='Para reglas por relación, el documento intermedio',
    )

    # Estado
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmado'),
        ('rejected', 'Rechazado'),
    ], string='Estado', default='pending', required=True)

    notes = fields.Text(
        string='Notas',
    )

    @api.depends('statement_line_id', 'payment_id', 'invoice_id', 'date')
    def _compute_name(self):
        for record in self:
            source = record.statement_line_id or record.payment_id
            source_name = source.name if source else 'N/A'
            invoice_name = record.invoice_id.name if record.invoice_id else 'N/A'
            record.name = f"{source_name} → {invoice_name}"

    def action_confirm(self):
        """Confirmar la conciliación"""
        self.write({'state': 'confirmed'})

    def action_reject(self):
        """Rechazar la conciliación"""
        self.write({'state': 'rejected'})
