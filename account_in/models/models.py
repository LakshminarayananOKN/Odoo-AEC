from odoo import api, fields, models

class dimo_dimo(models.Model):
    _inherit = 'sale.order',
    
    @api.depends('amount_total','invoice_status','pay')
    def _get_paid(self):
       self.env.cr.execute("""select sale_order.amount_total,sale_order.name,sale_order.pay,sale_order.invoice_status from sale_order
                              where sale_order.id = %d"""%(self.ids[0]))
       q = self.env.cr.fetchall()
       if q != []:
           if self.invoice_status =='to invoice':
               if q[0][2] != None:
                   c = q[0][0]-q[0][2]
                   if self.invoice_status != 'no':
                       self.env.cr.execute(""" update sale_order
                               set to_invoice = %d
                               where name = '%s'"""%(c,q[0][1]))
               else:
                   self.env.cr.execute(""" update sale_order
                               set to_invoice = %d
                               where name = '%s'"""%(q[0][0],q[0][1]))
    
    acc_in = fields.Many2one('account.invoice', string="Account")
    pay = fields.Monetary("Invoiced", store=True)
    to_invoice = fields.Monetary(string="To Be Invoiced")
    pay_subs = fields.Float(compute='_get_paid', store=True)
   
class store_pay(models.Model):
    _inherit ='account.invoice'
    
    @api.depends('amount_total')
    def _get_paid_amount(self):
       self.env.cr.execute("""select sale_order.amount_total,account_invoice.origin,sale_order.invoice_status from sale_order
                              join account_invoice on sale_order.name=account_invoice.origin
                              where account_invoice.id = %d"""%(self.ids[0]))
       s = self.env.cr.fetchall()
       if s != []:
            self.env.cr.execute(""" select sum(amount_total) from account_invoice
                               where origin ='%s'"""%(s[0][1]))
            z =self.env.cr.fetchall()
            d = s[0][0]
            e = d - z[0][0]
            self.env.cr.execute(""" update sale_order
                               set to_invoice = %d,
                               pay = %d
                               where name = '%s'"""%(e,z[0][0],s[0][1]))
    
    pay_sub = fields.Float(compute='_get_paid_amount', store=True)
