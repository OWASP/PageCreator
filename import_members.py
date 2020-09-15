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

class MemberData:
    def __init__(self, name, email, company, country, start, end, type, recurring):
        self.name = name
        self.email = email
        self.company = company
        self.country = country
        self.start = datetime.strptime(start, "%Y-%m-%d")
        self.end = datetime.strptime(end, "%Y-%m-%d")
        self.type = type
        self.recurring = recurring
        self.stripe_id = None
    def UpdateMetadata(self, customer_id, metadata):
        self.stripe_id = customer_id
        stripe.Customer.modify(
                            customer_id,
                            metadata=metadata
                        )
    def CreateCustomer(self):
        cust = stripe.Customer.create(email=self.email, 
                                       name=self.name,
                                       metadata = {
                                           'membership_type':self.type,
                                           'membership_start':datetime.strftime(self.start, '%m/%d/%Y'),
                                           'membership_end':datetime.strftime(self.end, '%m/%d/%Y'),
                                           'membership_recurring':self.recurring,
                                           'company':self.company,
                                           'country':self.country
                                       })
        
        
        self.stripe_id = cust.get('id')
        return self.stripe_id

    def GetSubscriptionData(self):
        metadata = {
                    'membership_type':self.type,
                    'membership_start':datetime.strftime(self.start, '%Y-%m-%d'),
                    'membership_end':datetime.strftime(self.end, '%Y-%m-%d'),
                    'membership_recurring':self.recurring,
                    'company':self.company,
                    'country':self.country
                }
        return metadata

# Import Members, assumption this is complimentary members
def import_members(filename):
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        stripe.api_key = os.environ['STRIPE_SECRET']
        cop = OWASPCopper()
                    
        for row in reader:
            nstr = f"{row['First Name']} {row['Last Name']}".strip()
            member = MemberData(nstr, row['Email'], row['Company'], row['Work Country'], row['membership-start-date'], row['membership-end-date'], row['membership-type'], row['membership-recurring'])
            customers = stripe.Customer.list(email=member.email)
            stripe_id = None
            
            if len(customers.data) > 0: # exists
                customer_id = customers.data[0].get('id', None)
                metadata = customers.data[0].get('metadata', {})
                stripe_member_type = metadata.get('membership_type')
                if stripe_member_type == 'lifetime': #do not update the membership on this person
                    continue

                membership_type = member.type
                if membership_type and membership_type != 'lifetime':
                    mendstr = metadata.get('membership_end', None)
                    if mendstr != None:
                        mend_dt = datetime.strptime(mendstr, '%m/%d/%Y')
                        #possible case: member got complimentary AND has membership already...update end date to be +time
                        if member.end > mend_dt:
                            add_days = 365
                            if membership_type == 'two':
                                add_days = 730
                            member.end = mend_dt + timedelta(days=add_days)

                        member.UpdateMetadata(customer_id,
                            {
                                "membership_end": member.end.strftime('%m/%d/%Y')
                            }
                        )
                else: #lifetime
                    member.UpdateMetadata(customer_id,
                            {
                                "membership_end": "",
                                "membership_type": "lifetime"
                            }
                        )

                # also need to update Copper info here...including creating an opportunity for this (even if $0)
                stripe_id = customer_id #cop.UpdateOWASPMembership(member.stripe_id, member.name, member.email, member.GetSubscriptionData())
            else: # does not exist
                stripe_id = member.CreateCustomer()
            
            if stripe_id != None:
                cop.CreateOWASPMembership(stripe_id, member.name, member.email, member.GetSubscriptionData())
          