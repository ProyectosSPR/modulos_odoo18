# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def post_init_hook(env):
    """
    Post-installation hook to update security rules to use parent_company_id
    after the field has been created in the database.
    """
    # Update security rules to include parent_company_id in domain
    rules_to_update = [
        ('saas_multicompany.rule_partner_read_multicompany', 'base.model_res_partner'),
        ('saas_multicompany.rule_company_read_multicompany', 'base.model_res_company'),
        ('saas_multicompany.rule_product_read_multicompany', 'product.model_product_template'),
        ('saas_multicompany.rule_sale_order_read_multicompany', 'sale.model_sale_order'),
        ('saas_multicompany.rule_invoice_read_multicompany', 'account.model_account_move'),
    ]

    for rule_xml_id, model_xml_id in rules_to_update:
        try:
            rule = env.ref(rule_xml_id, raise_if_not_found=False)
            if rule:
                # Special domain for companies (uses 'id' instead of 'company_id')
                if 'company' in rule_xml_id:
                    domain = """[
                        '|', ('id', '=', user.company_id.id),
                             ('id', '=', user.company_id.parent_company_id.id)
                    ]"""
                else:
                    # Standard domain for other models
                    domain = """[
                        '|', ('company_id', '=', False),
                        '|', ('company_id', '=', user.company_id.id),
                             ('company_id', '=', user.company_id.parent_company_id.id)
                    ]"""

                rule.write({'domain_force': domain})
        except Exception as e:
            # Log error but don't fail installation
            print(f"Warning: Could not update rule {rule_xml_id}: {e}")

    # Clear caches
    env['ir.rule'].clear_caches()
