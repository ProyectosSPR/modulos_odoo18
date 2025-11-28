# -*- coding: utf-8 -*-
from odoo import models, fields, api
import json

class AIAction(models.Model):
    _name = 'ai.action'
    _description = 'Acción Ejecutable por IA'
    _order = 'sequence, name'

    # ========== IDENTIFICACIÓN ==========
    name = fields.Char(
        string="Nombre de la Acción",
        required=True,
        help="Nombre descriptivo de la acción"
    )

    code = fields.Char(
        string="Código",
        required=True,
        help="Identificador único que N8N usará para ejecutar esta acción"
    )

    description = fields.Text(
        string="Descripción",
        required=True,
        help="Descripción detallada de qué hace esta acción (la IA lee esto)"
    )

    # ========== RELACIÓN CON PERFIL ==========
    agent_profile_id = fields.Many2one(
        'ai.agent.profile',
        string="Perfil de Agente",
        required=True,
        ondelete='cascade',
        help="Perfil al que pertenece esta acción"
    )

    company_id = fields.Many2one(
        'res.company',
        string="Empresa",
        related='agent_profile_id.company_id',
        store=True,
        readonly=True
    )

    # ========== INSTRUCCIONES PARA LA IA ==========
    when_to_use = fields.Text(
        string="Cuándo Usar",
        required=True,
        help="Instrucciones claras de cuándo la IA debe usar esta acción"
    )

    examples = fields.Text(
        string="Ejemplos de Uso",
        help="Ejemplos concretos de situaciones donde usar esta acción"
    )

    # ========== PARÁMETROS ==========
    parameters_description = fields.Text(
        string="Descripción de Parámetros",
        help="Descripción de los parámetros que acepta esta acción (puede ser JSON Schema o texto libre)"
    )

    required_parameters = fields.Text(
        string="Parámetros Obligatorios",
        help="Lista de parámetros obligatorios (ej: name, email, phone)"
    )

    optional_parameters = fields.Text(
        string="Parámetros Opcionales",
        help="Lista de parámetros opcionales (ej: company, notes, tags)"
    )

    # ========== CONTROL ==========
    active = fields.Boolean(
        string="Activo",
        default=True,
        help="Si está desactivado, la IA no podrá usar esta acción"
    )

    sequence = fields.Integer(
        string="Secuencia",
        default=10,
        help="Orden de prioridad (menor = mayor prioridad)"
    )

    requires_confirmation = fields.Boolean(
        string="Requiere Confirmación",
        default=False,
        help="Si está activado, N8N pedirá confirmación antes de ejecutar"
    )

    # ========== METADATOS ==========
    usage_count = fields.Integer(
        string="Veces Usada",
        default=0,
        readonly=True,
        help="Número de veces que esta acción ha sido ejecutada"
    )

    last_used_date = fields.Datetime(
        string="Último Uso",
        readonly=True,
        help="Fecha y hora del último uso"
    )

    # ========== CONSTRAINTS ==========
    _sql_constraints = [
        ('code_profile_unique',
         'UNIQUE(code, agent_profile_id)',
         'El código debe ser único dentro de cada perfil!')
    ]

    def increment_usage(self):
        """Incrementa el contador de uso"""
        self.ensure_one()
        self.sudo().write({
            'usage_count': self.usage_count + 1,
            'last_used_date': fields.Datetime.now()
        })

    def _format_for_api(self):
        """Formatea la acción para respuesta de API"""
        self.ensure_one()

        # Intentar parsear parámetros si es JSON
        try:
            params_desc = json.loads(self.parameters_description) if self.parameters_description else {}
        except:
            params_desc = self.parameters_description or ''

        return {
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'when_to_use': self.when_to_use,
            'examples': self.examples or '',
            'parameters': {
                'description': params_desc,
                'required': self.required_parameters.split(',') if self.required_parameters else [],
                'optional': self.optional_parameters.split(',') if self.optional_parameters else [],
            },
            'requires_confirmation': self.requires_confirmation,
            'sequence': self.sequence
        }
