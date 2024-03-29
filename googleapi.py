import os.path
from googleapiclient.discovery import build
from google.oauth2 import service_account
#from oauth2client.service_account import ServiceAccountCredentials
from httplib2 import http
import json

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from httplib2 import http
import json
from datetime import datetime
import random
from copper import OWASPCopper
import time
import random 
from requests.exceptions import HTTPError
import socket

class OWASPGoogle:
    def __init__(self):
        #socket.setdefaulttimeout(10)
        scopes = ['https://www.googleapis.com/auth/admin.directory.user', 'https://www.googleapis.com/auth/admin.directory.group', 'https://www.googleapis.com/auth/apps.groups.settings', 'https://www.googleapis.com/auth/admin.directory.userschema']
        client_secret = json.loads(os.environ['GOOGLE_CREDENTIALS'], strict=False)
        creds = service_account.Credentials.from_service_account_info(client_secret, scopes=scopes)
        creds = creds.with_subject(os.environ['GOOGLE_ADMIN'])

        self.admin = build('admin', 'directory_v1', credentials=creds, cache_discovery=False)
        self.groupSettings = build('groupssettings', 'v1', credentials=creds, cache_discovery=False)
      
    def UpdateUserData(self, email_address, membership_data):
        cp = OWASPCopper()
        user = {
            "customSchemas": {
                "OWASP_Membership":{
                    "membership_type": membership_data['membership_type'],
                    "membership_start": membership_data['membership_start'],
                    "membership_end": membership_data['membership_end'],
                    "membership_recurring": membership_data['membership_recurring']
                }
            }
        }

        result = f"User {email_address} updated."
        results = self.admin.users().update(userKey=email_address, body = user).execute()
        if 'primaryEmail' not in results:
            result = f"Failed to update User {email_address}."
        return result

    def GetUserFiles(self, email_address):
        items = {}
        scopes = ['https://www.googleapis.com/auth/admin.directory.user', 'https://www.googleapis.com/auth/admin.directory.group', 'https://www.googleapis.com/auth/apps.groups.settings', 'https://www.googleapis.com/auth/admin.directory.userschema', 'https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/drive.photos.readonly']
        client_secret = json.loads(os.environ['GOOGLE_CREDENTIALS'], strict=False)
        creds = service_account.Credentials.from_service_account_info(client_secret, scopes=scopes)
        creds = creds.with_subject(email_address)
        self.drive = build('drive', 'v3', credentials=creds)
        results = self.drive.files().list(pageSize=100, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        return items

    def CreateSpecificEmailAddress(self, altemail, first, last, email_address, fail_if_exists=True):
        
        user = {
            "name": {
                "familyName": last,
                "givenName": first
            },
            "primaryEmail": email_address,
            "recoveryEmail": altemail,
            "password": datetime.now().strftime('%m%d%Y'),
            "emails": [{
                    "address": altemail,
                    "type": "home",
                    "customType": "",
                    "primary": False
                },
                {
                    "address": email_address,
                    "type": "home",
                    "customType": "",
                    "primary": True
                }
            ]
        }
        
        if fail_if_exists:
            results = self.admin.users().list(domain='owasp.org', query=f"email={user['primaryEmail']}").execute()
            if 'users' in results and len(results['users']) > 0:
                return f"User {user['primaryEmail']} already exists."

        result = f"User {user['primaryEmail']} created"
        results = self.admin.users().insert(body = user).execute()
        if 'primaryEmail' not in results:
            result = f"Failed to create User {user['primaryEmail']}."
        return result
        
    def CreateEmailAddress(self, altemail, first, last, fail_if_exists=True):
        user = {
            "name": {
                "familyName": last,
                "givenName": first,
                "fullName": first + ' ' + last
            },
            "primaryEmail": first + '.' + last + '@owasp.org',
            "recoveryEmail": altemail,
            "password": "@123OWASP123@",
        }
        
        if fail_if_exists:
            results = self.admin.users().list(domain='owasp.org', query=f"email={user['primaryEmail']}").execute()
            if 'users' in results and len(results['users']) > 0:
                return f"User {user['primaryEmail']} already exists."

        result = f"User {user['primaryEmail']} created"
        results = self.admin.users().insert(body = user).execute()
        if 'primaryEmail' not in results:
            result = f"Failed to create User {user['primaryEmail']}."

        return result

    def GetActiveUsers(self, next_page_token):
        done = False
        while not done:
            try:
                results = results = self.admin.users().list(domain='owasp.org', query='isSuspended=false', pageToken=next_page_token).execute()
                if 'users' in results and len(results['users']) > 0:
                    return results
                else:
                    done = True
            except HTTPError as e:
                print('error waiting 8 to 10 seconds....')
                done = (e.status != 503)
                if not done:
                    dropoff = 4 + random.randint(1, 4)
                    time.sleep(dropoff * 1.25)
                pass

        return { 'users':[] }

    def GetAllUsers(self, email, showDeleted=False): # Gets all users with a specified email address
        done = False
        while not done:
            try:
                results = self.admin.users().list(domain='owasp.org', query=f'email:{email}', showDeleted=showDeleted).execute()
                if 'users' in results and len(results['users']) > 0:
                    return results['users']
                else:
                    done = True
            except HTTPError as e:
                print('error waiting 8 to 10 seconds....')
                done = (e.status != 503)
                if not done:
                    dropoff = 4 + random.randint(1, 4)
                    time.sleep(dropoff * 1.25)
                pass

        return []

    def GetUser(self, cid, showDeleted=False):
        done = False
        while not done:
            try:
                results = self.admin.users().list(domain="owasp.org", query=f"email:{cid}", showDeleted=showDeleted).execute()
                if 'users' in results and len(results['users']) > 0:
                    return results['users'][0]
                else:
                    done = True
            except HttpError as e:
                print('error waiting 8 to 10 seconds....')
                done = (e.status_code != 503)
                if not done:
                    dropoff = 4 + random.randint(1, 4)
                    time.sleep(dropoff * 1.25)
                pass
            except Exception as err:
                done = True

        return None        

    def GetPossibleEmailAddresses(self, preferred_email):
        emails = []
        results = self.admin.users().list(domain='owasp.org', query=f"email={preferred_email}").execute()
        if 'users' in results and len(results['users']) > 0:
            # come up with alternates...
            random.seed()
            alternate = preferred_email[0:preferred_email.find('@'):] + f'{random.randint(1, 99)}' + preferred_email[preferred_email.find('@'):]
            results = self.admin.users().list(domain='owasp.org', query=f"email={alternate}").execute()
            if not 'users' in results:
                emails.append(alternate)
            alternate = preferred_email[0:preferred_email.find('@'):] + datetime.now().strftime("%d%m") + preferred_email[preferred_email.find('@'):]
            results = self.admin.users().list(domain='owasp.org', query=f"email={alternate}").execute()
            if not 'users' in results:
                emails.append(alternate)
            alternate = preferred_email[0:preferred_email.find('@'):] + datetime.now().strftime("%Y%m") + preferred_email[preferred_email.find('@'):]
            results = self.admin.users().list(domain='owasp.org', query=f"email={alternate}").execute()
            if not 'users' in results:
                emails.append(alternate)
            alternate = preferred_email[0] + '.' + preferred_email[preferred_email.find('.')+1:]

            results = self.admin.users().list(domain='owasp.org', query=f"email={alternate}").execute()
            if not 'users' in results:
                emails.append(alternate)
            
            if len(emails) == 0:
                emails.append('Could not find a suitable alternate email.  Please submit a ticket at https://contact.owasp.org')
                
        else: # email not in list, just give that one
            emails.append(preferred_email)

        return emails


    def FindGroup(self, group_name):
        # test if group exists...
        try:
            results = self.admin.groups().get(groupKey=group_name).execute()
            if 'name' in results:
                return results
        except:
            pass
        
        return None

    def GetGroupSettings(self, group_name):
        val = ''
        try:
            val = self.groupSettings.groups().get(groupUniqueId=group_name).execute()
        except:
            pass

        return val

    def SetGroupSettings(self, group_name, group_settings):
        val = ''
        try:
            val = self.groupSettings.groups().update(groupUniqueId=group_name, body=group_settings).execute()
        except:
            pass

        return val

    def GetGroupMembers(self, group_name):
        val = ''
        try:
            val = self.admin.members().list(groupKey=group_name).execute()
        except:
            pass

        return val

    def GetGroupMembersAsObj(self, group_name):
        members = []
        try:
            val = self.admin.members().list(groupKey=group_name).execute()
            if 'members'in val:
                members.extend(val['members'])
                if 'nextPageToken' in val:
                    pageToken = val['nextPageToken']
                    while pageToken != None:
                        val = self.admin.members().list(groupKey=group_name, pageToken=pageToken).execute()
                        if 'members' in val:
                            members.extend(val['members'])
                            pageToken = val['nextPageToken']
                        else:
                            pageTaken = None
        except:
            pass

        return members

    def AddMemberToGroup(self, group_name, email, role='MANAGER', member_type='USER'):
        data = { 'email': email, 'role': role, 'type':member_type }
        val = ''
        try:
            val = self.admin.members().insert(groupKey=group_name, body=data).execute()
        except:
            pass

        return val

    def RemoveFromGroup(self, group_name, email):
        val = ''
        try:
            val = self.admin.members().delete(groupKey=group_name, memberKey=email).execute()
        except:
            pass

        return val        

    def GetInitialGroupSettings(self, admin_only):
        gs = {  'whoCanJoin': 'INVITED_CAN_JOIN', 
                'whoCanViewMembership': 'ALL_IN_DOMAIN_CAN_VIEW', 
                'whoCanViewGroup': 'ALL_MEMBERS_CAN_VIEW', 
                'whoCanInvite': 'ALL_OWNERS_CAN_INVITE', 
                'whoCanAdd': 'ALL_OWNERS_CAN_ADD', 
                'allowExternalMembers': 'true', 
                'whoCanPostMessage': 'ANYONE_CAN_POST', 
                'allowWebPosting': 'true' } 
                
        if admin_only:
            gs['whoCanViewMembership'] = 'ALL_MANAGERS_CAN_VIEW'
            gs['whoCanPostMessage'] = 'ALL_MEMBERS_CAN_POST'
            
        return gs
    
    def CreateGroup(self, group_name, admin_only=False):
        group = {
            "adminCreated": True,
            "description": "Group Created by Automation",
            "email": group_name,
            "kind": "admin#directory#group",
            "name": "Leader Group For " + group_name
        }

        result = f"Group {group['email']} created"
        results = ''
        try:
            results = self.admin.groups().insert(body = group).execute()
        except:
            pass

        if 'name' not in results:
            result = f"Failed to create Group {group['email']}."
        else:
            self.SetGroupSettings(group_name, self.GetInitialGroupSettings(admin_only))

        return result

    def SuspendUser(self, email): #suspend the user with email retrieved possibly from GetUser, for instance
            user = self.GetUser(email)
            if user:
                user['suspended'] = True

            results = self.admin.users().update(userKey=email, body=user).execute()

            return ('primaryEmail' in results)

    def UnsuspendUser(self, email): #suspend the user with email retrieved possibly from GetUser, for instance
        user = self.GetUser(email)
        if user:
            user['suspended'] = False

        results = self.admin.users().update(userKey=email, body= user).execute()

        return ('primaryEmail' in results)
    
    def DeleteUserById(self, user):
        results = None
        if user and user['suspended']:
            results = self.admin.users().delete(userKey=user["id"]).execute()
            results = True

        return results
    
    def DeleteUser(self, email): #suspend the user with email retrieved possibly from GetUser, for instance
        user = self.GetUser(email)
        results = None
        if user:
            results = self.admin.users().delete(userKey=user['id']).execute()
            results = True

        return results