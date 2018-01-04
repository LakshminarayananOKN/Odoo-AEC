from odoo import api, fields, models, _
#~ import uuid
from odoo.exceptions import UserError,except_orm
class saleorder(models.Model):
    _inherit='sale.order'
    

    tender_id     = fields.Many2one('purchase.requisition','Tender Reference')
    enquiry_id    = fields.Many2one('crm.lead','Enquiry Reference')
    amendment_notes=fields.Text('Manager notes')
    state         = fields.Selection([('draft', 'Draft'),
                                      ('to approve','Waiting For Approve'),
                                      ('approved','Approved'),  
                                      ('sent', 'Quotation Sent'),
                                      ('won', 'Quotation Won'),
                                      ('drop', 'Quotation Drop'),
                                      ('lost', 'Quotation Lost'),
                                      ('hold', 'Quotation Hold'),
                                      ('amendmend','Amendmend'),
                                      ('sale', 'Sale Order'),
                                      ('done', 'Done'),
                                      ('cancel', 'Cancelled'),
                                      ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
   
                    
    @api.multi
    def return_draft(self):
        self.write({'state':'draft'}) 
        return True
      
        
                         
    @api.model
    def get_salesman_url(self):
        self.ensure_one()
        val=self.user_id.partner_id.with_context(signup_valid=True)._get_signup_url_for_action(
            action='/mail/view',
            model=self._name,
            res_id=self.id)[self.user_id.partner_id.id]
            
        return val              
    @api.multi
    def quote_reject(self):
        url_val=self.get_salesman_url()
        resl_id=self.env['res.partner'].search([('id','=',self.user_id.partner_id.id)])
        body = _("Dear " + self.user_id.name + "\n")
                                            
        body += _("\t This (%s) Sale Quotation has been Rejected by %s. \n "%(self.name,self.env.user.name))
        body += _("\n Regards, \n %s."%(self.env.user.name)) 
        values={
            'subject': "Sale Quote Rejected",
            'email_to' :resl_id.email,
            'body_html':'<pre><span class="inner-pre" style="font-size:15px">%s</span><a style="display:block; width: 150px; height:20px; margin-left: 120px; color:#FDFEFE; font-family: Lucida Grande, Helvetica, Arial, sans-serif; font-size: 13px; font-weight: bold; text-align: center; text-decoration: none !important; line-height: 1; padding: 5px 0px 0px 0px; background-color: #B915EE; border-radius: 5px 5px; background-repeat: repeat no-repeat;"href="%s">View Quote</a></pre>'%(body,url_val),
            'body' :'<pre><span class="inner-pre" style="font-size:15px">%s</span></pre>'%(body),
            'res_id': False
           }    
        
        mail_mail_obj = self.env['mail.mail']
        msg_id = mail_mail_obj.create(values)
        
        if msg_id:
           res=msg_id.send(self) 
        val = self.env['ir.sequence'].next_by_code('salequote.amend')
        pre_name=self.name
        saleorder_name=val+' ('+pre_name+')'
        self.write({'name':saleorder_name})
        self.write({'state':'amendmend'})              
    
    
        
    @api.multi
    def approve_quote(self):
        values={}
        url_val=self.get_salesman_url()
        resl_id=self.env['res.partner'].search([('id','=',self.user_id.partner_id.id)])
        body = _("Dear " + self.user_id.name + "\n")
                                            
        body += _("\t This (%s) Sale Quotation has been Approved by %s. \n "%(self.name,self.env.user.name))
        
        body += _("\n Regards, \n %s."%(self.env.user.name)) 
        values={
            'subject': "Sale Quote Approved",
            'email_to' :resl_id.email,
            'body_html':'<pre><span class="inner-pre" style="font-size:15px">%s</span><a style="display:block; width: 150px; height:20px; margin-left: 120px; color:#FDFEFE; font-family: Lucida Grande, Helvetica, Arial, sans-serif; font-size: 13px; font-weight: bold; text-align: center; text-decoration: none !important; line-height: 1; padding: 5px 0px 0px 0px; background-color: #B915EE; border-radius: 5px 5px; background-repeat: repeat no-repeat;"href="%s">View Quote</a></pre>'%(body,url_val),
            'body' :'<pre><span class="inner-pre" style="font-size:15px">%s</span></pre>'%(body),
            'res_id': False
           }    
        
        mail_mail_obj = self.env['mail.mail']
        msg_id = mail_mail_obj.create(values)
        
        if msg_id:
           res=msg_id.send(self) 
         
        self.write({'state':'sent'}) 
               
    @api.multi
    def action_quotation_send(self):
        if self.state=='draft':           
           ret=self.validate_profit_percentage()
        
           if ret ==1:
              return False  
        return super(saleorder, self).action_quotation_send()
        
    @api.multi
    def validate_profit_percentage(self):
        tot=0.0
        val=1
        #~ conf_obj=self.env['sale.config.settings'].search([('company_id','=',self.env.user.company_id.id)],order='id desc',limit=1)
        
        if self.user_has_groups('sales_team.group_sale_manager') is False:
           if self.tender_id:
              
              #~ bid_line=self.env['bid.received.line'].search([('tender_id','=',self.tender_id.id)])
              
              for line in self.order_line:
                 
                 tot +=line.purchase_total_price
                               
              profit=self.amount_untaxed-tot
              profit_per=(profit/tot)*100
              if self.team_id.limit_id:
                 if profit_per < self.team_id.limit_id.values:
                    self.write({'state':'to approve'}) 
                    
                    rt=self.approve_quote_by_team_leader()
                    
                    return val
              #~ elif conf_obj.limit_id:
                 #~ if profit_per < sconf_obj.limit_id.values:
                    #~ self.write({'state':'to approve'}) 
               
                    #~ return val      
       
        return False
        
    @api.model
    def get_url(self):
        self.ensure_one()
        val=self.team_id.user_id.partner_id.with_context(signup_valid=True)._get_signup_url_for_action(
            action='/mail/view',
            model=self._name,
            res_id=self.id)[self.team_id.user_id.partner_id.id]
        return val
    
             
    @api.model
    def approve_quote_by_team_leader(self):
        values={}
        url_val=self.get_url()
        if self.team_id.user_id:
           resl_id=self.env['res.partner'].search([('id','=',self.team_id.user_id.partner_id.id)])
           try:
              body = _("Dear " + resl_id.name + "\n")
                                                
              body += _("\t This (%s) Sale Quotation is waiting for your Approval. \n "%(self.name))
              body += _("\n Regards, \n %s."%(self.env.user.name)) 
              values={
                 'subject': "Sale Quote Wait for Approval",
                 'email_to' :resl_id.email,
                 'body_html':'<pre><span class="inner-pre" style="font-size:15px">%s</span><a style="display:block; width: 150px; height:20px; margin-left: 120px; color:#FDFEFE; font-family: Lucida Grande, Helvetica, Arial, sans-serif; font-size: 13px; font-weight: bold; text-align: center; text-decoration: none !important; line-height: 1; padding: 5px 0px 0px 0px; background-color: #B915EE; border-radius: 5px 5px; background-repeat: repeat no-repeat;"href="%s">View Quote</a></pre>'%(body,url_val),
                 'body' :'<pre><span class="inner-pre" style="font-size:15px">%s</span></pre>'%(body),
                 'res_id': False
                }    
           
              mail_mail_obj = self.env['mail.mail']
              msg_id = mail_mail_obj.create(values)
            
              if msg_id:
                 res=msg_id.send(self)
                 return res
           except Exception,z :
              print z                  
        return False  
    
    @api.multi
    def action_quote_won(self):
        ret_val=self.env['ir.attachment'].search(['|',('res_id','=',self.id),('res_name','=',self.name)])
        if ret_val:
            data = self.read()[0]
            data['partner_id'] = self._context.get('active_id',[])
            if data['state'] == 'sent':
                self.env.cr.execute("""update crm_lead  set active = 'False'""")
                self.write({'state': 'won'})
        else:
            raise UserError(_('Please add the files in attachment.'))
   
    @api.multi
    def action_quote_drop(self):
        data = self.read()[0]
        data['partner_id'] = self._context.get('active_id',[])
        if data['state'] == 'sent':
            self.env.cr.execute("""update crm_lead  set active = 'False'""")
            self.write({'state': 'drop'})

    @api.multi
    def action_quote_lost(self):
        data = self.read()[0]
        data['partner_id'] = self._context.get('active_id',[])
        if data['state'] == 'sent':
            self.env.cr.execute("""update crm_lead  set active = 'False'""")
            self.write({'state': 'lost'})

    @api.multi
    def action_quote_hold(self):
        data = self.read()[0]
        data['partner_id'] = self._context.get('active_id',[])
        if data['state'] == 'sent':
            self.env.cr.execute("""update crm_lead  set active = 'False'""")
            self.write({'state': 'hold'})
    
    @api.multi
    def action_draft(self):
        
        orders = self.filtered(lambda s: s.state in ['cancel', 'sent', 'hold', 'drop', 'lost'])
        orders.write({
            'state': 'draft',
            'procurement_group_id': False,
        })
        orders.mapped('order_line').mapped('procurement_ids').write({'sale_line_id': False})


    @api.multi
    def action_confirm_quote(self):
        if self.state=='draft':
           ret=self.validate_profit_percentage()
           if ret:
              return True  
        
        self.write({'state':'sent'})
    
    @api.multi
    def action_confirm(self):
        ret_val=self.env['ir.attachment'].search(['|',('res_id','=',self.id),('res_name','=',self.name)])
        if ret_val:
           self.confirm_sale_sequence()
           return super(saleorder, self).action_confirm()
        else:
           raise UserError(_('Please add the files in attachment.')) 
        
        
    @api.multi
    def confirm_sale_sequence(self):
        val = self.env['ir.sequence'].next_by_code('confirm.sale')
        self.write({'name':val})
        
    @api.multi
    def print_quotation(self):
       
        
        if self.state=='draft':
           ret=self.validate_profit_percentage()
           if ret:
              return True
           else:
              return super(saleorder, self).print_quotation()
        return super(saleorder, self).print_quotation()        

class saleorder_approve(models.Model):
    _name='approve.limit'
    
    name=fields.Char('Name',size=15)
    active=fields.Boolean('Active',default=True)
    values=fields.Float('Value')


class saleorder_line(models.Model):
    _inherit='sale.order.line'

    purchase_unit_price=fields.Float('Purchase Unit Price',readonly=True)
    purchase_total_price=fields.Float('Purchase Total Price',readonly=True)

