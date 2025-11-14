# -*- coding: utf-8 -*-
from odoo import models,fields, api, _
from odoo.exceptions import UserError
import base64

class XMLInvoiceReconcile(models.TransientModel):
    _name ='xml.invoice.reconcile'
    _description = 'XMLInvoiceReconcile'

    attachment_id = fields.Many2one('ir.attachment',"UUID")
    invoice_id = fields.Many2one('account.move',"Factura")
    payment_id = fields.Many2one('account.payment',"Pago")
    date = fields.Date("Fecha")
    #partner_id = fields.Many2one("res.partner","Client")
    client_name = fields.Char("Cliente")
    amount = fields.Float("Monto")
    reconcilled = fields.Boolean("¿Está conciliada?")
    moneda = fields.Char("Moneda")

    folio_fiscal = fields.Char("Folio Fiscal")
    folio_factura = fields.Char("Folio factura")
    forma_pago_id = fields.Many2one('catalogo.forma.pago', string='Forma de pago')
    methodo_pago = fields.Selection(
        selection=[('PUE', _('Pago en una sola exhibición')),
                   ('PPD', _('Pago en parcialidades o diferido')),],
        string=_('Método de pago'), 
    )
    uso_cfdi_id = fields.Many2one('catalogo.uso.cfdi', string='Uso CFDI (cliente)')

    numero_cetificado = fields.Char("Numero cetificado")
    fecha_certificacion = fields.Char("Fecha certificacion")
    selo_digital_cdfi = fields.Char("Sello digital CFDI")
    selo_sat = fields.Char("Sello SAT")
    tipocambio = fields.Char("Tipo cambio")
    tipo_comprobante = fields.Selection(
        selection=[('I', 'Ingreso'), 
                   ('E', 'Egreso'),
                   ('P', 'Pago'),
                   ('N', 'Nomina'),
                    ('T', 'Traslado'),],
        string=_('Tipo de comprobante'),
    )
    fecha_factura = fields.Datetime(string=_('Fecha Factura'))
    number_folio = fields.Char(string=_('Folio'))
    invoice_type = fields.Char("Invoice Type")
    payment_type = fields.Char("Payment Type")
    client_rfc = fields.Char("RFC")

    def action_reconcile(self):
        self.ensure_one()
        invoice = self.invoice_id
        payment = self.payment_id
        if not invoice and not payment:
            raise UserError("Seleccionar primero la factura/pago y posteriormente reconciliar con el XML.")

        if invoice:
            if self.env['ir.config_parameter'].sudo().get_param('l10n_mx_sat_sync_itadmin.tipo_conciliacion') == '01':
               if invoice.amount_total != self.amount:
                   raise UserError("El total de la factura y el XML son distintos")
            else:
               diff = self.env['ir.config_parameter'].sudo().get_param('l10n_mx_sat_sync_itadmin.rango')
               if (invoice.amount_total < (self.amount - float(diff))) or  (invoice.amount_total > (self.amount + float(diff))):
                   raise UserError("El total de la factura no está dentro del rango permitido")
            invoice.write({'folio_fiscal': self.folio_fiscal,
                           'forma_pago_id' : self.forma_pago_id,
                           'methodo_pago' : self.methodo_pago,
                           'uso_cfdi_id' : self.uso_cfdi_id,
                           'numero_cetificado' : self.numero_cetificado,
                           'fecha_certificacion' : self.fecha_certificacion,
                           'fecha_factura' : self.fecha_factura,
                           'selo_digital_cdfi' : self.selo_digital_cdfi,
                           'selo_sat' : self.selo_sat,
                           'tipocambio' : self.tipocambio,
                           'tipo_comprobante': self.tipo_comprobante,
                           'factura_cfdi': True,
                           'moneda': self.moneda,
                           #'number_folio': self.folio_factura,
                           'estado_factura': 'factura_correcta',
                           })
            self.attachment_id.write({'creado_en_odoo':True, 'invoice_ids':[(6,0, [invoice.id])], 'res_id': invoice.id, 'res_model': invoice._name,})
#            _logger.info("Factura conciliada")
            self.write({'reconcilled':True})
        if payment:
            if self.env['ir.config_parameter'].sudo().get_param('l10n_mx_sat_sync_itadmin.tipo_conciliacion') == '01':
               if abs(payment.amount_company_currency_signed) != self.amount:
                   raise UserError("El total de la factura y el XML son distintos")
            else:
               diff = self.env['ir.config_parameter'].sudo().get_param('l10n_mx_sat_sync_itadmin.rango')
               if  abs(payment.amount_company_currency_signed) < self.amount - float(diff) or abs(payment.amount_company_currency_signed) > self.amount + float(diff):
                   raise UserError("El total de la factura no está dentro del rango permitido")

            payment.write({'folio_fiscal': self.folio_fiscal,
                           'fecha_pago' :self.fecha_factura,
                           'estado_pago': 'pago_correcto',
                           })
            self.attachment_id.write({'creado_en_odoo':True, 'payment_ids':[(6,0, [payment.id])], 'res_id': payment.id, 'res_model': payment._name,})
#            _logger.info("Factura reconciliada")
            self.write({'reconcilled':True})
        return
