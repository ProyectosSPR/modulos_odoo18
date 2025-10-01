# -*- coding: utf-8 -*-
# from odoo import http


# class N8n-sales(http.Controller):
#     @http.route('/n8n-sales/n8n-sales', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/n8n-sales/n8n-sales/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('n8n-sales.listing', {
#             'root': '/n8n-sales/n8n-sales',
#             'objects': http.request.env['n8n-sales.n8n-sales'].search([]),
#         })

#     @http.route('/n8n-sales/n8n-sales/objects/<model("n8n-sales.n8n-sales"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('n8n-sales.object', {
#             'object': obj
#         })

