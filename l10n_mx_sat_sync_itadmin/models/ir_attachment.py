# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
import base64
from lxml import etree
import requests
from lxml.objectify import fromstring
import io
import logging
from zipfile import ZipFile
from collections import defaultdict
from odoo.exceptions import AccessError

import logging
_logger = logging.getLogger(__name__)

from .special_dict import CaselessDictionary

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.depends('invoice_ids')
    def _compute_account_invoice_count(self):
        for attach in self:
            try:
                attach.invoice_count = len(attach.invoice_ids)
            except Exception:
                pass
            
    @api.depends('payment_ids')
    def _compute_account_payment_count(self):
        for attach in self:
            try:
                attach.payment_count = len(attach.payment_ids)
            except Exception:
                pass
                
    cfdi_uuid = fields.Char("CFDI UUID", copy=False)
    # cfdi_type = fields.Selection([('E','Emisor'),('R','Receptor')],"CFDI Invoice Type", copy=False)
    cfdi_type = fields.Selection([
        ('I', 'Facturas de clientes'),  # customer invoice, Emisor.RFC=myself.VAT, Customer invoice
        ('SI', 'Facturas de proveedor'),  # Emisor.RFC!=myself.VAT, Supplier bill
        ('E', 'Notas de crédito clientes'),  # customer credit note, Emisor.RFC=myself.VAT, Customer credit note
        ('SE', 'Notas de crédito proveedor'),  # Emisor.RFC!=myself.VAT, Supplier credit note
        ('P', 'REP de clientes'),  # Emisor.RFC=myself.VAT, Customer payment receipt
        ('SP', 'REP de proveedores'),  # Emisor.RFC!=myself.VAT, Supplier payment receipt
        ('N', 'Nominas de empleados'),  # currently we shall not do anythong with this type of cfdi, Customer Payslip
        ('SN', 'Nómina propia'),  # currently we shall not do anythong with this type of cfdi, Supplier Payslip
        ('T', 'Factura de traslado cliente'),
        # currently we shall not do anythong with this type of cfdi, WayBill Customer
        ('ST', 'Factura de traslado proveedor'), ],
        # currently we shall not do anythong with this type of cfdi, WayBill Supplier
        "Tipo de comprobante",
        copy=False)

    date_cfdi = fields.Date('Fecha')
    rfc_tercero = fields.Char("RFC tercero")
    nombre_tercero = fields.Char("Nombre tercero")
    cfdi_total = fields.Float("Importe")
    creado_en_odoo = fields.Boolean("Creado en odoo", copy=False)
    invoice_ids = fields.One2many("account.move", 'attachment_id', "Facturas")
    invoice_count = fields.Integer(compute='_compute_account_invoice_count', string='# de facturas', store=True)

    payment_ids = fields.One2many("account.payment", 'attachment_id', "Pagos")
    payment_count = fields.Integer(compute='_compute_account_payment_count', string='# de pagos', store=True)

    serie_folio = fields.Char("Folio")
    estado = fields.Char("Estado")
    uso_cfdi = fields.Char("Uso CFDI")
    forma_pago = fields.Selection(
        selection=[('01', '01 - Efectivo'),
                   ('02', '02 - Cheque nominativo'),
                   ('03', '03 - Transferencia electrónica de fondos'),
                   ('04', '04 - Tarjeta de Crédito'),
                   ('05', '05 - Monedero electrónico'),
                   ('06', '06 - Dinero electrónico'),
                   ('08', '08 - Vales de despensa'),
                   ('12', '12 - Dación en pago'),
                   ('13', '13 - Pago por subrogación'),
                   ('14', '14 - Pago por consignación'),
                   ('15', '15 - Condonación'),
                   ('17', '17 - Compensación'),
                   ('23', '23 - Novación'),
                   ('24', '24 - Confusión'),
                   ('25', '25 - Remisión de deuda'),
                   ('26', '26 - Prescripción o caducidad'),
                   ('27', '27 - A satisfacción del acreedor'),
                   ('28', '28 - Tarjeta de débito'),
                   ('29', '29 - Tarjeta de servicios'),
                   ('30', '30 - Aplicación de anticipos'),
                   ('31', '31 - Intermediario pagos'),
                   ('99', '99 - Por definir'), ],
        string="Forma de pago",
    )
    methodo_pago = fields.Selection(
        selection=[('PUE', 'PUE'),
                   ('PPD', 'PPD'), ],
        string="Método de pago",
    )
    tipo_relacion = fields.Char("Tipo de Relación")
    cfdi_condicion_pago = fields.Char("Condición de pago")
    cfdi_subtotal = fields.Float("Subtotal")
    cfdi_descuento = fields.Float("Descuento")
    cfdi_iva = fields.Float("IVA")
    cfdi_isr = fields.Float("ISR")
    cfdi_ieps = fields.Float("IEPS")
    cfdi_iva_ret = fields.Float("Ret IVA")
    cfdi_isr_ret = fields.Float("Ret ISR")
    cfdi_ieps_ret = fields.Float("Ret IEPS")
    cfdi_moneda = fields.Char("Moneda")
    cfdi_reg_fiscal = fields.Char("Reg Fiscal")

    def _read_group_allowed_fields(self):
        return super(IrAttachment, self)._read_group_allowed_fields() + ['creado_en_odoo', 'date_cfdi',
                                                                         'nombre_tercero', 'serie_folio', 'create_date',
                                                                         'rfc_tercero', 'cfdi_uuid', 'cfdi_type',
                                                                         'cfdi_total']

    @api.model
    def create(self, vals):
        ctx = self._context.copy()
        if ctx.get('is_fiel_attachment'):
            datas = vals.get('datas')
            if datas:
                xml_content = base64.b64decode(datas)
                if b'xmlns:schemaLocation' in xml_content:
                    xml_content = xml_content.replace(b'xmlns:schemaLocation', b'xsi:schemaLocation')
                try:
                    tree = etree.fromstring(xml_content)
                except Exception as e:
                    _logger.error('error : ' + str(e))
                    raise
                try:
                    ns = tree.nsmap
                    ns.update({'re': 'http://exslt.org/regular-expressions'})
                except Exception:
                    ns = {'re': 'http://exslt.org/regular-expressions'}

                tfd_namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
                tfd_elements = tree.xpath("//tfd:TimbreFiscalDigital", namespaces=tfd_namespace)
                tfd_uuid = tfd_elements and tfd_elements[0].get('UUID')
                cfdi_type = vals.get('cfdi_type', 'I')

                if cfdi_type in ['I', 'E', 'P', 'N', 'T']:
                    element_tag = 'Receptor'
                else:
                    element_tag = 'Emisor'
                try:
                    elements = tree.xpath("//*[re:test(local-name(), '%s','i')]" % (element_tag), namespaces=ns)
                except Exception:
                    _logger.info("No encontró al Emisor/Receptor")
                    elements = None
                client_rfc, client_name = '', ''
                if elements:
                    attrib_dict = CaselessDictionary(dict(elements[0].attrib))
                    client_rfc = attrib_dict.get('rfc')
                    client_name = attrib_dict.get('nombre')

                vals.update({
                    'cfdi_uuid': tfd_uuid,
                    'rfc_tercero': client_rfc,
                    'nombre_tercero': client_name,
                    'cfdi_total': tree.get('Total', tree.get('total')),
                    'date_cfdi': tree.get('Fecha', tree.get('fecha')),
                    'serie_folio': tree.get('Folio', tree.get('folio'))
                })
        return super(IrAttachment, self).create(vals)

    def action_view_payments(self):
        payments = self.mapped('payment_ids')
        if payments and payments[0].payment_type == 'outbound':
            action = self.env.ref('account.action_account_payments_payable').sudo().read()[0]
        else:
            action = self.env.ref('account.action_account_payments').sudo().read()[0]

        if len(payments) > 1:
            action['domain'] = [('id', 'in', payments.ids)]
        elif len(payments) == 1:
            action['views'] = [(self.env.ref('account.view_account_payment_form').sudo().id, 'form')]
            action['res_id'] = payments.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        if self.cfdi_type == 'I':
           action = self.env.ref('account.action_move_out_invoice_type').sudo().read()[0]
           if len(invoices) > 1:
               action['domain'] = [('id', 'in', invoices.ids)]
               action['view_mode'] = 'tree'
           elif len(invoices) == 1:
               action['views'] = [(self.env.ref('account.view_move_form').sudo().id, 'form')]
               action['res_id'] = invoices.ids[0]
           else:
               action = {'type': 'ir.actions.act_window_close'}
        else:
           action = self.env.ref('account.action_move_in_invoice_type').sudo().read()[0]
           if len(invoices) > 1:
               action['domain'] = [('id', 'in', invoices.ids)]
               action['view_mode'] = 'tree'
           elif len(invoices) == 1:
               action['views'] = [(self.env.ref('account.view_move_form').sudo().id, 'form')]
               action['res_id'] = invoices.ids[0]
           else:
               action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_renmove_invoice_link(self):
        for attach in self:
            if attach.invoice_ids:
                attach.invoice_ids.write({'attachment_id': False,
                                          'tipo_comprobante': '',
                                          'folio_fiscal': '',
                                          'forma_pago_id': None,
                                          'methodo_pago': '',
                                          'uso_cfdi_id': None,
                                          'numero_cetificado': '',
                                          'fecha_certificacion': '',
                                          'selo_digital_cdfi': '',
                                          'selo_sat': '',
                                          'tipocambio': '',
                                          'moneda': '',
                                         # 'folio': '',
                                          'estado_factura': 'factura_no_generada'})
            if attach.payment_ids:
                attach.payment_ids.write({'attachment_id': False,
                                          'tipo_comprobante': '',
                                          'folio_fiscal': '',
                                          'forma_pago_id': '',
                                          'methodo_pago': '',
                                          'uso_cfdi_id': '',
                                          'numero_cetificado': '',
                                          'fecha_certificacion': '',
                                          'selo_digital_cdfi': '',
                                          'selo_sat': '',
                                          'tipocambio': '',
                                          'moneda': '',
                                          'folio': '', })
            vals = {'res_id': False, 'res_model': False}
            if attach.creado_en_odoo:
                vals.update({'creado_en_odoo': False})
                # attach.creado_en_odoo=False
            attach.write(vals)
        return True

    @api.model
    def update_status_from_ir_attachment_document(self):
        attchment_list = self.env['ir.attachment'].sudo().search([('creado_en_odoo', '=', False)])
        for attchment in attchment_list:
            if attchment.cfdi_uuid and attchment.cfdi_type:
                if attchment.cfdi_type == 'I' or attchment.cfdi_type == 'E':
                    for uu in [attchment.cfdi_uuid, attchment.cfdi_uuid.lower(), attchment.cfdi_uuid.upper()]:
                       customer_invoices = self.env['account.move'].search([('folio_fiscal', '=', uu)],limit=1)
                       if customer_invoices:
                           customer_invoices.write({'attachment_id': attchment.id})
                           attchment.creado_en_odoo = True

                if attchment.cfdi_type == 'SI' or attchment.cfdi_type == 'SE':
                    for uu in [attchment.cfdi_uuid, attchment.cfdi_uuid.lower(), attchment.cfdi_uuid.upper()]:
                       customer_invoices = self.env['account.move'].search([('folio_fiscal', '=', uu)],limit=1)
                       if customer_invoices:
                           customer_invoices.write({'attachment_id': attchment.id})
                           attchment.creado_en_odoo = True

                if attchment.cfdi_type == 'P' or attchment.cfdi_type == 'SP':
                    for uu in [attchment.cfdi_uuid, attchment.cfdi_uuid.lower(), attchment.cfdi_uuid.upper()]:
                       customer_invoices = self.env['account.payment'].search([('folio_fiscal', '=', uu)],limit=1)
                       if customer_invoices:
                           customer_invoices.write({'attachment_id': attchment.id})
                           attchment.creado_en_odoo = True

    def action_extract_zip(self):
        fp = io.BytesIO()
        with ZipFile(fp, mode="w") as zf:
            for att in self:
                zf.writestr(att.name, base64.b64decode(att.datas))
        file_name = fields.Date.to_string(fields.Date.today()) + '.zip'
        zip_datas = base64.b64encode(fp.getvalue())
        attachment = self.env['ir.attachment'].with_context(is_fiel_attachment=False).create({
            'name': file_name,
            'datas': zip_datas,
          #  'datas_fname': file_name,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': "/web/content/?model=ir.attachment&id=" + str(
                attachment.id) + "&field=datas&download=true&filename_field=name",
            'target': 'download',
        }

    def action_download_state(self):
        for attach in self:
            if attach.cfdi_type == 'I' or attach.cfdi_type == 'E' or  attach.cfdi_type == 'P' or attach.cfdi_type == 'N' or attach.cfdi_type == 'T':
                try:
                    total = attach.cfdi_total if not attach.cfdi_type == 'P' else 0
                    status = self.get_sat_status(attach.company_id.vat, attach.rfc_tercero, total, attach.cfdi_uuid)
                except Exception as e:
                    _logger.info("Falla al descargar estado del SAT: %s", str(e))
                    continue
                attach.estado = status
            elif attach.cfdi_type == 'SI' or attach.cfdi_type == 'SE' or  attach.cfdi_type == 'SP' or attach.cfdi_type == 'SN' or attach.cfdi_type == 'ST':
                try:
                    total = attach.cfdi_total if not attach.cfdi_type == 'SP' else 0
                    status = self.get_sat_status(attach.rfc_tercero, attach.company_id.vat, total, attach.cfdi_uuid)
                except Exception as e:
                    _logger.info("Falla al descargar estado del SAT: %s", str(e))
                    continue
                attach.estado = status
        return True

    def get_sat_status(self, emisor_rfc, receptor_rfc, total, uuid):
        url = 'https://consultaqr.facturaelectronica.sat.gob.mx/ConsultaCFDIService.svc?wsdl'
        headers = {'SOAPAction': 'http://tempuri.org/IConsultaCFDIService/Consulta', 'Content-Type': 'text/xml; charset=utf-8'}
        template = """<?xml version="1.0" encoding="UTF-8"?>
        <SOAP-ENV:Envelope xmlns:ns0="http://tempuri.org/" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
           <SOAP-ENV:Header/>
           <ns1:Body>
              <ns0:Consulta>
                 <ns0:expresionImpresa>${data}</ns0:expresionImpresa>
              </ns0:Consulta>
           </ns1:Body>
        </SOAP-ENV:Envelope>"""
        namespace = {'a': 'http://schemas.datacontract.org/2004/07/Sat.Cfdi.Negocio.ConsultaCfdi.Servicio'}
        params = '?re=%s&amp;rr=%s&amp;tt=%s&amp;id=%s' % (
            tools.html_escape(emisor_rfc or ''),
            tools.html_escape(receptor_rfc or ''),
            total or 0.0, uuid or '')
        soap_env = template.format(data=params)
        soap_xml = requests.post(url, data=soap_env, headers=headers, timeout=20)
        response = fromstring(soap_xml.text)
        fetched_status = response.xpath('//a:Estado', namespaces=namespace)
        status = fetched_status[0] if fetched_status else ''
        return status

    @api.model
    def check(self, mode, values=None):
        """ Restricts the access to an ir.attachment, according to referred mode """
        if self.env.is_superuser():
            return True
        # Always require an internal user (aka, employee) to access to a attachment
        if not (self.env.is_admin() or self.env.user.has_group('base.group_user')):
            raise AccessError(_("Sorry, you are not allowed to access this document."))
        # collect the records to check (by model)
        model_ids = defaultdict(set)            # {model_name: set(ids)}
        if self:
            # DLE P173: `test_01_portal_attachment`
            self.env['ir.attachment'].flush_model(['res_model', 'res_id', 'create_uid', 'public', 'res_field'])
            self._cr.execute('SELECT res_model, res_id, create_uid, public, res_field, cfdi_uuid FROM ir_attachment WHERE id IN %s', [tuple(self.ids)])
            for res_model, res_id, create_uid, public, res_field, cfdi_uuid in self._cr.fetchall():
                if cfdi_uuid:
                    continue
                if public and mode == 'read':
                    continue
                if not self.env.is_system() and (res_field or (not res_id and create_uid != self.env.uid)):
                    raise AccessError(_("Sorry, you are not allowed to access this document."))
                if not (res_model and res_id):
                    continue
                model_ids[res_model].add(res_id)
        if values and values.get('res_model') and values.get('res_id'):
            model_ids[values['res_model']].add(values['res_id'])

        # check access rights on the records
        for res_model, res_ids in model_ids.items():
            # ignore attachments that are not attached to a resource anymore
            # when checking access rights (resource was deleted but attachment
            # was not)
            if res_model not in self.env:
                continue
            if res_model == 'res.users' and len(res_ids) == 1 and self.env.uid == list(res_ids)[0]:
                # by default a user cannot write on itself, despite the list of writeable fields
                # e.g. in the case of a user inserting an image into his image signature
                # we need to bypass this check which would needlessly throw us away
                continue
            records = self.env[res_model].browse(res_ids).exists()
            # For related models, check if we can write to the model, as unlinking
            # and creating attachments can be seen as an update to the model
            access_mode = 'write' if mode in ('create', 'unlink') else mode
            records.check_access_rights(access_mode)
            records.check_access_rule(access_mode)

    @api.model
    def l10n_mx_edi_get_tfd_etree(self, cfdi):
        '''Get the TimbreFiscalDigital node from the cfdi.

        :param cfdi: The cfdi as etree
        :return: the TimbreFiscalDigital node
        '''
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = 'tfd:TimbreFiscalDigital[1]'
        namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
        for Complemento in cfdi.Complemento:
            node = Complemento.xpath(attribute, namespaces=namespace)
            if node:
                break
        return node[0] if node else None

    @api.model
    def update_extra_info_xml(self):
        for attach in self:
            wrongfiles = {}
            attachments = {}
            attachment_uuids = {}
            attach_obj = self.env['ir.attachment']
            invoice_obj = self.env['account.move']
            payment_obj = self.env['account.payment']
            company = self.env.company
            company_vat = attach.company_id.vat
            company_id = attach.company_id.id
            NSMAP = {
                     'xsi':'http://www.w3.org/2001/XMLSchema-instance',
                     'cfdi':'http://www.sat.gob.mx/cfd/3', 
                     'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
                     'pago10': 'http://www.sat.gob.mx/Pagos',
                     }
            try:
                xml_str = base64.b64decode(attach.datas)
                # Fix the CFDIs emitted by the SAT
                xml_str = xml_str.replace(b'xmlns:schemaLocation', b'xsi:schemaLocation')
                xml = fromstring(xml_str)
                tree = etree.fromstring(xml_str)
            except Exception as e:
                _logger.error('error : ' + str(e))

            xml_tfd = self.l10n_mx_edi_get_tfd_etree(xml)

            xml_uuid = False if xml_tfd is None else xml_tfd.get('UUID', '')

            if not xml_uuid:
                msg = {'signed': True, 'xml64': True}
                wrongfiles.update({key: msg})
                continue
            else:
                xml_uuid = xml_uuid.upper()

            cfdi_type = xml.get('TipoDeComprobante', 'I')
            receptor = xml.Receptor.attrib or {}
            receptor_rfc = receptor.get('Rfc','')
            if receptor_rfc == company_vat:
                    cfdi_type = 'S'+cfdi_type

            try:
                ns = tree.nsmap
                ns.update({'re': 'http://exslt.org/regular-expressions'})
            except Exception:
                ns = {'re': 'http://exslt.org/regular-expressions'}

            cfdi_version = tree.get("Version",'4.0')
            if cfdi_version=='4.0':
                NSMAP.update({'cfdi':'http://www.sat.gob.mx/cfd/4', 'pago20': 'http://www.sat.gob.mx/Pagos20',})
            else:
                NSMAP.update({'cfdi':'http://www.sat.gob.mx/cfd/3', 'pago10': 'http://www.sat.gob.mx/Pagos',})

            if cfdi_type in ['I','E','P','N','T']:
                element_tag = 'Receptor'
            else:
                element_tag = 'Emisor'
            try:
                elements = tree.xpath("//*[re:test(local-name(), '%s','i')]"%(element_tag), namespaces=ns)
            except Exception:
                elements = None

            client_rfc, client_name = '', ''
            if elements:
                attrib_dict = CaselessDictionary(dict(elements[0].attrib))
                client_rfc = attrib_dict.get('rfc') 
                client_name = attrib_dict.get('nombre')
                cfdi_reg_fiscal = attrib_dict.get('regimenfiscalreceptor')
                if not cfdi_reg_fiscal:
                    cfdi_reg_fiscal = attrib_dict.get('regimenfiscal')

            monto_total = 0
            cfdi_iva = cfdi_isr = cfdi_ieps = cfdi_iva_ret = cfdi_isr_ret = cfdi_ieps_ret = 0
            if cfdi_type=='P' or cfdi_type=='SP':
                cfdi_moneda = tree.get("Moneda", '')
                Complemento = tree.findall('cfdi:Complemento', NSMAP)
                for complementos in Complemento:
                       methodo_pago = None
                       if cfdi_version == '4.0':
                          pagos = complementos.find('pago20:Pagos', NSMAP)
                          pago = pagos.find('pago20:Totales', NSMAP)
                          monto_total = pago.attrib['MontoTotalPagos']
                          forma = pagos.find('pago20:Pago', NSMAP)
                          forma_pago = forma.attrib['FormaDePagoP']
                       else:
                          pagos = complementos.find('pago10:Pagos', NSMAP)
                          try:
                             pago = pagos.find('pago10:Pago',NSMAP)
                             monto_total = pago.attrib['Monto']
                             forma_pago = pago.attrib['FormaDePagoP']
                          except Exception as e:
                             for payment in pagos.find('pago10:Pago',NSMAP):
                                monto_total += float(payment.attrib['Monto'])
                                forma_pago = pago.attrib['FormaDePagoP']
                       if pagos is not None:
                           break
            else:
                monto_total = tree.get('Total', tree.get('total'))
                forma_pago = tree.get("FormaPago", '')
                methodo_pago = tree.get("MetodoPago", '')
                cfdi_moneda = tree.get("Moneda", '')

                todos_impuestos = tree.find('cfdi:Impuestos', NSMAP)
                if todos_impuestos is not None:
                   traslados = todos_impuestos.find('cfdi:Traslados', NSMAP)
                   retenciones = todos_impuestos.find('cfdi:Retenciones', NSMAP)
                   if traslados is not None:
                      for traslado in traslados:
                          if traslado.attrib['Impuesto'] == '002' and traslado.attrib['TipoFactor'] != "Exento":
                             cfdi_iva += float(traslado.attrib['Importe'])
                          if traslado.attrib['Impuesto'] == '001':
                             cfdi_isr += float(traslado.attrib['Importe'])
                          if traslado.attrib['Impuesto'] == '003':
                             cfdi_ieps += float(traslado.attrib['Importe'])
                   if retenciones is not None:
                      for retencion in retenciones:
                          if retencion.attrib['Impuesto'] == '002':
                             cfdi_iva_ret += float(retencion.attrib['Importe'])
                          if retencion.attrib['Impuesto'] == '001':
                             cfdi_isr_ret += float(retencion.attrib['Importe'])
                          if retencion.attrib['Impuesto'] == '003':
                             cfdi_ieps_ret += float(retencion.attrib['Importe'])

            receptor = tree.find('cfdi:Receptor', NSMAP)
            uso_cfdi = receptor.attrib['UsoCFDI']

            cfdi_condicion_pago = xml.get('CondicionesDePago', '')
            cfdi_subtotal = xml.get('SubTotal', '')
            cfdi_descuento = xml.get('Descuento', '')

            nodo_relacionado = tree.find('cfdi:CfdiRelacionados', NSMAP)
            if nodo_relacionado:
                    tipo_relacion = nodo_relacionado.attrib['TipoRelacion']
            else:
                    tipo_relacion = ''

            vals = {
                    'methodo_pago' : methodo_pago,
                    'forma_pago' : forma_pago,
                    'uso_cfdi' : uso_cfdi,
                    'tipo_relacion' : tipo_relacion,
                    'cfdi_condicion_pago' : cfdi_condicion_pago,
                    'cfdi_subtotal' : cfdi_subtotal,
                    'cfdi_descuento' : cfdi_descuento,

                    'cfdi_iva' : cfdi_iva,
                    'cfdi_isr' : cfdi_isr,
                    'cfdi_ieps' : cfdi_ieps,
                    'cfdi_iva_ret' : cfdi_iva_ret,
                    'cfdi_isr_ret' : cfdi_isr_ret, 
                    'cfdi_ieps_ret' : cfdi_ieps_ret,

                    'cfdi_moneda' : cfdi_moneda,
                    'cfdi_reg_fiscal' : cfdi_reg_fiscal,
            }
            attach.update(vals)
