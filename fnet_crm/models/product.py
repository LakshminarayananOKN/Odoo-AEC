import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, tools, _


class product_template(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'
    

    type = fields.Selection([
        ('consu', _('Consumable')),
        ('service', _('Service')),
        ('product',_('Stockable Product'))], string='Product Type', default='product', required=True,
        help='A stockable product is a product for which you manage stock. The "Inventory" app has to be installed.\n'
             'A consumable product, on the other hand, is a product for which stock is not managed.\n'
             'A service is a non-material product you provide.\n'
             'A digital content is a non-material product you sell online. The files attached to the products are the one that are sold on '
             'the e-commerce such as e-books, music, pictures,... The "Digital Product" module has to be installed.')
    
    list_price = fields.Float(
        'Sale Price', default=0.0,
        digits=dp.get_precision('Product Price'),
        help="Base price to compute the customer price. Sometimes called the catalog price.")
