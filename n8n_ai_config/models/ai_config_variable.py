# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AIConfigVariable(models.Model):
    _name = 'ai.config.variable'
    _description = 'Variable de Configuración para IA'
    _order = 'sequence, name'

    agent_profile_id = fields.Many2one(
        'ai.agent.profile',
        string="Perfil de Agente",
        required=True,
        ondelete='cascade'
    )

    name = fields.Char(
        string="Nombre de Variable",
        required=True,
        help="Nombre de la variable (ej: response_format, max_retries, etc.)"
    )

    value = fields.Char(
        string="Valor",
        required=True,
        help="Valor de la variable"
    )

    description = fields.Char(
        string="Descripción",
        help="Descripción opcional de para qué sirve esta variable"
    )

    sequence = fields.Integer(
        string="Secuencia",
        default=10,
        help="Orden de las variables"
    )

    _sql_constraints = [
        ('name_profile_unique',
         'UNIQUE(name, agent_profile_id)',
         'El nombre de la variable debe ser único dentro de cada perfil!')
    ]
