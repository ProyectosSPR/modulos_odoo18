# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Odoo OCR Using AI Base',
    'version': '18.0.2.1.0',
    'summary': """
                Odoo OCR Using AI Base is an innovative module that integrates Optical Character Recognition (OCR) technology powered by artificial intelligence (AI) into the Odoo ERP system. This module streamlines data entry processes, enhances accuracy, and improves operational efficiency by automatically extracting and digitizing text from scanned documents, images, and PDFs.
                Odoo OCR AI
                AI-based OCR in Odoo
                Odoo OCR integration
                Odoo OCR document processing
                Odoo AI text recognition
                Odoo OCR AI implementation
                Intelligent OCR Odoo
                Automated OCR Odoo
                Odoo OCR solution
                AI OCR Odoo application
                Odoo OCR AI technology
                Optical Character Recognition
                Odoo OCR
                AI-Driven OCR
                AI Document Processing
                OCR AI Integration
                OCR Invoice & Bills
                OCR Sale Order
                OCR Purchase Order
                OCR Expense
                """,
    'sequence': 10,
    'description': """Odoo OCR Using AI Base is an innovative module that integrates Optical Character Recognition (OCR) technology powered by artificial intelligence (AI) into the Odoo ERP system. This module streamlines data entry processes, enhances accuracy, and improves operational efficiency by automatically extracting and digitizing text from scanned documents, images, and PDFs.""",
    'category': 'Tools',
    'website': "https://www.techultrasolutions.com",
    "author": "TechUltra Solutions Private Limited",
    "company": "TechUltra Solutions Private Limited",
    'live_test_url': 'https://ai.fynix.app/',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        # 'security/security.xml',
        'wizards/import_via_ocr_wizard_view.xml',
        'views/odoo_ocr_ai_config_views.xml',
        'views/odoo_ocr_api_config_view.xml',
    ],
    "images": ["static/description/main_banner.gif"],
    'demo': [],
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}