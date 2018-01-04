#~ from datetime import datetime
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
import calendar



class Report_Aged_Partner_Balance(models.AbstractModel):
    _name = 'report.fnet_crm.report_budget'

        
        
    def get_details(self,rec):
        d={ 1 : 'Jan', 2 :'Feb',3:'March',4:'Apr',5:'May',6:'June',7:'July',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec' }
        from_date=datetime.strptime(rec.date_from,'%Y-%m-%d')
        to_date=datetime.strptime(rec.date_to,'%Y-%m-%d')
        month=from_date.month
        to_month=to_date.month
        budget=[]
        for i in range(int(month),int(to_month)+1):
            budget.append(('B'+d[i],'Budget for '+ str(d[i])))
            budget.append(('A'+d[i],'Actual for '+ str(d[i])))
        return budget
            

    def get_category(self,docs,budget_val):
        d={ 1 : 'Jan', 2 :'Feb',3:'March',4:'Apr',5:'May',6:'June',7:'July',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec' }
        current_year=datetime.now().year
        from_date=datetime.strptime(docs.date_from,'%Y-%m-%d')
        to_date=datetime.strptime(docs.date_to,'%Y-%m-%d')
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
                            """%(str(docs.date_from),str(docs.date_to)))
        category = self.env.cr.dictfetchall()
        for i in category:
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
                                    WHERE st.date_from >= '%s' and st.date_to <= '%s' and st.type = '%s'
                                    ) temp
                                    GROUP BY type
                                    ORDER by type """%(str(where[0:len(where)-1]),str(docs.date_from),str(docs.date_to),i['type']))
            budget = [j for j in self.env.cr.dictfetchall()]
            for val in budget:
                s = list(val.get(i) for i in budget_val)
                budget_value.append({'categ':i['type'],'type':categ[i['type']],'total':s})
        return budget_value
        
    def get_sale_details(self,docs,category,budget_val):
        print category
        d={ 1 : 'Jan', 2 :'Feb',3:'March',4:'Apr',5:'May',6:'June',7:'July',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec' }
        current_year=datetime.now().year
        from_date=datetime.strptime(docs.date_from,'%Y-%m-%d')
        to_date=datetime.strptime(docs.date_to,'%Y-%m-%d')
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
                            """%(str(docs.date_from),str(docs.date_to),category))
        sale_person = self.env.cr.dictfetchall()
        print sale_person,where
        for i in sale_person:
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
                                    WHERE st.date_from >= '%s' and st.date_to <= '%s' and ru.id = '%s' and st.type='%s'
                                    ) temp
                                    GROUP BY type
                                    ORDER by type """%(str(where[0:len(where)-1]),str(docs.date_from),str(docs.date_to),i['id'],category))
            budget = [j for j in self.env.cr.dictfetchall()]
            for val in budget:
                s = list(val.get(i) for i in budget_val)
                budget_value.append({'sale_person':i['sales_person'],'total':s})
        print budget_value
        return budget_value


    @api.model
    def render_html(self, docids, data=None):
        Report = self.env['report']
        balance_report = Report._get_report_from_name('fnet_crm.report_budget')
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        budget = self.env['budget.wizard'].browse(active_ids)
        docargs = {
            'doc_ids': self.ids,
            'docs': budget,
            'get_category': self.get_category,
            'get_sale_details': self.get_sale_details,
            'get_details': self.get_details,        }
        return Report.render('fnet_crm.report_budget', docargs)

    
