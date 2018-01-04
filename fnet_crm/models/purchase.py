from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError, AccessError,except_orm
import curses
class purchase(models.Model):
    _inherit='purchase.order'
    
    
    state = fields.Selection([
        ('draft', 'Draft PO'),
        ('sent', 'RFQ Sent'),
        ('bid received','Bid Received'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
        ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    states=fields.Selection([('load','Load Order'),('in_progress','In Progress'),('done','Done')],readonly=True,default='load',track_visibility='onchange' )    
    margin_line=fields.One2many('sale.quotes.line','purchaseorder_id','Margin Rate')
    history_line=fields.One2many('bid.received.history','order_id','History')
    
    #~ @api.model
    #~ def create(self,vals):
        #~ """
        #~ This function is used for call the new sequence on purchase quotation new state
        #~ like 'RFQ0001'
        #~ """
        #~ if vals.get('name', 'New') == 'New':
            #~ vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order')
        #~ return super(purchase, self).create(vals)
        
    @api.multi
    def bid_received(self):
        
        var=self.write({'state': 'bid received'})
    @api.multi
    def send_rfq(self):
        self.write({'state':'sent'})
   
        
    @api.multi
    def button_approve(self, force=False):
        val = self.env['ir.sequence'].next_by_code('confirm.purchase')
        re=self.write({'name':val})
        req_id=self.env['purchase.requisition'].search([('id','=',self.requisition_id.id)])
        if req_id:
           
           if not req_id.quote_count:
              
              raise UserError(_('Please select the sale quotes in Purchase Agreements..!'))
           else:
              return super(purchase,self).button_approve(force=True)                  
        
        return super(purchase,self).button_approve(force=True)
            
    @api.multi
    def bids_confirm(self):
        """
        This function is call from button confirm,
        This process done in set margin price for product
        It is change the state on done and create the recored on bid received line. 
        """
        product=[]
        count=0
        cnt=[]
        offer=1
        for mrg in self.margin_line:
            if mrg.customer_price==0 and mrg.margin_unit_price==0:
               count=1
               product.append(mrg.product_id.name)
                   
        if count==0:                    
           self.write({'states': 'done'})
           var=False
           requisition_id=self.env['purchase.requisition'].search([('name','=',self.origin)])
           
           line_id=self.env['sale.quotes.line'].search([('purchaseorder_id','=',self.id)])
           history_obj=self.env['costing.history.line']
                                       
           for line in self.margin_line:
               bid_id=self.env['bid.received.line'].search([('tender_id','=',self.requisition_id.id),('product_id','=',line.product_id.id),('purchase_order_id','=',self.id,)])   
               if bid_id:
                  res_value={
                    #~ 'tender_id':requisition_id.id,   
                    #~ 'purchase_order_id':self.id,
                    #~ 'vender_id':self.partner_id.id,
                    #~ 'product_id':line.product_id.id,
                    'quantity':line.quantity,
                    'purchase_unit_price':line.purchase_unit_price,
                    'purchase_total_price':line.purchase_total_price,  
                    'unit_price':line.margin_unit_price,
                    'sub_total':line.customer_price,
                    #~ 'unit_measure':line.unit_measure.id,
                   }
                  cr_id=bid_id.write(res_value)
               else:
                   res_value={
                    'tender_id':requisition_id.id,   
                    'purchase_order_id':self.id,
                    'vender_id':self.partner_id.id,
                    'product_id':line.product_id.id,
                    'quantity':line.quantity,
                    'purchase_unit_price':line.purchase_unit_price,
                    'unit_price':line.margin_unit_price,
                    'purchase_total_price':line.purchase_total_price,
                    'sub_total':line.customer_price,
                    'unit_measure':line.unit_measure.id,
                   }
                   self.env['bid.received.line'].create(res_value)    
           if self.history_line:       
              for i in self.history_line:
                  string_val=i.offer
                  val=string_val.split(" ")
                  cnt.append(val[1])
              x = [int(n) for n in cnt]
              next_off=max(x)
              offer=next_off+1    
           vals={
             'offer':'OFFER ' + str(int(offer)),
             'order_id':self.id,
           }
           off_id=self.history_line.create(vals)
           for line in self.margin_line:
               history_value={
                 'offer_id':off_id.id,
                 'product_id':line.product_id.id,
                 'quantity':line.quantity,
                 'purchase_unit_price':line.purchase_unit_price,
                 'transfort_charge':line.transfort_charge,
                 'margin_percentages':line.margin_percentages.id,
                 'unit_measure':line.unit_measure.id,
                 'margin_unit_price':line.margin_unit_price,
                 'customer_price':line.customer_price,
               }    
               history_obj.create(history_value)
           
         
        else:
            raise UserError(_('Please Calculate the Customer Price..!'))
        
        
   
    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent','bid received']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step':
                order.button_approve(force=True)
            else:
                order.write({'state': 'to approve'})
        return True
        
    @api.multi
    def get_purchase_quote(self):
        """
        This function get the details from orderline 
        """
        
        if self.state in ['draft','sent']:
           raise except_orm('Messages','Please change the state to bid received!')    
        val={}
        quote_obj=self.env['sale.quotes.line']
               
        for line in self.order_line:
            if line.price_unit != 0:
               val={
                 'purchaseorder_id':line.order_id.id,
                 'product_id':line.product_id.id,
                 'quantity':line.product_qty,
                 'purchase_unit_price':line.price_unit,
                 'purchase_total_price':line.price_subtotal,
                 'unit_measure':line.product_uom.id, 
               }
                   
               quote_obj.create(val)    
            else:
                raise UserError(_('Please set the product unit price..!! '))   
        self.write({'states':'in_progress'}) 
                           
    @api.multi
    def set_margin_price(self):
        """
        This function is calculate the margin price for product
        margin=(unit price/100)*percent
        transfort+margin
        then the above value is added to unit price 
        """
        res={}
        product=[]
        for line in self.margin_line:
            if not line.margin_percentages:
               product.append(line.product_id.name) 
        if product:
           string_val= ",".join(str(x) for x in product)    
           raise UserError(_('Please set the margin price for these products"%s"') % \
                       (string_val))          
        for line in self.margin_line:    
            if line.margin_percentages:
               if line.purchase_unit_price != 0:
                  add_trans=line.transfort_charge+line.purchase_unit_price
                  margin=line.purchase_unit_price*line.margin_percentages.values
                  margin_price=margin+add_trans
                  total_price=margin_price*line.quantity
                  res={
                     'margin_unit_price':margin_price,
                     'customer_price':total_price,
                  }
                  line.write(res)
           
                        
                
    @api.multi
    def return_draft(self):
        res={}
        quote_obj=self.env['sale.quotes.line'].search([('purchaseorder_id','=',self.id)])
        if quote_obj:
           quote_obj.unlink()			
        self.write({'states':'load'})
        
        #~ for line in self.margin_line:
            #~ res={
              #~ 'transfort_charge':0.0,
              #~ 'margin_percentages':0.0,
              #~ 'margin_unit_price':0.0,
              #~ 'customer_price':0.0,           
            #~ }                                  
            #~ line.write(res)
            
class sale_quotes_line(models.Model):
    _name='sale.quotes.line'
    
    purchaseorder_id=fields.Many2one('purchase.order','Purchase Order',readonly=True)
    product_id=fields.Many2one('product.product','Product',readonly=True)
    quantity=fields.Float('Quantity',readonly=True)
    purchase_unit_price=fields.Float('Purchase Unit Price',readonly=True)
    transfort_charge=fields.Float('Transportation Charge')
    purchase_total_price=fields.Float('Total Price',readonly=True)
    margin_unit_price=fields.Float('Margin Unit Price',readonly=True)
    customer_price=fields.Float('Customer Price',readonly=True)       
    unit_measure=fields.Many2one('product.uom','Unit of Measure',readonly=True)     
    margin_percentages=fields.Many2one('margin.rate','Margin Percentage')
    
    
class margin_rate(models.Model):
    _name='margin.rate'
   
    name=fields.Char('Name',size=5)
    active=fields.Boolean('Active')
    values=fields.Float('Value',default=True)
    

class costing_history_line(models.Model):
    _name='costing.history.line'
   
    
    offer_id=fields.Many2one('bid.received.history','Bid Received',readonly=True)
    
    product_id=fields.Many2one('product.product','Product') 
    quantity=fields.Float('Quantity')
    purchase_unit_price=fields.Float('Purchase Unit Price')
    transfort_charge=fields.Float('Transportation Charge')
    margin_percentages=fields.Many2one('margin.rate','Margin Percentage')
    unit_measure=fields.Many2one('product.uom','Unit of Measure')
    margin_unit_price=fields.Float('Margin Unit Price')
    customer_price=fields.Float('Customer Price')       

class bid_received_history(models.Model):
    _name='bid.received.history'
    
    offer=fields.Char('OFFER', size=64)
    costing_history_line=fields.One2many('costing.history.line','offer_id','Offers')
    order_id=fields.Many2one('purchase.order','Purchase Order')
