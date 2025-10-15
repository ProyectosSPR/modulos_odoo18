from odoo import models, api, fields
from datetime import datetime, timedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def get_dashboard_data(self, start_date=None, end_date=None):
        SaleOrder = self.env['sale.order']
        AccountMove = self.env['account.move']

        # Prepare domain filters with date range
        order_domain = [('state', 'in', ['sale', 'done'])]
        invoice_domain = [('move_type', '=', 'out_invoice')]

        if start_date and end_date:
            start_dt = fields.Date.from_string(start_date)
            end_dt = fields.Date.from_string(end_date)
            order_domain.append(('date_order', '>=', start_dt))
            order_domain.append(('date_order', '<=', end_dt))
            invoice_domain.append(('invoice_date', '>=', start_dt))
            invoice_domain.append(('invoice_date', '<=', end_dt))

        # KPI Metrics
        total_orders = SaleOrder.search_count(order_domain)
        orders = SaleOrder.search(order_domain)
        total_revenue = sum(orders.mapped('amount_total')) if orders else 0

        # Best Products
        best_products_query = """
            SELECT COALESCE(pt.name->>'en_US', pt.name::text) as name, SUM(sol.product_uom_qty) as qty
            FROM sale_order_line sol
            JOIN product_product pp ON sol.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            JOIN sale_order so ON sol.order_id = so.id
            WHERE so.state in ('sale','done')
        """

        if start_date and end_date:
            best_products_query += f" AND so.date_order >= '{start_date}' AND so.date_order <= '{end_date}'"

        best_products_query += """
            GROUP BY pt.name
            ORDER BY qty DESC
            LIMIT 5
        """
        self.env.cr.execute(best_products_query)
        best_products = self.env.cr.dictfetchall()

        # Top Salespersons
        top_sales_query = """
            SELECT rp.name, SUM(so.amount_total) as total_sales
            FROM sale_order so
            JOIN res_users u ON so.user_id = u.id
            JOIN res_partner rp ON u.partner_id = rp.id
            WHERE so.state in ('sale','done')
        """

        if start_date and end_date:
            top_sales_query += f" AND so.date_order >= '{start_date}' AND so.date_order <= '{end_date}'"

        top_sales_query += """
            GROUP BY rp.name
            ORDER BY total_sales DESC
            LIMIT 5
        """
        self.env.cr.execute(top_sales_query)
        top_salespersons = self.env.cr.dictfetchall()

        # Order Status Overview
        status_overview = {}
        for state in ['draft', 'sent', 'sale', 'done', 'cancel']:
            state_domain = [('state', '=', state)]
            if start_date and end_date:
                state_domain.append(('date_order', '>=', start_date))
                state_domain.append(('date_order', '<=', end_date))
            count = SaleOrder.search_count(state_domain)
            status_overview[state] = count

        # Payment Summary
        invoices = AccountMove.read_group(
            domain=invoice_domain,
            fields=['payment_state', 'amount_total'],
            groupby=['payment_state']
        )
        payment_summary = {i['payment_state']: i['amount_total'] for i in invoices}

        # Total Canceled Orders
        canceled_domain = [('state', '=', 'cancel')]
        if start_date and end_date:
            canceled_domain.append(('date_order', '>=', start_date))
            canceled_domain.append(('date_order', '<=', end_date))
        total_canceled = SaleOrder.search_count(canceled_domain)

        # Total Not Invoiced Orders
        not_invoiced_domain = [
            ('state', 'in', ['sale', 'done']),
            ('invoice_status', '!=', 'invoiced')
        ]
        if start_date and end_date:
            not_invoiced_domain.append(('date_order', '>=', start_date))
            not_invoiced_domain.append(('date_order', '<=', end_date))
        total_not_invoiced = SaleOrder.search_count(not_invoiced_domain)

        return {
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'best_products': best_products,
            'top_salespersons': top_salespersons,
            'status_overview': status_overview,
            'payment_summary': payment_summary,
            'total_canceled': total_canceled,
            'total_not_invoiced': total_not_invoiced,
        }
