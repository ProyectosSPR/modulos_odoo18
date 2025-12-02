# -*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    """Migrar reglas existentes a usar ir.model.fields"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Mapeo de campos antiguos a nuevos
    source_field_mapping = {
        'ref': 'ref',
        'payment_ref': 'payment_ref',
        'narration': 'narration',
        'partner_name': 'partner_id',
    }
    
    target_field_mapping = {
        'ref': 'ref',
        'name': 'name',
        'l10n_mx_edi_cfdi_uuid': 'l10n_mx_edi_cfdi_uuid',
        'partner_name': 'partner_id',
        'invoice_origin': 'invoice_origin',
    }
    
    # Migrar reglas directas
    direct_rules = env['mx.reconcile.rule'].search([])
    for rule in direct_rules:
        # Determinar modelo origen
        source_model = 'account.bank.statement.line' if rule.source_model == 'statement_line' else 'account.payment'
        target_model = 'account.move'
        
        # Buscar campo origen
        if hasattr(rule, 'source_field') and rule.source_field:
            field_name = source_field_mapping.get(rule.source_field, rule.source_field)
            source_field = env['ir.model.fields'].search([
                ('model', '=', source_model),
                ('name', '=', field_name)
            ], limit=1)
            if source_field:
                rule.source_field_id = source_field.id
        
        # Buscar campo destino
        if hasattr(rule, 'target_field') and rule.target_field:
            field_name = target_field_mapping.get(rule.target_field, rule.target_field)
            target_field = env['ir.model.fields'].search([
                ('model', '=', target_model),
                ('name', '=', field_name)
            ], limit=1)
            if target_field:
                rule.target_field_id = target_field.id
    
    # Migrar reglas por relación
    relation_rules = env['mx.reconcile.relation.rule'].search([])
    for rule in relation_rules:
        # Campo de pago
        if hasattr(rule, 'payment_field') and rule.payment_field:
            payment_field = env['ir.model.fields'].search([
                ('model', 'in', ['account.payment', 'account.bank.statement.line']),
                ('name', '=', rule.payment_field)
            ], limit=1)
            if payment_field:
                rule.payment_field_id = payment_field.id
        
        # Campo de búsqueda en relación
        if hasattr(rule, 'relation_search_field') and rule.relation_search_field:
            search_field = env['ir.model.fields'].search([
                ('model', '=', rule.relation_model),
                ('name', '=', rule.relation_search_field)
            ], limit=1)
            if search_field:
                rule.relation_search_field_id = search_field.id
        
        # Campo de relación a factura
        if hasattr(rule, 'invoice_relation_field') and rule.invoice_relation_field:
            relation_field = env['ir.model.fields'].search([
                ('model', '=', rule.relation_model),
                ('name', '=', rule.invoice_relation_field)
            ], limit=1)
            if relation_field:
                rule.invoice_relation_field_id = relation_field.id
