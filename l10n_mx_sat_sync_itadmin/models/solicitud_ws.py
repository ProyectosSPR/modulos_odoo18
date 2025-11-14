# -*- coding: utf-8 -*-
from odoo import models, fields, _, api

class SolicitudWS(models.Model):
    _name = 'solicitud.ws'
    _description = 'SolicitudWS'

    #solicitud
    id_solicitud = fields.Char("ID Solicitud")
    cod_estatus = fields.Char("Codigo Solicitud")
    mensaje = fields.Char("Mensaje de solicitud")
    estado_solicitud = fields.Selection([
                      ('0', 'Token invalido'),
                      ('1', 'Aceptada'),
                      ('2', 'En proceso'),
                      ('3', 'Terminada'),
                      ('4', 'Error'),
                      ('5', 'Rechazada'),
                      ('6', 'Vencida'),],
                      "Estado solicitud",)

    state = fields.Selection([('draft', 'En espera'), ('done', 'Hecho'), ('cancel', 'Error')], string='Estado', default='draft')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)

    #Datos de solicitud
    fecha = fields.Datetime('Fecha de solicitud')
    fecha_inicio = fields.Datetime('Fecha inicio')
    fecha_fin = fields.Datetime('Fecha fin')
    rfc_receptor = fields.Boolean('Solicitud de recibidos')
    rfc_emisor = fields.Boolean('Solicitud de emitidos')

    # verificacion
    cod_verifica = fields.Char("Codigo verificacion")
    mensaje_ver = fields.Char("Mensaje de verificacion")
    numero_cfdis = fields.Char("Numero CFDIs")
    paquetes = fields.Char("Paquetes")

    # descarga
    cod_descarga = fields.Char("Codigo descarga")
    mensaje_descarga = fields.Char("Mensaje de descarga")
    paquete_b64 = fields.Binary(string='Paquete b64')
    filename = fields.Char('paquete.zip')
