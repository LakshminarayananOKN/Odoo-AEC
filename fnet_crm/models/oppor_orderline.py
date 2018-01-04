# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError
class crm_lead(models.Model):

    _inherit ='crm.lead'
    _rec_name ='oppor_order'
    
    opportunity_order_line=fields.One2many('opportunity.order.line','lead_id',string='Product Line')
    oppor_order=fields.Char(string="Opportunity ID",readonly=True, required=False)
    tender_counter=fields.Integer(compute='get_tender_count',readonly=True)
   

    @api.one
    def get_tender_count(self):
        '''
        This function is used to get the count of the tender
        '''
        var=0
        purchase_id=self.env['purchase.requisition'].search([('origin','=',self.oppor_order)])
        for i in purchase_id:
            var +=1
        self.tender_counter=var 
        
    @api.model
    def create(self, vals):
        '''
        Adding the sequence for enquiry ENQ00001
        '''
                           
        vals['oppor_order'] = self.env['ir.sequence'].next_by_code('enquiry.sequence')
   
        cid=super(crm_lead, self).create(vals)
        
        return cid
        
        
        
    @api.multi
    def make_tender(self):
       """
       This is used to create the tender against the enquiry
       """
       tenders=self.env['purchase.requisition'] 
       tender_count=tenders.search([('origin','=',self.oppor_order)])
       if tender_count:   
          raise UserError(_('You can create only one Tender !'))     
       user=self.env['res.users'].search([('id','=',self._uid)])
       if not self.partner_id:
          raise UserError(_('Please Select raleted customer !'))           
       values = {
        'user_id':self.user_id.id,       
        'oppor_id':self.id,
        'company_id':user.company_id.id,
        'origin':self.oppor_order,
        'customer_id':self.partner_id.id,
       }
       
       quotation=tenders.create(values)
      
       if quotation:
          
          value_line=self.env['opportunity.order.line'].search([('lead_id','=',self.id)])
          for len_val in value_line:
              ret_value={
               'requisition_id':quotation.id,
               'product_id':len_val.product_id.id,
               'product_qty':len_val.quantity,
               'product_uom_id':len_val.unit_measure.id,
              }
              
              line=tenders.env['purchase.requisition.line'].create(ret_value)
              
              
    @api.multi   
    def open_tender(self):
        """ This opens purchase tender view to view all opportunity associated to the call for tenders
            @return: the tender tree view
        """
        var=[]
        if self._context is None:
            context = {}
        res = self.env['ir.actions.act_window'].for_xml_id('purchase_requisition', 'action_purchase_requisition')
        res['context'] = self._context
        purchase_id=self.env['purchase.requisition'].search([('origin','=',self.oppor_order)])
        for i in purchase_id:
            var.append(i.id)
        res['domain'] = [('id', 'in', var)]
        return res           
        
class opportunity_orderline(models.Model):
    _name = 'opportunity.order.line'
    
    lead_id=fields.Many2one('crm.lead',string='Product')
    product_id=fields.Many2one('product.product',string='Product')

    quantity=fields.Float(string='Expected Quantity')
    unit_measure=fields.Many2one('product.uom','Unit of Measure')
    unit_price=fields.Float(string='Expected Price')
    
    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
       
        if self.product_id:
           res={}
           product_obj=self.env['product.product'].search([('id','=',self.product_id.id)])
           res_value=self.env['product.template'].search([('id','=',product_obj.product_tmpl_id.id)])
           res={
             'quantity':1,
             'unit_measure':res_value.uom_id.id,    
           }
           self.update(res)
        else:
               
           return False
     
  
    
    
    
