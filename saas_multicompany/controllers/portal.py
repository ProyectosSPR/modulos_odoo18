# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, MissingError
from collections import OrderedDict


class SaaSCustomerPortal(CustomerPortal):
    """
    Extend portal to allow internal SaaS users to access their own orders and invoices
    """

    def _prepare_home_portal_values(self, counters):
        """Override to allow internal users to see portal counters"""
        values = super()._prepare_home_portal_values(counters)

        # Check if user is internal SaaS user (not portal, not admin)
        user = request.env.user
        if user.has_group('base.group_user'):
            # Allow internal users to see their portal data
            partner = user.partner_id

            SaleOrder = request.env['sale.order']
            Invoice = request.env['account.move']

            if 'quotation_count' in counters:
                values['quotation_count'] = SaleOrder.search_count([
                    ('partner_id', 'child_of', partner.commercial_partner_id.id),
                    ('state', 'in', ['sent', 'draft'])
                ]) if SaleOrder.check_access_rights('read', raise_exception=False) else 0

            if 'order_count' in counters:
                values['order_count'] = SaleOrder.search_count([
                    ('partner_id', 'child_of', partner.commercial_partner_id.id),
                    ('state', 'in', ['sale', 'done'])
                ]) if SaleOrder.check_access_rights('read', raise_exception=False) else 0

            if 'invoice_count' in counters:
                values['invoice_count'] = Invoice.search_count([
                    ('partner_id', 'child_of', partner.commercial_partner_id.id),
                    ('move_type', 'in', ['out_invoice', 'out_refund']),
                    ('state', '!=', 'draft')
                ]) if Invoice.check_access_rights('read', raise_exception=False) else 0

        return values

    @http.route(['/my/orders', '/my/orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_orders(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        """Override to allow internal SaaS users to see their orders"""
        # Call parent method - it will use record rules to filter
        return super().portal_my_orders(page=page, date_begin=date_begin, date_end=date_end, sortby=sortby, **kw)

    @http.route(['/my/orders/<int:order_id>'], type='http', auth="user", website=True)
    def portal_order_page(self, order_id=None, access_token=None, **kw):
        """Override to allow internal SaaS users to see their order details"""
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        # Call parent method
        return super().portal_order_page(order_id=order_id, access_token=access_token, **kw)

    @http.route(['/my/invoices', '/my/invoices/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_invoices(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        """Override to allow internal SaaS users to see their invoices"""
        # Call parent method - it will use record rules to filter
        return super().portal_my_invoices(page=page, date_begin=date_begin, date_end=date_end, sortby=sortby, filterby=filterby, **kw)

    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="user", website=True)
    def portal_my_invoice_detail(self, invoice_id=None, access_token=None, report_type=None, download=False, **kw):
        """Override to allow internal SaaS users to see their invoice details"""
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        # Call parent method
        return super().portal_my_invoice_detail(invoice_id=invoice_id, access_token=access_token, report_type=report_type, download=download, **kw)
