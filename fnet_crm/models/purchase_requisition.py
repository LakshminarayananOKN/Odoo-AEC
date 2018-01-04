from odoo import models,fields,_
from odoo import api
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError,except_orm
class purchase_requisition(models.Model):
    _inherit='purchase.requisition'
    
    
    @api.model
    def _get_picking_in(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
       
        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
            
        return types[:1]
    
    oppor_id=fields.Many2one('crm.lead','Enquiry Reference',required=True)
    bid_received_line=fields.One2many('bid.received.line','tender_id','Sale Quotes')
    quote_count=fields.Integer(compute='get_count',readonly=True)
    customer_id=fields.Many2one('res.partner','Customer Name')
    ordering_date = fields.Date('Scheduled Ordering Date')
    date_end = fields.Datetime('Tender Closing Deadline')
    schedule_date = fields.Date('Scheduled Date', select=True, help="The expected and scheduled delivery date where all the products are received")
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', required=True, default=_get_picking_in)
    
    
    
    
    @api.multi
    def action_open(self):
        if self.quote_count:
           return super(purchase_requisition, self).action_open()           
        else:
           raise UserError(_('You cannot validate agreement because there is no sale quote.'))
           
    @api.one
    def get_count(self):
        """
        This function is return the count of the sale quotations 
        """
        count_quote=0
        #crm_obj=self.env['crm.lead'].search([('oppor_order','=',self.origin)]) 
        purchase_id=self.env['sale.order'].search([('tender_id','=',self.id)])
        
        for purchase in purchase_id:
            count_quote +=1
        
        self.quote_count=count_quote
                    
    @api.multi
    def open_quotation(self):
        """
        This is used for view the sale quotation against the current tender
        """
        var=[]
        if self._context is None:
            context = {}
        res = self.env['ir.actions.act_window'].for_xml_id('sale', 'action_quotations')
        res['context'] = self._context
        #crm_obj=self.env['crm.lead'].search([('oppor_order','=',self.origin)]) 
        purchase_id=self.env['sale.order'].search([('tender_id','=',self.id)])
        for i in purchase_id:
            var.append(i.id)
        res['domain'] = [('id', 'in', var)]
        return res 
           
    @api.multi
    def make_quotation(self):
        """
        This function is used to create the quotation from purchase tender.
        That quotation is create against the select sale quotes
        """
        result_val=[]
        order_cn=[]
        count_value=0
        test_val=[]
        desig=""
        quote_val=self.env['bid.received.line'].search([('tender_id','=',self.id)])
        for ch in quote_val:
            if ch.valid_qoute is True:
               test_val.append(ch.product_id.id)
        chec=set([x for x in test_val if test_val.count(x) > 1])    
        if chec:
           raise except_orm('Selection Mistake','More than one times you selected the same product ')     
        for i in quote_val:
            if i.valid_qoute is True:
                count_value=1
        if not quote_val:
           raise except_orm('Sale Quotes Missing','Please first you create RFQs then receive the bids on sale quotes!')
        elif count_value == 0:
           raise UserError(_('Please select any RFQ in sale quotes!'))      
        sale_quotation=self.env['sale.order']
        purchase=self.env['purchase.order'] 
        crm_obj=self.env['crm.lead'].search([('oppor_order','=',self.origin)])
        quotation_count=sale_quotation.search([('opportunity_id','=',crm_obj.id)])
        if quotation_count:
           raise UserError(_('You can create only one Quotation !'))
        #~ crm_obj=self.env['crm.lead'].search([('oppor_order','=',self.origin)])
        self.env.cr.execute('''SELECT hr_job.name FROM hr_job 
                                    LEFT JOIN hr_employee ON hr_job.id = hr_employee.job_id
                                    LEFT JOIN resource_resource ON resource_resource.id = hr_employee.resource_id
                                    WHERE resource_resource.user_id = %d'''%(crm_obj.user_id.id))
        fet_value=self.env.cr.fetchall()
      
        val=len(fet_value)
        if val != 0:
            desig=fet_value[0][0]
        
        addr = crm_obj.partner_id.address_get(['delivery', 'invoice'])
        values = {
         'partner_id':crm_obj.partner_id.id or False,       
         'source_id':crm_obj.source_id.id or False,
         'campaign_id':crm_obj.campaign_id.id or False,
         'note':crm_obj.env.user.company_id.sale_note or False,
         'medium_id':crm_obj.medium_id.id or False,
         'user_id':crm_obj.user_id.id or False,
         'designation':desig or False,
         'team_id':crm_obj.team_id.id or False,
         'opportunity_id':crm_obj.id or False,
         'enquiry_id':crm_obj.id or False,
         'tender_id':self.id or False,
         
        }
       
        quotation=sale_quotation.create(values)
      
        if quotation:
          
           value_line=self.env['bid.received.line'].search([('tender_id','=',self.id),('valid_qoute','=',True)])
           for len_val in value_line:
               ret_value={
                'order_id':quotation.id,
                'product_id':len_val.product_id.id,
                'product_uom_qty':len_val.quantity,
                'price_unit':len_val.unit_price,
                'product_uom':len_val.unit_measure.id,
                'purchase_unit_price':len_val.purchase_unit_price,
                'purchase_total_price':len_val.purchase_total_price,  
               }
               
               line=sale_quotation.env['sale.order.line']
               valu=line.create(ret_value)
               """
               This hided line is used for if sale quotes are create then against purchase quote 
               was converted in purchase order state
               """              
               #~ purchase_res=purchase.search([('id','=',len_val.purchase_order_id.id)])
               #~ for purchase_id in purchase_res:
                   #~ res=purchase_id.write({'state':'purchase'})
               not_quotes=purchase.search([('origin','=',self.name)])
               for val in not_quotes:
                   unbid_id=self.env['bid.received.line'].search([('purchase_order_id','=',val.id)])
                   bid_id=self.env['bid.received.line'].search([('purchase_order_id','=',val.id),('valid_qoute','=',True)])
                   if not unbid_id:
                       rfe=val.write({'state':'cancel'})
                   
                   elif not bid_id:
                       val.write({'state':'cancel'})    
        unquote_line=self.env['bid.received.line'].search([('tender_id','=',self.id),('valid_qoute','=',False)])
        quote_line=self.env['bid.received.line'].search([('tender_id','=',self.id),('valid_qoute','=',True)])
        for clear_value in unquote_line:
            clear_value.unlink()       
        valid_line=self.env['bid.received.line'].search([('tender_id','=',self.id)])
       
        for i in valid_line:
            order_cn.append(i.purchase_order_id.id) 
            set_val=set(order_cn)
            result_val = list(set_val)
        for re in result_val:
            order_obj=self.env['purchase.order.line'].search([('order_id','=',re)])
            for order in order_obj:
                val=self.env['bid.received.line'].search([('purchase_order_id','=',re),('product_id','=',order.product_id.id)])
                if not val:
                    order.unlink()                                       
        
        
class bid_received_line(models.Model):
    _name='bid.received.line'
    
   
    tender_id=fields.Many2one('purchase.requisition','Tender Reference')
    valid_qoute=fields.Boolean('Select')
    purchase_order_id=fields.Many2one('purchase.order','Purchase Quotes',readonly=True)
    vender_id=fields.Many2one('res.partner','Supplier',readonly=True)
    product_id=fields.Many2one('product.product','Product',readonly=True)
    quantity=fields.Float('Quantity',readonly=True)
    unit_measure=fields.Many2one('product.uom','Unit of Measure',readonly=True)
    purchase_unit_price=fields.Float('Purchase Unit Price',readonly=True)
    unit_price=fields.Float('Unit Price',readonly=True)
    purchase_total_price=fields.Float('Purchase Price',readonly=True)
    sub_total=fields.Float('Sub Total',readonly=True)
    
    
   
