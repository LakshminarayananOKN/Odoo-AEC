{
    'name': 'Opportunity To Tender',
    'version': '1.0',
    'category': 'CRM',
    'sequence': 4,
    'summary': 'Opportunity,Tender,Purchase Order,Sale Quotations ',
    'icon': "/fnet_crm/static/img/iswasu.png",
    'description': """

    This application allows to create the tender in opportunity when Won stage.
    Then the relavent tender call the many purchase quotations.
    The sale quots is create on the bid received state in purchase quotation 
    If you select any product in comportable RFQ which is converted the sale quotations remaining 
    RFQ can be changed cancel state
    """,
    'author': 'Futurenet',
    'website': 'http://www.futurenet.in',
    'depends': ['sale','crm','base','sale_crm','purchase_requisition','purchase','stage','account'],
    'data': [
        'views/sale_view.xml',
        'views/oppor_orderline_view.xml',
        'views/purchase_requisition_view.xml',
        'views/purchase_view.xml',
        'data/rights_data.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/product_view.xml',
        'views/sale_team_view.xml',  
        'wizard/budget.xml',
        'report/report_budget.xml',
        #~ 'views/sale_config_setting_view.xml',    
            ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
