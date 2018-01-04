from odoo import api, fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'
    
    limit_id=fields.Many2one('approve.limit','Approve Limit')
    budget_line=fields.One2many('sale.budget','budget_id','Budget')
    from_date=fields.Date('Budget From Period',required=True)
    to_date=fields.Date('Budget To Period',required=True)

class SaleBudget(models.Model):
    _name='sale.budget'
    
    @api.one
    def _compute_invoice_value(self):
        if self.budget_id.id and self.type:
            self.env.cr.execute("""
                            select  sum(ail.price_subtotal) as total
                                    from account_invoice ai
                                    left join account_invoice_line ail on (ail.invoice_id=ai.id)
                                    left join product_product pp on (ail.product_id=pp.id)
                                    left join product_template pt on (pp.product_tmpl_id=pt.id)
                                    left join product_category pc on (pt.categ_id=pc.id)
                                    left join res_users ru on (ai.user_id=ru.id)
                                    left join res_partner rp on (ru.partner_id=rp.id)
                            where   ai.state in ('open') 
                                and ru.sale_team_id= %s and ai.date_invoice between %s and %s and
                                pc.type = %s """,(self.budget_id.id,self.budget_id.from_date,self.budget_id.to_date,self.type))
            value = self.env.cr.dictfetchall()
            if value:
                self.invoice_value = value[0]['total']
            else:
                self.invoice_value = 0.0
        else:
            self.invoice_value = 0.0
        
        
    type = fields.Selection([
        ('normal', 'Product'),('cloud','Cloud EYE'),('cloud_new','Cloud Service'),('tech','Technical Support Group'),('db','Database'),('odoo','Odoo'),('can','CAN'),('tod','TOD'),('rental','Rental'),('tec','TEC'),('top','TOP'),('tor_new','TOR-NEW'),('tor','TOR'),('tos','TOS'),('tos_new','TOS-NEW'),
        ('aws', 'AWS'),('aws_new', 'AWS-Service')], 'Category', default='normal',
        help="A category of the view type is a virtual category that can be used as the parent of another category to create a hierarchical structure.")
    budget_id=fields.Many2one('crm.team','Sales Team')
    jan=fields.Float('Jan',default=0.0)
    feb=fields.Float('Feb',default=0.0)
    mar=fields.Float('March',default=0.0)
    apr=fields.Float('April',default=0.0)
    may=fields.Float('May',default=0.0)
    jun=fields.Float('June',default=0.0)
    jul=fields.Float('July',default=0.0)
    aug=fields.Float('Aug',default=0.0)
    sep=fields.Float('Sep',default=0.0)
    octt=fields.Float('Oct',default=0.0)
    nov=fields.Float('Nov',default=0.0)
    dec=fields.Float('Dec',default=0.0)
    invoice_value = fields.Float('Invoice Value', compute='_compute_invoice_value')

    
