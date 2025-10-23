import json
import base64
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class OdashPdfReport(models.Model):
    _name = 'odash.pdf.report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dashboard PDF Report Configuration'
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(string='Report Name', required=True, help="Name of the PDF report configuration")
    active = fields.Boolean(string='Active', default=True, help="Whether this report configuration is active")
    
    # Report Configuration
    description = fields.Text(string='Description', help="Description of what this report contains")
    
    # Scheduling Configuration
    period = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ], string='Sending Period', required=True, default='weekly', help="How often to send the report")
    
    send_time = fields.Float(
        string='Send Time (Hour)',
        default=9.0,
        help="Time of day to send the report (24h format, e.g., 9.5 = 9:30 AM)"
    )
    
    # Weekly specific
    weekday = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'), 
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string='Day of Week', default='0', help="Day of week for weekly reports")
    
    # Monthly specific
    day_of_month = fields.Integer(
        string='Day of Month',
        default=1,
        help="Day of month for monthly/quarterly reports (1-28)"
    )
    
    # Recipients Configuration
    recipient_user_ids = fields.Many2many(
        comodel_name='res.users',
        string='Recipient Users',
        domain=[('share', '=', False)],
        help="Users who will receive the PDF report"
    )
    
    recipient_emails = fields.Text(
        string='Additional Email Recipients',
        help="Additional email addresses (one per line) to send the report to"
    )
    
    # Pages Configuration
    page_ids = fields.Many2many(
        comodel_name='odash.config',
        string='Dashboard Pages',
        domain=[('is_page_config', '=', True)],
        help="Dashboard pages to include in the PDF report"
    )
    
    include_all_pages = fields.Boolean(
        string='Include All Pages',
        default=False,
        help="Include all available dashboard pages (ignores specific page selection)"
    )
    
    # Execution tracking
    last_sent_date = fields.Datetime(string='Last Sent Date', readonly=True)
    next_send_date = fields.Datetime(string='Next Send Date', compute='_compute_next_send_date', store=True)
    send_count = fields.Integer(string='Send Count', default=0, readonly=True, help="Number of times this report has been sent")
    
    # Status
    last_execution_status = fields.Selection([
        ('success', 'Success'),
        ('error', 'Error'),
        ('pending', 'Pending'),
    ], string='Last Execution Status', readonly=True)
    
    last_error_message = fields.Text(string='Last Error Message', readonly=True)

    @api.constrains('day_of_month')
    def _check_day_of_month(self):
        for record in self:
            if record.day_of_month < 1 or record.day_of_month > 28:
                raise ValidationError(_("Day of month must be between 1 and 28 to ensure it exists in all months."))

    @api.constrains('send_time')
    def _check_send_time(self):
        for record in self:
            if record.send_time < 0 or record.send_time >= 24:
                raise ValidationError(_("Send time must be between 0 and 23.99 (24h format)."))

    @api.constrains('recipient_user_ids', 'recipient_emails')
    def _check_recipients(self):
        for record in self:
            if not record.recipient_user_ids and not record.recipient_emails:
                raise ValidationError(_("At least one recipient (user or email) must be specified."))

    @api.constrains('page_ids', 'include_all_pages')
    def _check_pages(self):
        for record in self:
            if not record.include_all_pages and not record.page_ids:
                raise ValidationError(_("Either select specific pages or enable 'Include All Pages'."))

    @api.depends('period', 'weekday', 'day_of_month', 'send_time', 'last_sent_date')
    def _compute_next_send_date(self):
        for record in self:
            if not record.active:
                record.next_send_date = False
                continue
                
            now = datetime.now()
            base_date = record.last_sent_date or now
            
            # Calculate next send date based on period
            if record.period == 'daily':
                next_date = base_date + timedelta(days=1)
            elif record.period == 'weekly':
                # Find next occurrence of the specified weekday
                days_ahead = int(record.weekday) - base_date.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                next_date = base_date + timedelta(days=days_ahead)
            elif record.period == 'monthly':
                next_date = base_date + relativedelta(months=1)
                next_date = next_date.replace(day=record.day_of_month)
            elif record.period == 'quarterly':
                next_date = base_date + relativedelta(months=3)
                next_date = next_date.replace(day=record.day_of_month)
            else:
                next_date = False
            
            if next_date:
                # Set the time
                hour = int(record.send_time)
                minute = int((record.send_time - hour) * 60)
                next_date = next_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            record.next_send_date = next_date

    def get_pages_to_include(self):
        """Get the list of pages to include in the report"""
        self.ensure_one()
        if self.include_all_pages:
            return self.env['odash.config'].search([('is_page_config', '=', True)], order='sequence, name')
        else:
            return self.page_ids.sorted(lambda p: (p.sequence, p.name))

    def get_all_recipients(self):
        """Get all recipients (users + additional emails) for this report"""
        self.ensure_one()
        recipients = []
        
        # Add user emails
        for user in self.recipient_user_ids:
            if user.email:
                recipients.append({
                    'email': user.email,
                    'name': user.name,
                    'user_id': user.id,
                    'lang': user.lang,
                })
        
        # Add additional emails
        if self.recipient_emails:
            for email in self.recipient_emails.strip().split('\n'):
                email = email.strip()
                if email and '@' in email:
                    recipients.append({
                        'email': email,
                        'name': email.split('@')[0],
                        'user_id': False,
                        'lang': self.env.user.lang or 'en_US',
                    })
        
        return recipients

    def action_send_now(self):
        """Manual action to send the report immediately"""
        self.ensure_one()
        try:
            self._generate_and_send_report()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('PDF report sent successfully!'),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f"Error sending PDF report {self.name}: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Failed to send PDF report: %s') % str(e),
                    'type': 'danger',
                }
            }

    def action_preview_report(self):
        """Generate and download a preview of the PDF report"""
        self.ensure_one()
        try:
            pdf_data = self._generate_pdf_report()
            
            # Create attachment for download
            filename = f"{self.name}_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(pdf_data),
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'self',
            }
        except Exception as e:
            _logger.error(f"Error generating PDF preview for {self.name}: {str(e)}")
            raise UserError(_('Failed to generate PDF preview: %s') % str(e))

    def _generate_pdf_report(self):
        """Generate the PDF report content"""
        self.ensure_one()
        return self.env['odash.pdf.generator'].sudo().generate_dashboard_pdf(self)

    def _generate_and_send_report(self):
        """Generate PDF and send via email"""
        self.ensure_one()
        
        try:
            # Generate PDF
            pdf_data = self._generate_pdf_report()
            
            # Get recipients
            recipients = self.get_all_recipients()
            if not recipients:
                raise UserError(_("No valid recipients found for report '%s'") % self.name)
            
            # Send email to each recipient
            for recipient in recipients:
                self._send_email_with_pdf(recipient, pdf_data)
            
            # Update tracking fields
            self.write({
                'last_sent_date': datetime.now(),
                'send_count': self.send_count + 1,
                'last_execution_status': 'success',
                'last_error_message': False,
            })
            
            _logger.info(f"PDF report '{self.name}' sent successfully to {len(recipients)} recipients")
            
        except Exception as e:
            error_msg = str(e)
            self.write({
                'last_execution_status': 'error',
                'last_error_message': error_msg,
            })
            _logger.error(f"Error generating/sending PDF report '{self.name}': {error_msg}")
            raise

    def _send_email_with_pdf(self, recipient, pdf_data):
        """Send email with PDF attachment to a specific recipient"""
        self.ensure_one()
        
        try:
            # Get the email template
            template = self.env.ref('odashboard.mail_template_pdf_report')
            
            # Create PDF attachment
            filename = f"Dashboard_Report_{self.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(pdf_data),
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            
            # Prepare email context
            email_context = {
                'recipient_name': recipient['name'],
                'recipient_lang': recipient['lang'],
            }
            
            # Send email
            template.with_context(email_context).send_mail(
                self.id,
                email_values={
                    'email_to': recipient['email'],
                    'attachment_ids': [(6, 0, [attachment.id])],
                    'email_from': self.env.company.email
                },
                force_send=True
            )
            
            _logger.info(f"PDF report sent successfully to {recipient['email']}")
            
        except Exception as e:
            _logger.error(f"Error sending email to {recipient['email']}: {str(e)}")
            raise

    @api.model
    def cron_send_scheduled_reports(self):
        """Cron job to send scheduled reports"""
        now = datetime.now()
        
        # Find reports that should be sent now
        reports_to_send = self.search([
            ('active', '=', True),
            ('next_send_date', '<=', now),
        ])
        
        _logger.info(f"Found {len(reports_to_send)} PDF reports to send")
        
        for report in reports_to_send:
            try:
                report._generate_and_send_report()
            except Exception as e:
                _logger.error(f"Failed to send scheduled PDF report '{report.name}': {str(e)}")
                # Continue with other reports even if one fails
                continue
