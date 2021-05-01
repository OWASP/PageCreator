import requests
import json
import os
import logging
from datetime import datetime
import time
from datetime import timedelta

class OWASPCopper:

    cp_base_url = "https://api.prosperworks.com/developer_api/v1/"
    cp_projects_fragment = "projects/"
    cp_opp_fragment = "opportunities/"
    cp_pipeline_fragment = "pipelines/"
    cp_people_fragment = "people/"
    cp_related_fragment = ':entity/:entity_id/related'
    cp_custfields_fragment = 'custom_field_definitions/'
    cp_search_fragment = "search"
    
    # Custom Field Definition Ids
    cp_project_type = 399609
    cp_project_type_option_global_event = 899314
    cp_project_type_option_regional_event = 899315
    cp_project_type_option_chapter = 899316
    cp_project_type_option_global_partner = 900407
    cp_project_type_option_local_partner = 900408
    cp_project_type_option_project = 1378082
    cp_project_type_option_committee = 1378083
    cp_project_github_repo = 399740
    # event specific
    cp_project_event_start_date = 392473
    cp_project_event_website = 395225
    cp_project_event_sponsorship_url = 395226
    cp_project_event_projected_revenue = 392478
    cp_project_event_sponsors = 392480
    cp_project_event_jira_ticket = 394290
    cp_project_event_approved_date = 392477
    # chapter specific
    cp_project_chapter_status = 399736
    cp_project_chapter_status_option_active = 899462
    cp_project_chapter_status_option_inactive = 899463
    cp_project_chapter_status_option_suspended = 899464
    cp_project_chapter_region = 399739
    cp_project_chapter_region_option_africa = 899465
    cp_project_chapter_region_option_asia = 899466
    cp_project_chapter_region_option_europe = 899467
    cp_project_chapter_region_option_northamerica = 899468
    cp_project_chapter_region_option_oceania = 899469
    cp_project_chapter_region_option_southamerica = 899470
    cp_project_chapter_country = 399738
    cp_project_chapter_postal_code = 399737
    #person specific
    #inactive cp_person_group_url = 394184
    #inactive cp_person_group_type = 394186
    #inactive cp_person_group_type_option_chapter=672528
    #inactive cp_person_group_type_option_project=672529
    #inactive cp_person_group_type_option_committee=672530
    #inactive cp_person_group_participant_type = 394187
    #inactive cp_person_group_participant_type_option_participant = 672531
    #inactive cp_person_group_participant_type_option_leader = 672532
    #inactive cp_person_member_checkbox = 394880
    #inactive cp_person_leader_checkbox = 394881
    cp_person_membership = 394882
    cp_person_membership_option_student = 674397
    cp_person_membership_option_lifetime = 674398
    cp_person_membership_option_oneyear = 674395
    cp_person_membership_option_twoyear = 674396
    cp_person_membership_option_complimentary = 1506889
    cp_person_membership_start = 394883
    cp_person_membership_end = 394884
    cp_person_github_username = 395220
    #inactive cp_person_membership_number = 397651
    cp_person_external_id = 400845 #old Salesforce id
    cp_person_stripe_number = 440584
    #opportunity specific
    cp_opportunity_end_date = 400119
    cp_opportunity_autorenew_checkbox = 419575
    cp_opportunity_invoice_no = 407333  # can be the URL to the stripe payment for membership
    cp_opportunity_stripe_transaction_id = 440903
    # pipeline ids
    cp_opportunity_pipeline_id_membership = 721986

    default_headers = {
            'X-PW-AccessToken':os.environ['COPPER_API_KEY'],
            'X-PW-Application':'developer_api',
            'X-PW-UserEmail':os.environ['COPPER_USER'],
            'Content-Type':'application/json'
    }

    def GetHeaders(self):
        
        return self.default_headers
    
    def GetCustomFieldHelper(self, custom_field_id, fields):
        for field in fields:
            if field['custom_field_definition_id'] == custom_field_id:
                return field['value']
        
        return None
    
    def GetDatetimeHelper(self, datestr):
        retdate = None
        try:
            retdate = datetime.strptime(datestr, "%m/%d/%Y")
        except:
            try:
                retdate = datetime.strptime(datestr, "%Y-%m-%d")
            except:
                try:
                    retdate = datetime.strptime(datestr, "%m/%d/%y")
                except:
                    return retdate
                    
        return retdate

    def GetStartdateHelper(self, subscription_data):
        startdate = datetime.now()
        mem_type = subscription_data['membership_type']
        mem_end = self.GetDatetimeHelper(subscription_data['membership_end'])
        if mem_end != None: 
            if mem_type == 'one' or mem_type == 'complimentary' or mem_type == 'student':
                startdate = mem_end - timedelta(days=365)
            elif mem_type == 'two':
                startdate = mem_end - timedelta(days=730)
            
        return startdate

    def ListProjects(self):
        data = {
            'page_size': 200,
            'sort_by': 'name'
        }
        url = f'{self.cp_base_url}{self.cp_projects_fragment}{self.cp_search_fragment}'
        r = requests.post(url, headers=self.GetHeaders(), data=json.dumps(data))
        if r.ok:
            return r.text
        
        return ''
        
    def ListOpportunities(self, page_number = 1, pipeline_ids=None, status_ids=[0, 1, 2, 3]):
        data = {
            'page_size': 200,
            'sort_by': 'name',
            'page_number': page_number,
            'status_ids': status_ids,
        }

        if pipeline_ids:
            data['pipeline_ids'] = pipeline_ids

        url = f'{self.cp_base_url}{self.cp_opp_fragment}{self.cp_search_fragment}'
        r = requests.post(url, headers=self.GetHeaders(), data=json.dumps(data))
        if r.ok:
            return r.text
        
        return ''
    
    def GetPerson(self, pid):
        url = f'{self.cp_base_url}{self.cp_people_fragment}{pid}'
        
        r = requests.get(url, headers=self.default_headers)
        if r.ok and r.text != '[]':
            return r.text
        
        return ''

    def FindPersonByEmail(self, searchtext):
        lstxt = searchtext.lower()
        if len(lstxt) <= 0:
            return ''

        # first use fetch_by_email
        url = f'{self.cp_base_url}{self.cp_people_fragment}fetch_by_email'
        data = { 'email': lstxt }
        r = requests.post(url, headers=self.GetHeaders(), data=json.dumps(data))
        if r.ok and r.text != '[]':
            return f"[{r.text}]"

        data = {
            'page_size': 5,
            'sort_by': 'name',
            'emails': [lstxt]
        }

        url = f'{self.cp_base_url}{self.cp_people_fragment}{self.cp_search_fragment}'
        
        r = requests.post(url, headers=self.GetHeaders(), data=json.dumps(data))
        if r.ok:
            return r.text
        
        return ''

    def ListMembers(self):
        members = []

        #Get One year
        data = {
            'page_size': 200,
            'sort_by': 'name',
            'custom_fields': [{
                'custom_field_definition_id': self.cp_person_membership,
                'value': self.cp_person_membership_option_oneyear,
            }]
        }

        url = f'{self.cp_base_url}{self.cp_people_fragment}{self.cp_search_fragment}'
        r = requests.post(url, headers=self.GetHeaders(), data=json.dumps(data))
        if 'X-PW-TOTAL' in r.headers:
            count = r.headers['X-PW-TOTAL']
        if not r.ok:
            return members
        
        members = json.loads(r.text)
        data = {
            'page_size': 200,
            'sort_by': 'name',
            'custom_fields': [{
                'custom_field_definition_id': self.cp_person_membership,
                'value': self.cp_person_membership_option_twoyear,
            }]
        }

        url = f'{self.cp_base_url}{self.cp_people_fragment}{self.cp_search_fragment}'
        r = requests.post(url, headers=self.GetHeaders(), data=json.dumps(data))
        if 'X-PW-TOTAL' in r.headers:
            count = r.headers['X-PW-TOTAL']
        if not r.ok:
            return members
        members.append(json.loads(r.text))
        data = {
            'page_size': 200,
            'sort_by': 'name',
            'custom_fields': [{
                'custom_field_definition_id': self.cp_person_membership,
                'value': self.cp_person_membership_option_student,
            }]
        }

        url = f'{self.cp_base_url}{self.cp_people_fragment}{self.cp_search_fragment}'
        r = requests.post(url, headers=self.GetHeaders(), data=json.dumps(data))
        if 'X-PW-TOTAL' in r.headers:
            count = r.headers['X-PW-TOTAL']
        if not r.ok:
            return members
        members.append(json.loads(r.text))

        data = {
            'page_size': 200,
            'sort_by': 'name',
            'custom_fields': [{
                'custom_field_definition_id': self.cp_person_membership,
                'value': self.cp_person_membership_option_lifetime,
            }]
        }

        url = f'{self.cp_base_url}{self.cp_people_fragment}{self.cp_search_fragment}'
        r = requests.post(url, headers=self.GetHeaders(), data=json.dumps(data))
        if 'X-PW-TOTAL' in r.headers:
            count = r.headers['X-PW-TOTAL']
        if not r.ok:
            return members
        members.append(json.loads(r.text))

        data = {
            'page_size': 200,
            'sort_by': 'name',
            'custom_fields': [{
                'custom_field_definition_id': self.cp_person_membership,
                'value': self.cp_person_membership_option_complimentary,
            }]
        }

        url = f'{self.cp_base_url}{self.cp_people_fragment}{self.cp_search_fragment}'
        r = requests.post(url, headers=self.GetHeaders(), data=json.dumps(data))
        if 'X-PW-TOTAL' in r.headers:
            count = r.headers['X-PW-TOTAL']
        if not r.ok:
            return members
        members.append(json.loads(r.text))

        return members

    def FindPersonByName(self, searchtext):
        lstxt = searchtext.lower()
        if len(lstxt) <= 0:
            return ''
            
        data = {
            'page_size': 5,
            'sort_by': 'name',
            'name': lstxt
        }

        url = f'{self.cp_base_url}{self.cp_people_fragment}{self.cp_search_fragment}'
        r = requests.post(url, headers=self.GetHeaders(), data=json.dumps(data))
        if r.ok:
            return r.text
        
        return '[]'

    def CreatePerson(self, name, email, subscription_data = None, stripe_id = None):
        # Needs Name
        if not name:
            name = 'Unknown'

        data = {
            'name':name,
            'emails': [
                {
                    'email':email,
                    'category': 'work'
                }
            ]
        }
        memstart = self.GetDatetimeHelper(subscription_data['membership_start'])
        if memstart == None:
            # so we have no start...must calculate it
            memstart = self.GetStartdateHelper(subscription_data)

        if subscription_data != None:
            fields = []
            if subscription_data['membership_type'] == 'lifetime':
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership, 
                        'value': self.cp_person_membership_option_lifetime
                    })
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership_end, 
                        'value': None
                    })
            elif subscription_data['membership_type'] == 'one':
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership, 
                        'value': self.cp_person_membership_option_oneyear
                    })
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership_end, 
                        'value': datetime.strptime(subscription_data['membership_end'], "%Y-%m-%d").strftime("%m/%d/%Y")
                    })
            elif subscription_data['membership_type'] == 'complimentary':
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership, 
                        'value': self.cp_person_membership_option_complimentary
                    })
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership_end, 
                        'value': datetime.strptime(subscription_data['membership_end'], "%Y-%m-%d").strftime("%m/%d/%Y")
                    })
            elif subscription_data['membership_type'] == 'two':
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership, 
                        'value': self.cp_person_membership_option_twoyear
                    })
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership_end, 
                        'value': datetime.strptime(subscription_data['membership_end'], "%Y-%m-%d").strftime("%m/%d/%Y")
                    })
            elif subscription_data['membership_type'] == 'student':
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership, 
                        'value': self.cp_person_membership_option_student
                    })
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership_end, 
                        'value': datetime.strptime(subscription_data['membership_end'], "%Y-%m-%d").strftime("%m/%d/%Y")
                    })

            fields.append({
                        'custom_field_definition_id' : self.cp_person_stripe_number, 
                        'value': f"https://dashboard.stripe.com/customers/{stripe_id}"
                    })

            fields.append({
                        'custom_field_definition_id' : self.cp_person_membership_start, 
                        'value': memstart.strftime("%m/%d/%Y")
                    })        
            data['custom_fields'] = fields

        url = f'{self.cp_base_url}{self.cp_people_fragment}'
        r = requests.post(url, headers=self.GetHeaders(), data=json.dumps(data))
        pid = None
        if r.ok:
            person = json.loads(r.text)
            pid = person['id']
        else:
            logging.error(f"Failed to create {name}: {r.text}")
        
        return pid

    def UpdatePerson(self, pid, subscription_data = None, stripe_id = None, other_email = None):
        
        data = {
        }

        

        if subscription_data != None:
            memstart = self.GetDatetimeHelper(subscription_data['membership_start'])
            if memstart == None:
                # so we have no start...must calculate it
                memstart = self.GetStartdateHelper(subscription_data)
                
            fields = []
            if subscription_data['membership_type'] == 'lifetime':
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership, 
                        'value': self.cp_person_membership_option_lifetime
                    })
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership_end, 
                        'value': None
                    })
            elif subscription_data['membership_type'] == 'one':
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership, 
                        'value': self.cp_person_membership_option_oneyear
                    })
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership_end, 
                        'value': datetime.strptime(subscription_data['membership_end'], "%Y-%m-%d").strftime("%m/%d/%Y")
                    })
            elif subscription_data['membership_type'] == 'honorary' or subscription_data['membership_type'] == 'complimentary':
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership, 
                        'value': self.cp_person_membership_option_complimentary
                    })
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership_end, 
                        'value': datetime.strptime(subscription_data['membership_end'], "%Y-%m-%d").strftime("%m/%d/%Y")
                    })
            elif subscription_data['membership_type'] == 'two':
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership, 
                        'value': self.cp_person_membership_option_twoyear
                    })
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership_end, 
                        'value': datetime.strptime(subscription_data['membership_end'], "%Y-%m-%d").strftime("%m/%d/%Y")
                    })
            elif subscription_data['membership_type'] == 'student':
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership, 
                        'value': self.cp_person_membership_option_student
                    })
                fields.append({
                        'custom_field_definition_id' : self.cp_person_membership_end, 
                        'value': datetime.strptime(subscription_data['membership_end'], "%Y-%m-%d").strftime("%m/%d/%Y")
                    })

            fields.append({
                        'custom_field_definition_id' : self.cp_person_stripe_number, 
                        'value': f"https://dashboard.stripe.com/customers/{stripe_id}"
                    })

            fields.append({
                        'custom_field_definition_id' : self.cp_person_membership_start, 
                        'value': memstart.strftime("%m/%d/%Y")
                    })        
            data['custom_fields'] = fields

        if other_email != None:
            # first, we have to get all the emails from the person record....
            contact_json = self.GetPerson(pid)
            if contact_json != '':
                pers = json.loads(contact_json)
                if 'emails' in pers:
                    data['emails'] = pers['emails']
                else:
                    data['emails'] = []
                data['emails'].append({'email':other_email, 'category':'other'})

        url = f'{self.cp_base_url}{self.cp_people_fragment}{pid}'
        r = requests.put(url, headers=self.GetHeaders(), data=json.dumps(data))
        pid = None
        if r.ok:
            person = json.loads(r.text)
            pid = person['id']
        
        return pid

    def CreateOpportunity(self, opp_name, contact_email):

        contact_json = self.FindPersonByEmail(contact_email)
        if contact_json == '':
            return ''
        people = json.loads(contact_json)

        # See CreateProject for adding custom fields
        
        data = {
            'name': 'opp_name',
            'primary_contact_id': people[0]['id']
        }

        url = f'{self.cp_base_url}{self.cp_opp_fragment}'
        r = requests.post(url, headers=self.GetHeaders(), data=json.dumps(data))
        if r.ok:
            return r.text
        
        return ''
    
    def FindOpportunities(self, email):
        opps = []
        contact_json = self.FindPersonByEmail(email)
        pid = None
        if contact_json != '' and contact_json !='[]':
            jsonp = json.loads(contact_json)
            if len(jsonp) > 0:
                pid = jsonp[0]['id']

        if pid != None:
            url = f'{self.cp_base_url}{self.cp_related_fragment}'
            url = url.replace(':entity_id', str(pid)).replace(':entity', 'people')
            url = url + '/opportunities'
            r = requests.get(url, headers=self.GetHeaders())
            if r.ok and r.text:
                opps = json.loads(r.text)

        return opps

    def GetOpportunity(self, oid):
        opp = None
        
        url = f'{self.cp_base_url}{self.cp_opp_fragment}{oid}'
        r = requests.get(url, headers=self.GetHeaders())
        if r.ok and r.text:
            opp = json.loads(r.text)

        return opp

    def FindMemberOpportunity(self, email, subscription_data=None ):
        opp = None
        contact_json = self.FindPersonByEmail(email)
        pid = None
        if contact_json and contact_json != '' and contact_json != '[]':
            jsonp = json.loads(contact_json)
            if len(jsonp) > 0:
                pid = jsonp[0]['id']
        
        if pid != None:
            url = f"{self.cp_base_url}{self.cp_related_fragment}"
            url = url.replace(':entity_id', str(pid)).replace(':entity', 'people')
            url = url + '/opportunities'
            r = requests.get(url, headers=self.GetHeaders())
            if r.ok and r.text:
                for item in json.loads(r.text):
                    url = url = f"{self.cp_base_url}{self.cp_opp_fragment}{item['id']}"
                    r = requests.get(url, headers=self.GetHeaders())
                    if r.ok:
                        opportunity = json.loads(r.text)
                        if 'Lifetime' in opportunity['name'] or (opportunity['name'] == 'Membership' and opportunity['monetary_value'] == 500):
                            return r.text
                        elif 'Membership' not in opportunity['name']:
                            continue
                        
                        for cfield in opportunity['custom_fields']:
                            if cfield['custom_field_definition_id'] == self.cp_opportunity_end_date:
                                mend = cfield['value']
                                if subscription_data == None: # no data, just find first non-expired membership, if any
                                    today = datetime.today()
                                    tdstamp = int(today.timestamp())
                                    if mend > tdstamp:
                                        return r.text
                                elif subscription_data['membership_end']:
                                    tend = int(datetime.strptime(subscription_data['membership_end'], "%Y-%m-%d").timestamp())
                                    if mend == tend:
                                        return r.text

        return opp

    # def FindMemberOpportunity(self, email, subscription_data):
    #     opp = None
    #     contact_json = self.FindPersonByEmail(email)
    #     pid = None
    #     if contact_json != '' and contact_json !='[]':
    #         jsonp = json.loads(contact_json)
    #         if len(jsonp) > 0:
    #             pid = jsonp[0]['id']

    #     if pid != None:
    #         url = f'{self.cp_base_url}{self.cp_related_fragment}'
    #         url = url.replace(':entity_id', str(pid)).replace(':entity', 'people')
    #         url = url + '/opportunities'
    #         r = requests.get(url, headers=self.GetHeaders())
    #         if r.ok and r.text:
    #             for item in json.loads(r.text):
    #                 url = url = f"{self.cp_base_url}{self.cp_opp_fragment}{item['id']}"
    #                 r = requests.get(url, headers=self.GetHeaders())
    #                 if r.ok:
    #                     opportunity = json.loads(r.text)
    #                     if 'Lifetime' in opportunity['name'] or (opportunity['name'] == 'Membership' and opportunity['monetary_value'] == 500):
    #                         return r.text
    #                     for cfield in opportunity['custom_fields']:
    #                         if cfield['custom_field_definition_id'] == self.cp_opportunity_end_date:
    #                             mend = cfield['value']
    #                             if subscription_data['membership_end']:
    #                                 tend = int(datetime.strptime(subscription_data['membership_end'], "%Y-%m-%d").timestamp())
    #                                 if mend == tend:
    #                                     return r.text

    #     return opp

    def CreateMemberOpportunity(self, opp_name, pid, subscription_data):
        # there is a delay before FindPerson shows up...let's pass the ID instead....
        
        pipeline = self.GetPipeline('Individual Membership')
        if pipeline == None:
            return ''

        pipeline_id = pipeline['id']
        pipeline_stage_id = 0
        for stage in pipeline['stages']:
            if stage['name'] == 'Won':
                pipeline_stage_id = stage['id']
                break

        memstart = self.GetDatetimeHelper(subscription_data['membership_start'])
        closedate = datetime.now().strftime("%m/%d/%Y")
        if memstart != None:
            closedate = memstart.strftime("%m/%d/%Y")

        data = {
            'name': opp_name,
            'primary_contact_id': pid,
            'pipeline_id': pipeline_id,
            'pipeline_stage_id': pipeline_stage_id,
            'status': 'Won',
            'close_date': closedate
        }
        
        if subscription_data != None:
            fields = []
            if subscription_data['membership_type'] == 'lifetime':
                fields.append({
                        'custom_field_definition_id' : self.cp_opportunity_end_date, 
                        'value': None
                    })
                fields.append({
                        'custom_field_definition_id' : self.cp_opportunity_autorenew_checkbox, 
                        'value': False
                    })
            else:
                fields.append({
                        'custom_field_definition_id' : self.cp_opportunity_end_date, 
                        'value': datetime.strptime(subscription_data['membership_end'], "%Y-%m-%d").strftime("%m/%d/%Y")
                    })
                renew = False
                if subscription_data['membership_recurring'] == 'yes':
                    renew = True
                fields.append({
                        'custom_field_definition_id' : self.cp_opportunity_autorenew_checkbox, 
                        'value': renew
                    })
            # if this were not complimentary, we would need the invoice number for the opportunity as well (payment url in Stripe)
            data['custom_fields'] = fields

        url = f'{self.cp_base_url}{self.cp_opp_fragment}'
        r = requests.post(url, headers=self.GetHeaders(), data=json.dumps(data))
        if r.ok:
            return r.text
        
        return ''

    def GetProject(self, proj_name):
        data = {
            'page_size': 200,
            'sort_by': 'name',
            'name': proj_name, 
        }
        url = f'{self.cp_base_url}{self.cp_projects_fragment}{self.cp_search_fragment}'
        r = requests.post(url, headers=self.GetHeaders(), data=json.dumps(data))
        if r.ok:
            return r.text
        
        return ''

    def RelateRecord(self, entity, entity_id, person_id):
        data = {
            'resource': {
                'id': person_id,
                'type': 'person'
            }
        }
        url = f'{self.cp_base_url}{self.cp_related_fragment}'
        url = url.replace(':entity_id', str(entity_id)).replace(':entity', entity)
        r = requests.post(url, headers=self.GetHeaders(), data=json.dumps(data))
        if r.ok:
            return r.text

        return ''

    def FindProject(self, proj_name):
        lstxt = proj_name.lower()

        data = {
            'page_size': 5,
            'sort_by': 'name',
            'name': lstxt
        }
        projects = []
        url = f'{self.cp_base_url}{self.cp_projects_fragment}{self.cp_search_fragment}'
        r = requests.post(url, headers=self.GetHeaders(), data=json.dumps(data))
        if r.ok:
            projects = json.loads(r.text)
            return projects
        
        return projects

    def CreateProject(self, proj_name, emails, project_type, status, region, country, postal_code, repo):
        data = {
                'name':proj_name
        }
        fields = []
        if project_type:
            fields.append({
                    'custom_field_definition_id' : self.cp_project_type, 
                    'value': project_type
                })
        if status:
            fields.append({
                    'custom_field_definition_id': self.cp_project_chapter_status,
                    'value': status
                })
        if region:
            fields.append({
                    'custom_field_definition_id': self.cp_project_chapter_region,
                    'value': region
                })
        if country:
            fields.append({
                    'custom_field_definition_id': self.cp_project_chapter_country,
                    'value': country
                })
        if postal_code:
            fields.append({
                    'custom_field_definition_id': self.cp_project_chapter_postal_code,
                    'value': postal_code
                })
        fields.append({
                    'custom_field_definition_id': self.cp_project_github_repo,
                    'value': repo
                })
                
        custom_fields = fields

        data['custom_fields'] = custom_fields

        url = f'{self.cp_base_url}{self.cp_projects_fragment}'
        r = requests.post(url, headers=self.GetHeaders(), data=json.dumps(data))
        if r.ok:
            project = json.loads(r.text)
            pid = project['id']

            for email in emails:
                sr = self.FindPersonByEmail(email)
                people = json.loads(sr)
                if len(people) > 0:
                    person_id = people[0]['id']
                else: 
                    person_id = self.CreatePerson(email)    
                
                if person_id:
                    self.RelateRecord('projects', pid, person_id)


            return r.text
        
        return ''

    def GetCustomFields(self):
        url = f'{self.cp_base_url}{self.cp_custfields_fragment}'
        r = requests.get(url, headers=self.GetHeaders())
        if r.ok:
            return r.text
        
        return ''

    def GetPipeline(self, pipeline_name):
        url = f'{self.cp_base_url}{self.cp_pipeline_fragment}'
        r = requests.get(url, headers=self.GetHeaders())
        
        if r.ok:
            pipelines = json.loads(r.text)
            for pipeline in pipelines:
                if pipeline['name'] == pipeline_name:
                    return pipeline
            
        
        return None

    def CreateOWASPMembership(self, stripe_id, name, email, subscription_data):
        # Multiple steps here
        # CreatePerson
        # CreateOpportunity
        contact_json = self.FindPersonByEmail(email)
        person = None
        pid = None
        if contact_json != '' and contact_json !='[]':
            person = json.loads(contact_json)
            if len(person) > 0:
                person = person[0]
                pid = person['id']
        
        if pid == None or pid <= 0:
            pid = self.CreatePerson(name, email, subscription_data, stripe_id)
        else: #should only update if sub data membership end is later or nonexistent (and not a lifetime member)
            memtype = self.GetCustomFieldHelper(self.cp_person_membership, person['custom_fields'])
            if memtype == None:
                self.UpdatePerson(pid, subscription_data, stripe_id)
            elif memtype != self.cp_person_membership_option_lifetime:
                mend = self.GetDatetimeHelper(subscription_data['membership_end'])
                cp_mend = self.GetCustomFieldHelper(self.cp_person_membership_end, person['custom_fields'])
                if mend == None or cp_mend == None or mend > datetime.fromtimestamp(cp_mend):
                    self.UpdatePerson(pid, subscription_data, stripe_id)

        if pid == None or pid <= 0:
            logging.error(f'Failed to create person for {email}')
            return

        opp_name = subscription_data['membership_type'].capitalize()
        if opp_name == 'Honorary':
            opp_name = "Complimentary One"
        if subscription_data['membership_type'] != 'lifetime':
            opp_name += f" Year Membership until {subscription_data['membership_end']}"
        else:
            opp_name += " Membership"
        
        time.sleep(7.0) # seems to take copper a little while after a person is created for the relation to be able to see it

        self.CreateMemberOpportunity(opp_name, pid, subscription_data)