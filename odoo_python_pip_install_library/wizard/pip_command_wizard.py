########################################################################
#                                                                      #
#     ------------------------ODOO WAVES----------------------         #
#     --------------odoowaves.solution@gmail.com--------------         #
#                                                                      #
########################################################################
from odoo import fields, models
import subprocess
import logging
_logger = logging.getLogger(__name__)


class PipCommands(models.TransientModel):
    _name = 'pip.command'
    _description = 'Install python library'
    
    library_name = fields.Char('Library Name')
    pip_versions = fields.Selection(selection=[('pip', 'pip'),('pip3', 'pip3')],string='Pip versions',default='pip3', required=True,)

    def install_button(self):
        msg = ''
        try:
            result = subprocess.run([self.pip_versions, 'install', self.library_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            output = result.stdout.decode('utf-8').replace('\n', '<br>')
            msg = f'<div class="alert alert-success text-start" role="alert">{output}</div>'
        except subprocess.CalledProcessError as e:
            # Handle errors here
            output = e.stderr.decode('utf-8').replace('\n', '<br>')
            msg = f'<div class="alert alert-danger text-start" role="alert">Error : {output}</div>'
        if not msg:
            msg = f'<div class="alert alert-info text-start" role="alert">Nothing To install</div>'
        message_id = self.env['message.wizard'].create({'message': msg})
        return {
            'name': 'Message',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'message.wizard',
            'res_id': message_id.id,
            'target': 'new'
        }
 