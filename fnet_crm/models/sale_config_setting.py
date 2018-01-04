from odoo import api, fields, models

class SaleConfigurations(models.TransientModel):
    _inherit = 'sale.config.settings'
    
    
    def _get_limit_value(self):
        approve_obj=self.env['approve.limit']
        val=approve_obj.search[('id','=',1)]
        if val:
           return val.id
        return False      


    limit_id=fields.Many2one('approve.limit','Manager Approval Limit',default=_get_limit_value)
    
    
    
