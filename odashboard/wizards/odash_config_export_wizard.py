import json
import base64
from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class OdashConfigExportWizard(models.TransientModel):
    _name = 'odash.config.export.wizard'
    _description = 'Export Dashboard Configurations Wizard'

    export_type = fields.Selection([
        ('all', 'Export All Pages'),
        ('specific_pages', 'Export Specific Pages'),
        ('single_config', 'Export Single Configuration')
    ], string='Export Type', default='all', required=True)

    # Page selection for specific pages export
    page_ids = fields.Many2many(
        comodel_name='odash.config',
        string='Select Pages',
        domain=[('is_page_config', '=', True)],
        help="Select the pages to export with all their components"
    )

    # Single config selection
    config_id = fields.Many2one(
        comodel_name='odash.config',
        string='Select Configuration',
        help="Select a single configuration to export"
    )

    # Export options
    include_security = fields.Boolean(
        string='Include Security Settings',
        default=True,
        help="Include security groups and user assignments in export"
    )
    include_metadata = fields.Boolean(
        string='Include Metadata',
        default=True,
        help="Include export date, versions, and other metadata"
    )

    # Preview fields
    preview_data = fields.Text(string='Export Preview', readonly=True)
    show_preview = fields.Boolean(string='Show Preview', default=False)
    config_count = fields.Integer(string='Configurations Count', readonly=True)

    @api.onchange('export_type', 'page_ids', 'config_id')
    def _onchange_export_selection(self):
        """Update preview when export selection changes"""
        self._update_preview()

    def _update_preview(self):
        """Generate preview of what will be exported"""
        if not self.export_type:
            self.preview_data = ""
            self.show_preview = False
            self.config_count = 0
            return

        try:
            configs = self._get_configs_to_export()
            
            if not configs:
                self.preview_data = "No configurations found for the selected export type."
                self.show_preview = True
                self.config_count = 0
                return

            # Generate preview
            preview_lines = []
            
            # Export type description
            type_descriptions = {
                'all': 'All pages with their components',
                'specific_pages': f'{len(self.page_ids)} selected pages with their components' if self.page_ids else 'Specific pages with components',
                'single_config': f'Single configuration: "{self.config_id.name}"' if self.config_id else 'Single configuration'
            }
            
            preview_lines.append(f"Export Type: {type_descriptions.get(self.export_type, 'Unknown')}")
            preview_lines.append(f"Total Configurations: {len(configs)}")
            preview_lines.append("")

            # Group by type
            pages = configs.filtered(lambda c: c.is_page_config)
            components = configs.filtered(lambda c: not c.is_page_config)

            if pages:
                preview_lines.append(f"Pages ({len(pages)}):")
                for page in pages[:5]:  # Show first 5
                    security_info = "Public" if not page.security_group_ids and not page.user_ids else "Restricted"
                    preview_lines.append(f"  • {page.name} ({security_info})")
                if len(pages) > 5:
                    preview_lines.append(f"  ... and {len(pages) - 5} more pages")
                preview_lines.append("")

            if components:
                preview_lines.append(f"Components ({len(components)}):")
                for component in components[:5]:  # Show first 5
                    preview_lines.append(f"  • {component.name}")
                if len(components) > 5:
                    preview_lines.append(f"  ... and {len(components) - 5} more components")
                preview_lines.append("")

            # Export options
            preview_lines.append("Export Options:")
            preview_lines.append(f"  • Security Settings: {'Included' if self.include_security else 'Excluded'}")
            preview_lines.append(f"  • Metadata: {'Included' if self.include_metadata else 'Excluded'}")

            self.preview_data = "\n".join(preview_lines)
            self.show_preview = True
            self.config_count = len(configs)

        except Exception as e:
            self.preview_data = f"Error generating preview: {str(e)}"
            self.show_preview = True
            self.config_count = 0

    def _get_configs_to_export(self):
        """Get the configurations to export based on selection"""
        if self.export_type == 'all':
            # Export all pages and their components
            return self.env['odash.config'].search([])
        
        elif self.export_type == 'specific_pages':
            if not self.page_ids:
                return self.env['odash.config']
            
            # Get selected pages and all their components
            configs = self.env['odash.config'].browse(self.page_ids.ids)
            
            # Find components used by these pages
            all_components = self.env['odash.config'].search([('is_page_config', '=', False)])
            
            for page in self.page_ids:
                if page.config:
                    page_config_str = json.dumps(page.config)
                    for component in all_components:
                        if component.config_id and component.config_id in page_config_str:
                            if component not in configs:
                                configs += component
            
            return configs
        
        elif self.export_type == 'single_config':
            if not self.config_id:
                return self.env['odash.config']
            return self.env['odash.config'].browse(self.config_id.id)
        
        return self.env['odash.config']

    def _generate_filename(self):
        """Generate appropriate filename based on export type"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if self.export_type == 'all':
            return f"odashboard_full_export_{timestamp}.json"
        elif self.export_type == 'specific_pages' and self.page_ids:
            if len(self.page_ids) == 1:
                page_name = self.page_ids[0].name.replace(' ', '_').lower()
                return f"odashboard_page_{page_name}_{timestamp}.json"
            else:
                return f"odashboard_pages_{len(self.page_ids)}pages_{timestamp}.json"
        elif self.export_type == 'single_config' and self.config_id:
            config_name = self.config_id.name.replace(' ', '_').lower()
            config_type = "page" if self.config_id.is_page_config else "component"
            return f"odashboard_{config_type}_{config_name}_{timestamp}.json"
        else:
            return f"odashboard_export_{timestamp}.json"

    def action_export(self):
        """Execute the export process"""
        if self.export_type == 'specific_pages' and not self.page_ids:
            raise UserError(_("Please select at least one page to export."))
        
        if self.export_type == 'single_config' and not self.config_id:
            raise UserError(_("Please select a configuration to export."))

        try:
            configs = self._get_configs_to_export()
            
            if not configs:
                raise UserError(_("No configurations found to export."))

            # Prepare export data
            export_data = {
                'export_type': self.export_type,
                'configs': []
            }

            # Add metadata if requested
            if self.include_metadata:
                export_data.update({
                    'export_date': datetime.now().isoformat(),
                    'odoo_version': self.env['ir.module.module'].sudo().search([('name', '=', 'base')]).latest_version,
                    'odashboard_version': self.env['ir.module.module'].sudo().search([('name', '=', 'odashboard')]).latest_version,
                    'exported_by': self.env.user.name,
                })

            # Add specific export context
            if self.export_type == 'specific_pages' and self.page_ids:
                export_data['page_names'] = self.page_ids.mapped('name')
                export_data['page_config_ids'] = self.page_ids.mapped('config_id')
            elif self.export_type == 'single_config' and self.config_id:
                export_data['config_name'] = self.config_id.name
                export_data['config_type'] = 'page' if self.config_id.is_page_config else 'component'

            # Export configurations
            for config in configs:
                config_data = {
                    'name': config.name,
                    'sequence': config.sequence,
                    'is_page_config': config.is_page_config,
                    'config_id': config.config_id,
                    'config': config.config,
                }

                # Add security settings if requested
                if self.include_security:
                    config_data.update({
                        'security_groups': config.security_group_ids.mapped('name'),
                        'users': config.user_ids.mapped('login'),
                        'allow_public_access': config.allow_public_access,
                    })

                export_data['configs'].append(config_data)

            # Create JSON file
            json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
            filename = self._generate_filename()

            # Create attachment
            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(json_data.encode('utf-8')),
                'res_model': 'odash.config.export.wizard',
                'res_id': self.id,
                'mimetype': 'application/json',
            })

            # Show success message and download
            message = _("Export completed successfully!\n")
            message += _("Exported %s configurations") % len(configs)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Export Successful'),
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                    'next': {
                        'type': 'ir.actions.act_url',
                        'url': f'/web/content/{attachment.id}?download=true',
                        'target': 'self',
                    }
                }
            }

        except Exception as e:
            raise UserError(_("Export failed: %s") % str(e))
