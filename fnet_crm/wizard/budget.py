# -*- coding: utf-8 -*-

import time
from datetime import datetime
from dateutil import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import xlsxwriter
import StringIO
import base64
import itertools
from xlsxwriter.utility import xl_col_to_name
import calendar

class BudgetWizard(models.TransientModel):

    _name = 'budget.wizard'
    _description = 'Budget Report'

    date_from = fields.Date(string='From date', required=True,default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='To date', required=True,default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    filedata=fields.Binary('Download file',readonly=True)
    filename=fields.Char('Filename', size = 64, readonly=True)
    
    def _build_contexts(self, data):
        result = {}
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        return result
    
    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        return self._print_report(data)
    
    def _print_report(self, data):
        res = {}
        data['form'].update(self.read(['date_from'])[0])
        data['form'].update(self.read(['date_to'])[0])
        if not data['form']['date_from']:
            raise UserError(_('You must set a start date.'))
        data['form'].update(res)
        return self.env['report'].with_context(landscape=True).get_action(self, 'fnet_crm.report_budget', data=data)
    
        
    def get_details(self):
        d={ 1 : 'Jan', 2 :'Feb',3:'March',4:'Apr',5:'May',6:'June',7:'July',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec' }
        from_date=datetime.strptime(self.date_from,'%Y-%m-%d')
        to_date=datetime.strptime(self.date_to,'%Y-%m-%d')
        month=from_date.month
        to_month=to_date.month
        budget=[]
        for i in range(int(month),int(to_month)+1):
            budget.append(('B'+d[i],'Budget for '+ str(d[i])))
            budget.append(('A'+d[i],'Actual for '+ str(d[i])))
        budget.append(('Btot','Budget Total'))
        budget.append(('Atot','Actual Total'))
        return budget
    
    def get_category(self,budget_val):
        d={ 1 : 'Jan', 2 :'Feb',3:'March',4:'Apr',5:'May',6:'June',7:'July',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec' }
        current_year=datetime.now().year
        from_date=datetime.strptime(self.date_from,'%Y-%m-%d')
        to_date=datetime.strptime(self.date_to,'%Y-%m-%d')
        month=from_date.month
        to_month=to_date.month
        year=from_date.year
        to_year=to_date.year
        mon=[i for i in range(int(month),int(to_month)+1)]
        date=[]
        if len(mon) != 0:
            for val in mon:
                if mon < 12:
                    last_date=calendar.monthrange(year,val)
                    date.append((str(year)+ '-' + str(val) + '-' +'01',str(year)+ '-' + str(val) + '-' +str(last_date[1])))
                else:
                    last_date=calendar.monthrange(to_year,val)
                    date.append((str(to_year)+ '-' + str(val) + '-' +'01',str(year)+ '-' + str(val) + '-' +str(last_date[1])))
        where=""
        new_where=""
        for val in date:
            where+="""COALESCE(sum(CASE WHEN date_from >= '%s' and date_to <= '%s' THEN budget ELSE 0 END),'0') "B%s" ,"""  %(val[0],val[1],str(d[datetime.strptime(val[0],'%Y-%m-%d').month]))
            where+="""COALESCE(sum(CASE WHEN date_from >= '%s' and date_to <= '%s' THEN actual ELSE 0 END),'0') "A%s","""%(val[0],val[1],str(d[datetime.strptime(val[0],'%Y-%m-%d').month]))
        categ={'normal':'Product','cloud':'Cloud EYE','tech':'Technical Support Group','db':'Database','odoo':'Odoo','can':'CAN','tod':'TOD',
        'rental':'Rental','tec':'TEC','top':'TOP','tor':'TOR','tos':'TOS','aws': 'AWS'}
        budget_value=[]
        self.env.cr.execute("""
                                SELECT DISTINCT st.type as type
                                FROM sale_target_line st
                                WHERE st.date_from >= '%s' and st.date_to <= '%s'
                            """%(str(self.date_from),str(self.date_to)))
        category = self.env.cr.dictfetchall()
        for i in category:
            self.env.cr.execute("""
                                    SELECT  %s 
                                    FROM 
                                    (SELECT  st.target_amount as budget,
                                        (st.target_achived/st.target_amount)*100 as actual,
                                        rr.name as sales_person,
                                        st.type,
                                        st.date_from,
                                        st.date_to
                                    FROM sale_target_line st
                                    LEFT JOIN hr_employee hr on (st.employee_id=hr.id)
                                    LEFT JOIN resource_resource rr on (rr.name=hr.name_related)
                                    LEFT JOIN res_users ru on (rr.user_id=ru.id)
                                    WHERE st.date_from >= '%s' and st.date_to <= '%s' and st.type = '%s'
                                    ) temp
                                    GROUP BY type
                                    ORDER by type """%(str(where[0:len(where)-1]),str(self.date_from),str(self.date_to),i['type']))
            budget = [j for j in self.env.cr.dictfetchall()]
            new_where+="""COALESCE(sum(CASE WHEN date_from >= '%s' and date_to <= '%s' THEN budget ELSE 0 END),'0') "Btot" ,"""  %(str(self.date_from),str(self.date_to))
            new_where+="""COALESCE(sum(CASE WHEN date_from >= '%s' and date_to <= '%s' THEN actual ELSE 0 END),'0') "Atot" ,"""  %(str(self.date_from),str(self.date_to))
            self.env.cr.execute("""
                                    SELECT  %s 
                                    FROM 
                                    (SELECT  st.target_amount as budget,
                                        (st.target_achived/st.target_amount)*100 as actual,
                                        rr.name as sales_person,
                                        st.type,
                                        st.date_from,
                                        st.date_to
                                    FROM sale_target_line st
                                    LEFT JOIN hr_employee hr on (st.employee_id=hr.id)
                                    LEFT JOIN resource_resource rr on (rr.name=hr.name_related)
                                    LEFT JOIN res_users ru on (rr.user_id=ru.id)
                                    WHERE st.date_from >= '%s' and st.date_to <= '%s' and st.type = '%s'
                                    ) temp
                                    GROUP BY type
                                    ORDER by type """%(str(new_where[0:len(new_where)-1]),str(self.date_from),str(self.date_to),i['type']))
            total = [j for j in self.env.cr.dictfetchall()]
            for val in budget:
                s = list(val.get(i) for i in budget_val[0:-2])
                s.append(total[0]['Btot'])
                s.append(total[0]['Atot'])
                budget_value.append({'categ':i['type'],'type':categ[i['type']],'total':s})
        return budget_value
    
    def get_revenue(self,budget_val,option):
        d={ 1 : 'Jan', 2 :'Feb',3:'March',4:'Apr',5:'May',6:'June',7:'July',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec' }
        from_date=datetime.strptime(self.date_from,'%Y-%m-%d')
        to_date=datetime.strptime(self.date_to,'%Y-%m-%d')
        month=from_date.month
        to_month=to_date.month
        year=from_date.year
        to_year=to_date.year
        mon=[i for i in range(int(month),int(to_month)+1)]
        date=[]
        if len(mon) != 0:
            for val in mon:
                if mon < 12:
                    last_date=calendar.monthrange(year,val)
                    date.append((str(year)+ '-' + str(val) + '-' +'01',str(year)+ '-' + str(val) + '-' +str(last_date[1])))
                else:
                    last_date=calendar.monthrange(to_year,val)
                    date.append((str(to_year)+ '-' + str(val) + '-' +'01',str(year)+ '-' + str(val) + '-' +str(last_date[1])))
        where=""
        new_where=""
        for val in date:
            where+="""COALESCE(sum(CASE WHEN date_from >= '%s' and date_to <= '%s' THEN budget ELSE 0 END),'0') "B%s" ,"""  %(val[0],val[1],str(d[datetime.strptime(val[0],'%Y-%m-%d').month]))
            where+="""COALESCE(sum(CASE WHEN date_from >= '%s' and date_to <= '%s' THEN actual ELSE 0 END),'0') "A%s","""%(val[0],val[1],str(d[datetime.strptime(val[0],'%Y-%m-%d').month]))
        if option == 'percent':
            self.env.cr.execute("""
                                SELECT  %s
                                FROM 
                                (SELECT  st.target_amount as budget,
                                    (st.target_achived/st.target_amount)*100 as actual,
                                    st.date_from,st.date_to
                                FROM sale_target_line st
                                LEFT JOIN hr_employee hr on (st.employee_id=hr.id)
                                LEFT JOIN resource_resource rr on (rr.name=hr.name_related)
                                LEFT JOIN res_users ru on (rr.user_id=ru.id)
                                WHERE st.date_from >= '%s' and st.date_to <= '%s'
                                ) temp"""%(str(where[0:len(where)-1]),str(self.date_from),str(self.date_to)))
        if option == 'value':
            self.env.cr.execute("""
                                SELECT  %s
                                FROM 
                                (SELECT  st.target_amount as budget,
                                         st.target_achived as actual,
                                         st.date_from,st.date_to
                                FROM sale_target_line st
                                LEFT JOIN hr_employee hr on (st.employee_id=hr.id)
                                LEFT JOIN resource_resource rr on (rr.name=hr.name_related)
                                LEFT JOIN res_users ru on (rr.user_id=ru.id)
                                WHERE st.date_from >= '%s' and st.date_to <= '%s'
                                ) temp"""%(str(where[0:len(where)-1]),str(self.date_from),str(self.date_to)))
        budget_value=[]
        budget = [j for j in self.env.cr.dictfetchall()]
        new_where+="""COALESCE(sum(CASE WHEN date_from >= '%s' and date_to <= '%s' THEN budget ELSE 0 END),'0') "Btot" ,"""  %(str(self.date_from),str(self.date_to))
        new_where+="""COALESCE(sum(CASE WHEN date_from >= '%s' and date_to <= '%s' THEN actual ELSE 0 END),'0') "Atot" ,"""  %(str(self.date_from),str(self.date_to))
        if option == 'percent':
            self.env.cr.execute("""
                                    SELECT  %s 
                                    FROM 
                                    (SELECT  st.target_amount as budget,
                                        (st.target_achived/st.target_amount)*100 as actual,
                                        rr.name as sales_person,
                                        st.type,
                                        st.date_from,
                                        st.date_to
                                    FROM sale_target_line st
                                    LEFT JOIN hr_employee hr on (st.employee_id=hr.id)
                                    LEFT JOIN resource_resource rr on (rr.name=hr.name_related)
                                    LEFT JOIN res_users ru on (rr.user_id=ru.id)
                                    WHERE st.date_from >= '%s' and st.date_to <= '%s'
                                    ) temp"""%(str(new_where[0:len(new_where)-1]),str(self.date_from),str(self.date_to)))
        if option == 'value':
            self.env.cr.execute("""
                                    SELECT  %s 
                                    FROM 
                                    (SELECT  st.target_amount as budget,
                                            st.target_achived as actual,
                                        rr.name as sales_person,
                                        st.type,
                                        st.date_from,
                                        st.date_to
                                    FROM sale_target_line st
                                    LEFT JOIN hr_employee hr on (st.employee_id=hr.id)
                                    LEFT JOIN resource_resource rr on (rr.name=hr.name_related)
                                    LEFT JOIN res_users ru on (rr.user_id=ru.id)
                                    WHERE st.date_from >= '%s' and st.date_to <= '%s'
                                    ) temp"""%(str(new_where[0:len(new_where)-1]),str(self.date_from),str(self.date_to)))
        total = [j for j in self.env.cr.dictfetchall()]
        for val in budget:
            s = list(val.get(i) for i in budget_val[0:-2])
            s.append(total[0]['Btot'])
            s.append(total[0]['Atot'])
            budget_value.append({'total':s})
        return budget_value

    def get_purchase(self,budget_val):
        d={ 1 : 'Jan', 2 :'Feb',3:'March',4:'Apr',5:'May',6:'June',7:'July',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec' }
        from_date=datetime.strptime(self.date_from,'%Y-%m-%d')
        to_date=datetime.strptime(self.date_to,'%Y-%m-%d')
        month=from_date.month
        to_month=to_date.month
        year=from_date.year
        to_year=to_date.year
        mon=[i for i in range(int(month),int(to_month)+1)]
        date=[]
        if len(mon) != 0:
            for val in mon:
                if mon < 12:
                    last_date=calendar.monthrange(year,val)
                    date.append((str(year)+ '-' + str(val) + '-' +'01',str(year)+ '-' + str(val) + '-' +str(last_date[1])))
                else:
                    last_date=calendar.monthrange(to_year,val)
                    date.append((str(to_year)+ '-' + str(val) + '-' +'01',str(year)+ '-' + str(val) + '-' +str(last_date[1])))
        where=""
        new_where=""
        for val in date:
            where+="""COALESCE(sum(CASE WHEN budget > 0 THEN budget ELSE 0 END),'0') "B%s","""%(str(d[datetime.strptime(val[0],'%Y-%m-%d').month]))
            where+="""COALESCE(sum(CASE WHEN date_invoice >= '%s' and date_invoice <= '%s' THEN actual ELSE 0 END),'0') "A%s","""%(val[0],val[1],str(d[datetime.strptime(val[0],'%Y-%m-%d').month]))
        self.env.cr.execute("""
                            SELECT  %s
                            FROM 
                            (SELECT COALESCE(SUM(CASE WHEN ai.type = 'in_invoice' THEN ail.price_subtotal ELSE -ail.price_subtotal END),'0') AS actual,
                                    COALESCE(SUM(CASE WHEN ai.type = 'out_invoice' THEN ail.price_subtotal ELSE -ail.price_subtotal END),'0') AS budget,
                                    ai.date_invoice
                                    FROM account_invoice ai
                                    LEFT JOIN account_invoice_line ail on (ail.invoice_id=ai.id)
                                    LEFT JOIN product_product pp on (ail.product_id=pp.id)
                                    LEFT JOIN product_template pt on (pp.product_tmpl_id=pt.id)
                                    LEFT JOIN product_category pc on (pt.categ_id=pc.id)
                                    LEFT JOIN res_partner rpp on (ai.partner_id=rpp.id)
                                    JOIN account_move am ON (am.id = ai.move_id)
                                    WHERE  ai.date_invoice >= '%s' 
                                    AND ai.date_invoice <= '%s' AND ai.state in ('open','paid')
                                    AND rpp.supplier=True 
                                    AND ai.type in ('in_invoice','in_refund')
                                    GROUP BY ai.date_invoice
                            ) temp"""%(str(where[0:len(where)-1]),str(self.date_from),str(self.date_to)))
        budget_value=[]
        budget = [j for j in self.env.cr.dictfetchall()]
        new_where+="""COALESCE(sum(CASE WHEN budget > 0 THEN budget ELSE 0 END),'0') "Btot" ,"""
        new_where+="""COALESCE(sum(CASE WHEN date_invoice >= '%s' and date_invoice <= '%s' THEN actual ELSE 0 END),'0') "Atot" ,"""  %(str(self.date_from),str(self.date_to))
        self.env.cr.execute("""
                                SELECT  %s 
                                FROM 
                                (SELECT COALESCE(SUM(CASE WHEN ai.type = 'in_invoice' THEN ail.price_subtotal ELSE -ail.price_subtotal END),'0') AS actual,
                                        COALESCE(SUM(CASE WHEN ai.type = 'out_invoice' THEN ail.price_subtotal ELSE -ail.price_subtotal END),'0') AS budget,
                                    ai.date_invoice
                                    FROM account_invoice ai
                                    LEFT JOIN account_invoice_line ail on (ail.invoice_id=ai.id)
                                    LEFT JOIN product_product pp on (ail.product_id=pp.id)
                                    LEFT JOIN product_template pt on (pp.product_tmpl_id=pt.id)
                                    LEFT JOIN product_category pc on (pt.categ_id=pc.id)
                                    LEFT JOIN res_partner rpp on (ai.partner_id=rpp.id)
                                    JOIN account_move am ON (am.id = ai.move_id)
                                    WHERE  ai.date_invoice >= '%s' 
                                    AND ai.date_invoice <= '%s' AND ai.state in ('open','paid')
                                    AND rpp.supplier=True 
                                    AND ai.type in ('in_invoice','in_refund')
                                    GROUP BY ai.date_invoice
                                ) temp"""%(str(new_where[0:len(new_where)-1]),str(self.date_from),str(self.date_to)))
        total = [j for j in self.env.cr.dictfetchall()]
        for val in budget:
            s = list(val.get(i) for i in budget_val[0:-2])
            s.append(total[0]['Btot'])
            s.append(total[0]['Atot'])
            budget_value.append({'total':s})
        return budget_value
        
    def get_sale_details(self,category,budget_val):
        d={ 1 : 'Jan', 2 :'Feb',3:'March',4:'Apr',5:'May',6:'June',7:'July',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec' }
        current_year=datetime.now().year
        from_date=datetime.strptime(self.date_from,'%Y-%m-%d')
        to_date=datetime.strptime(self.date_to,'%Y-%m-%d')
        month=from_date.month
        to_month=to_date.month
        year=from_date.year
        to_year=to_date.year
        mon=[i for i in range(int(month),int(to_month)+1)]
        date=[]
        if len(mon) != 0:
            for val in mon:
                if mon < 12:
                    last_date=calendar.monthrange(year,val)
                    date.append((str(year)+ '-' + str(val) + '-' +'01',str(year)+ '-' + str(val) + '-' +str(last_date[1])))
                else:
                    last_date=calendar.monthrange(to_year,val)
                    date.append((str(to_year)+ '-' + str(val) + '-' +'01',str(year)+ '-' + str(val) + '-' +str(last_date[1])))
        where=""
        new_where=""
        for val in date:
            where+="""COALESCE(sum(CASE WHEN date_from >= '%s' and date_to <= '%s' THEN budget ELSE 0 END),'0') "B%s" ,"""  %(val[0],val[1],str(d[datetime.strptime(val[0],'%Y-%m-%d').month]))
            where+="""COALESCE(sum(CASE WHEN date_from >= '%s' and date_to <= '%s' THEN actual ELSE 0 END),'0') "A%s","""%(val[0],val[1],str(d[datetime.strptime(val[0],'%Y-%m-%d').month]))
        categ={'normal':'Product','cloud':'Cloud EYE','tech':'Technical Support Group','db':'Database','odoo':'Odoo','can':'CAN','tod':'TOD',
        'rental':'Rental','tec':'TEC','top':'TOP','tor':'TOR','tos':'TOS','aws': 'AWS'}
        budget_value=[]
        self.env.cr.execute("""
                                SELECT  DISTINCT rr.name as sales_person,ru.id
                                    FROM sale_target_line st
                                    LEFT JOIN hr_employee hr on (st.employee_id=hr.id)
                                    LEFT JOIN resource_resource rr on (rr.name=hr.name_related)
                                    LEFT JOIN res_users ru on (rr.user_id=ru.id)
                                    WHERE st.date_from >= '%s' and st.date_to <= '%s' and st.type = '%s'
                            """%(str(self.date_from),str(self.date_to),category))
        sale_person = self.env.cr.dictfetchall()
        for i in sale_person:
            self.env.cr.execute("""
                                    SELECT  %s 
                                    FROM 
                                    (SELECT  st.target_amount as budget,
                                        (st.target_achived/st.target_amount)*100 as actual,
                                        rr.name as sales_person,
                                        st.type,
                                        st.date_from,
                                        st.date_to
                                    FROM sale_target_line st
                                    LEFT JOIN hr_employee hr on (st.employee_id=hr.id)
                                    LEFT JOIN resource_resource rr on (rr.name=hr.name_related)
                                    LEFT JOIN res_users ru on (rr.user_id=ru.id)
                                    WHERE st.date_from >= '%s' and st.date_to <= '%s' and ru.id = '%s' and st.type='%s'
                                    ) temp
                                    GROUP BY type
                                    ORDER by type """%(str(where[0:len(where)-1]),str(self.date_from),str(self.date_to),i['id'],category))
            budget = [j for j in self.env.cr.dictfetchall()]
            new_where+="""COALESCE(sum(CASE WHEN date_from >= '%s' and date_to <= '%s' THEN budget ELSE 0 END),'0') "Btot" ,"""  %(str(self.date_from),str(self.date_to))
            new_where+="""COALESCE(sum(CASE WHEN date_from >= '%s' and date_to <= '%s' THEN actual ELSE 0 END),'0') "Atot" ,"""  %(str(self.date_from),str(self.date_to))
            self.env.cr.execute("""
                                    SELECT  %s 
                                    FROM 
                                    (SELECT  st.target_amount as budget,
                                        (st.target_achived/st.target_amount)*100 as actual,
                                        rr.name as sales_person,
                                        st.type,
                                        st.date_from,
                                        st.date_to
                                    FROM sale_target_line st
                                    LEFT JOIN hr_employee hr on (st.employee_id=hr.id)
                                    LEFT JOIN resource_resource rr on (rr.name=hr.name_related)
                                    LEFT JOIN res_users ru on (rr.user_id=ru.id)
                                    WHERE st.date_from >= '%s' and st.date_to <= '%s' and ru.id = '%s' and st.type='%s'
                                    ) temp
                                    GROUP BY type
                                    ORDER by type """%(str(new_where[0:len(new_where)-1]),str(self.date_from),str(self.date_to),i['id'],category))
            total = [j for j in self.env.cr.dictfetchall()]
            for val in budget:
                s = list(val.get(i) for i in budget_val[0:-2])
                s.append(total[0]['Btot'])
                s.append(total[0]['Atot'])
                budget_value.append({'sale_person':i['sales_person'],'total':s})
        return budget_value
                    
                
    def excel_report(self):
        data=self.read(['date_from', 'date_to'])[0]
        f_date =datetime.strptime(data['date_from'],'%Y-%m-%d')
        date_str = f_date.strftime('%d-%m-%Y')
        t_date =datetime.strptime(data['date_to'],'%Y-%m-%d')
        date_str_to = t_date.strftime('%d-%m-%Y')
        output = StringIO.StringIO()
        #~ url = os.path.dirname(os.path.realpath(''))
        url = '/home/ubuntu/odoo/report'
        workbook = xlsxwriter.Workbook(url+'budget.xlsx')
        worksheet = workbook.add_worksheet()
        merge_format = workbook.add_format({'bold': 1,'border': 1,'font_size':15,'align': 'center','valign': 'vcenter', 'fg_color': 'white','font_name':'Liberation Serif',})
        merge_format1 = workbook.add_format({'align': 'right','valign': 'vcenter','font_name':'Liberation Serif',})
        merge_format2 = workbook.add_format({'bold': 1,'align': 'center','valign': 'vcenter','underline': 'underline','font_name':'Liberation Serif',})
        merge_format3 = workbook.add_format({ 'bold': 1, 'border': 1,'align': 'center','valign': 'vcenter','fg_color': 'gray','font_name':'Liberation Serif',})
        merge_format4 = workbook.add_format({'align': 'center','valign': 'vcenter','font_name':'Liberation Serif',})
        merge_format5 = workbook.add_format({'bold': 1,'align': 'left','valign': 'vcenter','font_name':'Liberation Serif',})
        merge_format6 = workbook.add_format({'bold': 1,'align': 'right','valign': 'vcenter','font_name':'Liberation Serif',})
        worksheet.set_column('A:A', 7)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 25)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('E:E', 25)
        worksheet.set_column('F:F', 25)
        worksheet.set_column('G:G', 28)
        worksheet.set_column('H:H', 25)
        worksheet.set_column('I:I', 25)
        worksheet.set_column('J:J', 25)
        worksheet.set_column('K:K', 25)
        worksheet.set_column('L:L', 25)
        worksheet.merge_range('A1:H1',self.env.user.company_id.name, merge_format)
        worksheet.merge_range('A2:H2', 'BUDGET / ACTUAL SUMMARY REPORT', merge_format2)
        worksheet.merge_range('A3:H3', date_str + '  to  ' + date_str_to, merge_format2)
        worksheet.merge_range('A4:H4', ' ', merge_format1)
        worksheet.write('A5',"S.No",merge_format3)
        worksheet.write('B5',"Category/Salesperson",merge_format3)
        get = self.get_details()
        n=2
        c=5
        budget=[]
        for o in get:
            req = xl_col_to_name(n)
            budget.append(o[0])
            worksheet.write(req+str(c), o[1],merge_format3)
            n=n+1
        categ= self.get_category(budget)
        col=6
        c=1
        last_row = 5
        for val in categ:
            worksheet.write('A'+str(col),str(c) ,merge_format5)
            worksheet.write('B'+str(col), val['type'],merge_format5)
            d=2
            a=len(val['total'])
            if a!=0:
                for k in val['total']:
                    test = xl_col_to_name(d)
                    if k != 0.0:
                        worksheet.write(test+str(col), ("{0:.2f}".format(k)),merge_format6)
                        d=d+1
                    else:
                        worksheet.write(test+str(col),0.0,merge_format6)
                        d =d+1
            sale_person= self.get_sale_details(val['categ'],budget)
            column=col+1
            for val in sale_person:
                worksheet.write('A' + str(column),'', merge_format1)
                worksheet.write('B' + str(column), val['sale_person'], merge_format1)
                a=len(val['total'])
                row=2
                if a!=0:
                    for k in val['total']:
                        test = xl_col_to_name(row)
                        if k != 0.0:
                            worksheet.write(test+str(column), ("{0:.2f}".format(k)),merge_format1)
                            row=row+1
                        else:
                            worksheet.write(test+str(column),0.0,merge_format1)
                            row=row+1
                column=column+1
            col=column+1
            c=c+1
            last_row = last_row+1
        revenue= self.get_revenue(budget,'value')
        worksheet.write('B'+str(col), 'Total Revenue' ,merge_format5)   
        for val in revenue:
            a=len(val['total'])
            row=2
            if a!=0:
                for k in val['total']:
                    test = xl_col_to_name(row)
                    if k != 0.0:
                        worksheet.write(test+str(col), k,merge_format6)
                        row=row+1
                    else:
                        worksheet.write(test+str(col),0.0,merge_format6)
                        row=row+1
            col=col+1
        worksheet.write('B'+str(col), 'Purchase Cost' ,merge_format5)  
        purchase= self.get_purchase(budget)
        for val in purchase:
            a=len(val['total'])
            row=2
            if a!=0:
                for k in val['total']:
                    test = xl_col_to_name(row)
                    if k != 0.0:
                        worksheet.write(test+str(col), k,merge_format6)
                        row=row+1
                    else:
                        worksheet.write(test+str(col),0.0,merge_format6)
                        row=row+1
            col=col+1
        worksheet.write('B'+str(col), 'Gross Margin' ,merge_format5)  
        revenue_value= self.get_revenue(budget,'value')[0]['total']
        purchase_value= self.get_purchase(budget)[0]['total']
        gross=[b - a for (b, a) in zip(revenue_value,purchase_value)]
        rec={'total':gross}
        gross_value=[]
        gross_value.append(rec)
        for val in gross_value:
            a=len(val['total'])
            row=2
            if a!=0:
                for k in val['total']:
                    test = xl_col_to_name(row)
                    if k != 0.0:
                        worksheet.write(test+str(col), k,merge_format6)
                        row=row+1
                    else:
                        worksheet.write(test+str(col),0.0,merge_format6)
                        row=row+1
            col=col+1
        workbook.close()
        fo = open(url+'budget.xlsx', "rb+")
        data=fo.read()
        out=base64.encodestring(data)
        self.write({'filedata':out,'filename':'Budget.xlsx'})
        return {'name':'payroll register',
                'res_model':'budget.wizard',
                'type':'ir.actions.act_window',
                'view_type':'form',
                'view_mode':'form',
                'target':'new',
                'nodestroy': True,
                'res_id': self.id,}

