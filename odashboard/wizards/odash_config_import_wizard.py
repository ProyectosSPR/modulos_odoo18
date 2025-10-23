import json
import base64
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class OdashConfigImportWizard(models.TransientModel):
    _name = 'odash.config.import.wizard'
    _description = 'Import Dashboard Configurations Wizard'

    import_file = fields.Binary(string='Configuration File', required=True,
                                help="Select the JSON file exported from odashboard")
    filename = fields.Char(string='Filename')
    import_mode = fields.Selection([
        ('merge', 'Merge with Existing Configurations'),
        ('replace', 'Replace All Configurations'),
        ('skip_existing', 'Skip Existing Configurations')
    ], string='Import Mode', default='merge', required=True)

    # Preview fields
    preview_data = fields.Text(string='Preview', readonly=True)
    show_preview = fields.Boolean(string='Show Preview', default=False)

    @api.onchange('import_file')
    def _onchange_import_file(self):
        """Preview the import file content"""
        if self.import_file:
            try:
                file_content = base64.b64decode(self.import_file).decode('utf-8')
                import_data = json.loads(file_content)

                # Validate file structure
                if 'configs' not in import_data:
                    raise ValidationError(_("Invalid file format. Missing 'configs' key."))

                # Create preview
                preview_lines = [
                    f"Export Date: {import_data.get('export_date', 'Unknown')}",
                    f"Odoo Version: {import_data.get('odoo_version', 'Unknown')}",
                    f"Odashboard Version: {import_data.get('odashboard_version', 'Unknown')}",
                    f"Total Configurations: {len(import_data['configs'])}",
                    "",
                    "Configurations to import:"
                ]

                for config in import_data['configs'][:10]:  # Show first 10
                    config_type = "Page" if config.get('is_page_config') else "Component"
                    preview_lines.append(f"- {config.get('name', 'Unnamed')} ({config_type})")

                if len(import_data['configs']) > 10:
                    preview_lines.append(f"... and {len(import_data['configs']) - 10} more")

                self.preview_data = "\n".join(preview_lines)
                self.show_preview = True

            except json.JSONDecodeError:
                raise ValidationError(_("Invalid JSON file format."))
            except Exception as e:
                raise ValidationError(_("Error reading file: %s") % str(e))
        else:
            self.preview_data = ""
            self.show_preview = False

    def action_import(self):
        """Execute the import process"""
        if not self.import_file:
            raise UserError(_("Please select a file to import."))

        try:
            # Decode and parse the file
            file_content = base64.b64decode(self.import_file).decode('utf-8')
            import_data = json.loads(file_content)

            if 'configs' not in import_data:
                raise ValidationError(_("Invalid file format. Missing 'configs' key."))

            # Handle replace mode first
            if self.import_mode == 'replace':
                # Delete all existing configurations
                existing_configs = self.env['odash.config'].search([])
                existing_configs.unlink()
                existing_configs = self.env['odash.config']  # Empty recordset
            else:
                # Get existing configurations for merge/skip modes
                existing_configs = self.env['odash.config'].search([])

            imported_count = 0
            skipped_count = 0

            for config_data in import_data['configs']:
                # Check if configuration already exists (only for non-replace modes)
                existing_config = self.env['odash.config']
                if self.import_mode != 'replace':
                    existing_config = existing_configs.filtered(
                        lambda c: c.config_id == config_data.get('config_id') and
                                  c.is_page_config == config_data.get('is_page_config', False)
                    )

                if existing_config and self.import_mode == 'skip_existing':
                    skipped_count += 1
                    continue

                # Prepare security groups
                security_group_ids = []
                if config_data.get('security_groups'):
                    for group_name in config_data['security_groups']:
                        group = self.env['odash.security.group'].search([('name', '=', group_name)], limit=1)
                        if group:
                            security_group_ids.append(group.id)

                # Prepare users
                user_ids = []
                if config_data.get('users'):
                    for user_login in config_data['users']:
                        user = self.env['res.users'].search([('login', '=', user_login)], limit=1)
                        if user:
                            user_ids.append(user.id)

                # Prepare configuration values
                config_values = {
                    'name': config_data.get('name', _('Unnamed')),
                    'sequence': config_data.get('sequence', 1),
                    'is_page_config': config_data.get('is_page_config', False),
                    'config_id': config_data.get('config_id'),
                    'config': config_data.get('config', {}),
                    'security_group_ids': [(6, 0, security_group_ids)],
                    'user_ids': [(6, 0, user_ids)],
                }

                if existing_config and self.import_mode == 'merge':
                    # Update existing configuration
                    existing_config.write(config_values)
                else:
                    # Create new configuration
                    self.env['odash.config'].create(config_values)

                imported_count += 1

            # Show success message
            message = _("Import completed successfully!\n")
            message += _("Imported: %s configurations\n") % imported_count
            if skipped_count > 0:
                message += _("Skipped: %s configurations") % skipped_count

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Import Successful'),
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'}
                }
            }

        except json.JSONDecodeError:
            raise UserError(_("Invalid JSON file format."))
        except Exception as e:
            raise UserError(_("Import failed: %s") % str(e))
