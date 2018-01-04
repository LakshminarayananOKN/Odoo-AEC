# -*- coding: utf-8 -*-
from openerp import http

# class AccountIn(http.Controller):
#     @http.route('/account_in/account_in/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_in/account_in/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_in.listing', {
#             'root': '/account_in/account_in',
#             'objects': http.request.env['account_in.account_in'].search([]),
#         })

#     @http.route('/account_in/account_in/objects/<model("account_in.account_in"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_in.object', {
#             'object': obj
#         })