import io
import logging
import requests
try:
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    # Old PyPDF2 (<= 1.26.0)
    from PyPDF2 import PdfFileReader as PdfReader
    from PyPDF2 import PdfFileWriter as PdfWriter

from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OdashPdfGenerator(models.AbstractModel):
    _name = 'odash.pdf.generator'
    _description = 'Dashboard PDF Generation Service'

    @api.model
    def generate_dashboard_pdf(self, report_config):
        """
        Generate a PDF report from dashboard pages using the existing PDF server
        
        Args:
            report_config: odash.pdf.report record
            
        Returns:
            bytes: PDF data
        """
        try:
            # Get pages to include
            pages = report_config.get_pages_to_include()
            if not pages:
                raise UserError(_("No pages found to include in the PDF report"))

            # Get PDF server URL
            pdf_server_url = self.env['ir.config_parameter'].sudo().get_param('odashboard.pdf.url', 'https://pdf.odashboard.app')
            
            # Create a merged PDF if multiple pages
            if len(pages) == 1:
                # Single page - use direct PDF generation
                return self._generate_single_page_pdf(pages[0], pdf_server_url)
            else:
                # Multiple pages - generate each page and merge
                return self._generate_multi_page_pdf(pages, pdf_server_url, report_config)
            
        except Exception as e:
            _logger.error(f"Error generating PDF report: {str(e)}")
            raise UserError(_("Failed to generate PDF report: %s") % str(e))

    def _generate_single_page_pdf(self, page, pdf_server_url):
        """Generate PDF for a single dashboard page using the existing PDF server"""
        try:
            # Get the public dashboard URL for this page
            connection_url = self.env['odash.dashboard'].sudo().get_public_dashboard(page.id)
            
            # Add PDF parameter to the URL
            pdf_url = f"{connection_url}&is_pdf=true"
            
            # Call the PDF server
            payload = {"url": pdf_url}
            
            _logger.info(f"Generating PDF for page '{page.name}' using PDF server: {pdf_server_url}")
            
            response = requests.post(
                f"{pdf_server_url}/render", 
                json=payload, 
                timeout=120
            )
            
            if response.status_code != 200:
                error_msg = f"PDF server returned status {response.status_code}"
                _logger.error(f"Error generating PDF for page {page.name}: {error_msg}")
                raise UserError(_("Failed to generate PDF for page '%s': %s") % (page.name, error_msg))
            
            # Check if response is actually PDF content
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('application/pdf'):
                error_msg = f"PDF server returned unexpected content type: {content_type}"
                _logger.error(f"Error generating PDF for page {page.name}: {error_msg}")
                raise UserError(_("Failed to generate PDF for page '%s': %s") % (page.name, error_msg))
            
            _logger.info(f"Successfully generated PDF for page '{page.name}'")
            return response.content
            
        except requests.RequestException as e:
            error_msg = f"PDF service unreachable: {str(e)}"
            _logger.error(f"Error generating PDF for page {page.name}: {error_msg}")
            raise UserError(_("Failed to generate PDF for page '%s': %s") % (page.name, error_msg))

    def _generate_multi_page_pdf(self, pages, pdf_server_url, report_config):
        """Generate and merge PDFs for multiple dashboard pages"""
        try:
            pdf_writer = PdfWriter()
            
            # Generate PDF for each page and merge
            for i, page in enumerate(pages):
                try:
                    # Generate PDF for this page
                    page_pdf_data = self._generate_single_page_pdf(page, pdf_server_url)
                    
                    # Read the PDF data
                    pdf_reader = PdfReader(io.BytesIO(page_pdf_data))
                    
                    # Add all pages from this PDF to the writer
                    for page_num in range(len(pdf_reader.pages)):
                        pdf_writer.add_page(pdf_reader.pages[page_num])
                        
                except Exception as e:
                    _logger.error(f"Error processing page {page.name}: {str(e)}")
                    # Continue with other pages even if one fails
                    continue
            
            # Write the merged PDF to a buffer
            output_buffer = io.BytesIO()
            pdf_writer.write(output_buffer)
            
            # Get the merged PDF data
            merged_pdf_data = output_buffer.getvalue()
            output_buffer.close()

            return merged_pdf_data
            
        except Exception as e:
            raise UserError(_("Failed to merge PDF pages: %s") % str(e))

    @api.model
    def test_pdf_generation(self, page_id=None):
        """Test method to generate a sample PDF using the PDF server"""
        try:
            # Get a test page or use the first available page
            if page_id:
                page = self.env['odash.config'].sudo().browse(page_id)
            else:
                page = self.env['odash.config'].sudo().search([('is_page_config', '=', True)], limit=1)
            
            if not page:
                raise UserError(_("No dashboard pages found for testing"))
            
            # Get PDF server URL
            pdf_server_url = self.env['ir.config_parameter'].sudo().get_param('odashboard.pdf.url', 'https://pdf.odashboard.app')
            
            # Generate test PDF
            pdf_data = self._generate_single_page_pdf(page, pdf_server_url)
            
            _logger.info(f"Test PDF generation successful for page: {page.name}")
            return pdf_data
            
        except Exception as e:
            _logger.error(f"Error in test PDF generation: {str(e)}")
            raise UserError(_("Test PDF generation failed: %s") % str(e))
