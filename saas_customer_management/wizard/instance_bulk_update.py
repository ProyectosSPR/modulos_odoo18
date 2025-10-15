from odoo import models, fields, api

class InstanceBulkUpdate(models.TransientModel):
    _name = 'saas.instance.bulk.update'
    _description = 'Bulk Update Instance Status'

    instance_ids = fields.Many2many('saas.instance', string='Instances')
    new_status = fields.Selection([
        ('provisioning', 'Provisioning'),
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated')
    ], string='New Status', required=True)
    
    reason = fields.Text(string='Reason for Change')
    
    def action_update_instances(self):
        """Update status for selected instances"""
        for instance in self.instance_ids:
            instance.write({'status': self.new_status})
            # Log the change if needed
            instance.message_post(
                body=f"Status changed to {dict(instance._fields['status'].selection)[self.new_status]} via bulk update. Reason: {self.reason or 'No reason provided'}"
            )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
