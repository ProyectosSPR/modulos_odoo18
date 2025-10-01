# -*- coding: utf-8 -*-
# from odoo import http


# class SaaSAccessManagement(http.Controller):
#     @http.route('/saa_s__access_management/saa_s__access_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/saa_s__access_management/saa_s__access_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('saa_s__access_management.listing', {
#             'root': '/saa_s__access_management/saa_s__access_management',
#             'objects': http.request.env['saa_s__access_management.saa_s__access_management'].search([]),
#         })

#     @http.route('/saa_s__access_management/saa_s__access_management/objects/<model("saa_s__access_management.saa_s__access_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('saa_s__access_management.object', {
#             'object': obj
#         })

