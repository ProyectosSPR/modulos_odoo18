# -*- coding: utf-8 -*-

{
    'name': 'Administrador de documentos Digitales',
    'version': '18.0.1.0.0',
    'description': ''' 
                    Descarga los CFDI del portal del SAT a la base de datos de 
                    Odoo para su procesamiento y administracion, se necesita de la libreria de python
                    xmltodict - sudo pip3 install xmltodict 
                    OpenSSL - sudo apt-get install python3-openssl
                    ''',
    'category': 'Accounting',
    'author': 'IT Admin',
    'website': 'www.itadmin.com.mx',
    'depends': [
        'account',
        'purchase',
        # NOTE: The following dependencies may need to be verified/updated for Odoo 18:
        # 'cdfi_invoice',  # Verify if this module exists in Odoo 18 or install the equivalent
        # 'sale_purchase',  # Verify if this module exists in Odoo 18 or install the equivalent
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/l10n_mx_edi_esignature.xml',
        'security/security.xml',
        'data/cron_data.xml',
        'views/ir_attachment_view.xml',
        'views/res_config_settings_view.xml',
        'views/res_company_view.xml',
        'views/esignature_view.xml',
        'views/solicitud_ws.xml',
        'wizard/cfdi_invoice.xml',
        'wizard/import_invoice_process_message.xml',
        'wizard/reconcile_vendor_cfdi_xml_bill.xml',
        'wizard/xml_invoice_reconcile_view.xml',
        'wizard/descarga_x_dia_wizard.xml',
        'wizard/attach_xmls_wizard_view.xml',
        'report/report_facturas_de_clientes_or_proveedores.xml',
        'report/payment_report_from_xml.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'l10n_mx_sat_sync_itadmin/static/src/xml/*.xml',
            'l10n_mx_sat_sync_itadmin/static/src/js/**/*',
            'l10n_mx_sat_sync_itadmin/static/src/css/**/*',
        ],
    },
    'application': False,
    'installable': True,
    'license': 'OPL-1',
}
