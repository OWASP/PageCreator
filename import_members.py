from github import OWASPGitHub
from copper import OWASPCopper
import logging
import os
import requests
import json
import base64
import pathlib
import urllib
import gspread
import stripe
from datetime import datetime
from datetime import timedelta
import csv
from owaspmailchimp import OWASPMailchimp

class MemberData:
    def __init__(self, name, email, company, country, postal_code, start, end, type, recurring):
        self.name = name
        names = self.name.split(' ')
        self.first = ''
        self.last = ''
        for name in names:
            if not self.first:
                self.first = name
            else:
                self.last = self.last + name + ' '
        
        self.last = self.last.strip()

        copper = OWASPCopper()

        self.email = email
        self.company = company
        self.country = country
        self.postal_code = postal_code
    
        if end:
            self.end = copper.GetDatetimeHelper(end)
        else:
            self.end = None

        self.start = None
        self.tags = []
        
        customers = stripe.Customer.list(email=email)
        if len(customers.data) > 0:
            customer = customers.data[0]
            cmetadata = customer.get('metadata', None)
            if cmetadata:
                memstart = cmetadata.get('membership_start', None)
                if memstart:
                    start = memstart # don't change a start date

        
        if start:
            self.start = copper.GetDatetimeHelper(start)
        
            
        self.type = type
        self.recurring = recurring
        self.stripe_id = None
    def UpdateMetadata(self, customer_id, metadata):
        self.stripe_id = customer_id
        stripe.Customer.modify(
                            customer_id,
                            metadata=metadata
                        )

    def AddTags(self, tags):
        self.tags = tags

    def CreateCustomer(self):
        mdata = self.GetSubscriptionData()
        for tag in self.tags:
            mdata[tag] = True

        cust = stripe.Customer.create(email=self.email, 
                                       name=self.name,
                                       metadata = mdata)
        
        
        self.stripe_id = cust.get('id')
        return self.stripe_id

    def GetSubscriptionData(self):
        mstart = None
        mend = None
        if self.start:
            mstart = datetime.strftime(self.start, '%m/%d/%Y')
        if self.end:
            mend = datetime.strftime(self.end, '%m/%d/%Y')
        metadata = {
                    'membership_type':self.type,
                    'membership_start':mstart,
                    'membership_end':mend,
                    'membership_recurring':self.recurring,
                    'company':self.company,
                    'country':self.country
                }
        for tag in self.tags:
            metadata[tag] = True

        return metadata

# Import Members
def import_members(filename, override_lifetime_add_tags=False):
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        stripe.api_key = os.environ['STRIPE_SECRET']
        cop = OWASPCopper()
                    
        for row in reader:
            nstr = f"{row['First Name']} {row['Last Name']}".strip()
            member = MemberData(nstr, row['Email'].lower(), row['Company'], row['Work Country'], row['Work Zip'], row['membership-start-date'], row['membership-end-date'], row['membership-type'], row['membership-recurring'])
            customers = stripe.Customer.list(email=member.email)
            stripe_id = None
            tags = row['tags'].split(',') # for stripe purposes these 'tags' are simply true if they exist (for instance, distinguished: true will be the result)
            member.AddTags(tags)
            if len(customers.data) > 0: # exists
                customer_id = customers.data[0].get('id', None)
                metadata = customers.data[0].get('metadata', {})
                stripe_member_type = metadata.get('membership_type')
                if stripe_member_type == 'lifetime' and not override_lifetime_add_tags: #do not update the membership on this person unless told to override
                    continue

                membership_type = member.type
                memberdata = member.GetSubscriptionData()
                memop = cop.FindMemberOpportunity(member.email)
                if memop != None:
                    persons = cop.FindPersonByEmail(member.email)
                    if persons:
                        person = json.loads(persons)[0]
                        cpstart = cop.GetCustomFieldHelper(cop.cp_person_membership_start, person['custom_fields'])
                        current_start = datetime.fromtimestamp(cpstart)
                        memberdata['membership_start'] = current_start.strftime('%m/%d/%Y')

                if membership_type and membership_type != 'lifetime': 
                    mendstr = metadata.get('membership_end', None) # current membership end say 8/1/2022
                    if mendstr != None:
                        mend_dt = datetime.strptime(mendstr, '%m/%d/%Y')
                        #possible case: has membership already...update end date to be +time
                        # This needs to be re-evaluated....
                        if membership_type != 'two':
                            add_days = 365
                        else: 
                            add_days = 730
                        member.end = mend_dt + timedelta(days=add_days)
                        memberdata['membership_end'] = member.end.strftime('%m/%d/%Y')

                        member.UpdateMetadata(customer_id,
                            memberdata
                        )
                else: #lifetime
                    memberdata['membership_end'] = ''
                    member.UpdateMetadata(customer_id,
                            memberdata
                        )

                # also need to update Copper info here...including creating an opportunity for this (even if $0)
                stripe_id = customer_id #cop.UpdateOWASPMembership(member.stripe_id, member.name, member.email, member.GetSubscriptionData())
            else: # does not exist
                stripe_id = member.CreateCustomer()
            
            if stripe_id != None:
                sub_data = member.GetSubscriptionData()
                if sub_data['membership_type'] != 'lifetime' and sub_data.get('membership_end', None) == None:
                    sub_data['membership_end'] = '2000-01-01' # faking this data so we can look it up later and fix it

                cop.CreateOWASPMembership(stripe_id, member.name, member.email, sub_data, tags)
                mailchimp = OWASPMailchimp()
                mailchimpdata = {
                    'name': member.name,
                    'first_name': member.first,
                    'last_name': member.last,
                    'source': 'script import',    
                    'purchase_type': 'membership',
                    'company': member.company,
                    'country': member.country,
                    'postal_code': member.postal_code,
                    'mailing_list': 'True'                    ''
                }
                for tag in tags:
                    if tag == 'distinguished':
                        mailchimpdata['status'] = 'distinguished'

                mailchimp.AddToMailingList(member.email, mailchimpdata , member.GetSubscriptionData(), stripe_id)

            print(member.email + ' completed.')