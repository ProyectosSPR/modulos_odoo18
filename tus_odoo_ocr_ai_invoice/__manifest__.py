# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Odoo OCR Using AI - Invoices & Bills',
    'version': '18.0.2.1.0',
    'summary': 'Leverage the power of AI and Optical Character Recognition (OCR) in Odoo to automate and streamline your invoice processing. This advanced solution uses cutting-edge AI technology to accurately extract and process data from invoices, reducing manual data entry and minimizing errors. Enhance your financial workflows and increase efficiency with Odoo AI-driven OCR capabilities.',
    'sequence': 10,
    'description': """ 
Leverage the power of AI and Optical Character Recognition (OCR) in Odoo to automate and streamline your invoice processing. This advanced solution uses cutting-edge AI technology to accurately extract and process data from invoices, reducing manual data entry and minimizing errors. Enhance your financial workflows and increase efficiency with Odoo's AI-driven OCR capabilities.
        Odoo OCR AI
        Odoo Optical Character Recognition
        AI-based OCR in Odoo
        Odoo OCR integration
        Odoo AI OCR module
        Automated OCR Odoo
        Odoo OCR document processing
        Odoo AI text recognition
        Odoo OCR invoice scanning
        Odoo OCR AI implementation
        OCR automation with Odoo
        Intelligent OCR Odoo
        Odoo OCR solution
        Odoo AI document scanning
        AI OCR Odoo application
        Odoo machine learning OCR
        Odoo OCR AI technology
        Odoo document AI OCR
        Odoo OCR workflow automation
        Odoo AI OCR customization
        Odoo OCR
        AI Invoice Processing
        Invoice OCR
        Optical Character Recognition
        AI-Powered OCR
        Invoice Automation
        Smart Invoice Scanning
        Odoo Invoice Management
        Automated Invoice Data Extraction
        OCR AI Integration
        Invoice Recognition
        AI Document Processing
        OCR for Accounting
        Intelligent Invoice Processing
        AI-Driven OCR
        Invoice Data Capture
        Odoo AI Module
        OCR Invoice Automation
        Digital Invoice Processing
        Machine Learning OCR
     """,
    'category': 'Accounting',
    'website': "https://www.techultrasolutions.com",
    "author": "TechUltra Solutions Private Limited",
    "company": "TechUltra Solutions Private Limited",
    'live_test_url': 'https://ai.fynix.app/',
    'depends': ["account", "tus_odoo_ocr_ai_base"],
    'data': [
        'data/ocr_model_data.xml',
        'views/ocr_ai_invoice_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tus_odoo_ocr_ai_invoice/static/src/xml/**/*',
            'tus_odoo_ocr_ai_invoice/static/src/js/**/*',
        ],
    },
    "images": ["static/description/main_banner.gif"],
    'installable': True,
    'application': True,

    'license': 'OPL-1',
}
