# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AIExecutionLog(models.Model):
    _name = 'ai.execution.log'
    _description = 'Log de Ejecuciones de IA'
    _order = 'execution_date desc'
    _rec_name = 'display_name'

    # ========== RELACIONES ==========
    agent_profile_id = fields.Many2one(
        'ai.agent.profile',
        string="Perfil de Agente",
        required=True,
        ondelete='cascade',
        help="Perfil que fue usado en esta ejecución"
    )

    action_code = fields.Char(
        string="Código de Acción",
        help="Código de la acción que fue ejecutada (si aplica)"
    )

    partner_id = fields.Many2one(
        'res.partner',
        string="Usuario",
        required=True,
        help="Usuario que realizó la consulta"
    )

    company_id = fields.Many2one(
        'res.company',
        string="Empresa",
        required=True,
        default=lambda self: self.env.company
    )

    # ========== DATOS DE LA EJECUCIÓN ==========
    execution_date = fields.Datetime(
        string="Fecha de Ejecución",
        required=True,
        default=fields.Datetime.now,
        help="Fecha y hora de la ejecución"
    )

    input_message = fields.Text(
        string="Mensaje de Entrada",
        help="Mensaje original del usuario"
    )

    ai_response = fields.Text(
        string="Respuesta de la IA",
        help="Respuesta generada por la IA"
    )

    action_executed = fields.Boolean(
        string="Acción Ejecutada",
        default=False,
        help="Indica si se ejecutó alguna acción"
    )

    success = fields.Boolean(
        string="Éxito",
        default=True,
        help="Indica si la ejecución fue exitosa"
    )

    error_message = fields.Text(
        string="Mensaje de Error",
        help="Mensaje de error si la ejecución falló"
    )

    # ========== ANALYTICS ==========
    tokens_used = fields.Integer(
        string="Tokens Usados",
        default=0,
        help="Número de tokens consumidos en esta ejecución"
    )

    execution_time_ms = fields.Integer(
        string="Tiempo de Ejecución (ms)",
        help="Tiempo de ejecución en milisegundos"
    )

    cost = fields.Float(
        string="Costo",
        digits=(10, 6),
        help="Costo estimado de esta ejecución en USD"
    )

    # ========== METADATA ==========
    metadata = fields.Text(
        string="Metadata Adicional",
        help="Cualquier metadata adicional en formato JSON"
    )

    # ========== COMPUTED FIELDS ==========
    display_name = fields.Char(
        string="Nombre",
        compute='_compute_display_name',
        store=False
    )

    @api.depends('agent_profile_id', 'execution_date', 'partner_id')
    def _compute_display_name(self):
        for record in self:
            date_str = record.execution_date.strftime('%Y-%m-%d %H:%M') if record.execution_date else ''
            record.display_name = f"{record.agent_profile_id.name} - {record.partner_id.name} - {date_str}"

    @api.model
    def create_log(self, vals):
        """
        Método helper para crear logs desde API.
        Incrementa automáticamente el contador de uso del perfil y acción.
        """
        log = self.create(vals)

        # Incrementar uso del perfil
        if log.agent_profile_id:
            log.agent_profile_id.sudo().increment_usage()

        # Incrementar uso de la acción si se ejecutó
        if log.action_code and log.action_executed:
            action = self.env['ai.action'].search([
                ('code', '=', log.action_code),
                ('agent_profile_id', '=', log.agent_profile_id.id)
            ], limit=1)
            if action:
                action.sudo().increment_usage()

        return log

    @api.model
    def get_analytics(self, company_id, partner_id=None, days=30):
        """
        Obtiene analytics de uso para un período.
        Si partner_id es None, devuelve analytics de toda la empresa.
        """
        from datetime import datetime, timedelta

        domain = [
            ('company_id', '=', company_id),
            ('execution_date', '>=', fields.Datetime.to_string(datetime.now() - timedelta(days=days)))
        ]

        if partner_id:
            domain.append(('partner_id', '=', partner_id))

        logs = self.search(domain)

        total_executions = len(logs)
        total_actions = len(logs.filtered(lambda l: l.action_executed))
        total_errors = len(logs.filtered(lambda l: not l.success))
        total_tokens = sum(logs.mapped('tokens_used'))
        total_cost = sum(logs.mapped('cost'))
        avg_execution_time = sum(logs.mapped('execution_time_ms')) / total_executions if total_executions > 0 else 0

        # Top acciones más usadas
        action_usage = {}
        for log in logs.filtered(lambda l: l.action_code):
            action_usage[log.action_code] = action_usage.get(log.action_code, 0) + 1

        top_actions = sorted(action_usage.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            'period_days': days,
            'total_executions': total_executions,
            'total_actions_executed': total_actions,
            'total_errors': total_errors,
            'success_rate': (total_executions - total_errors) / total_executions * 100 if total_executions > 0 else 0,
            'total_tokens': total_tokens,
            'total_cost_usd': total_cost,
            'avg_execution_time_ms': avg_execution_time,
            'top_actions': [{'code': code, 'count': count} for code, count in top_actions]
        }
