import requests
import io
import base64
import os
import json

class OWASPYM():
    base_url = os.environ['YM_APIENDPOINT']
    auth_url = "/Ams/Authenticate"
    group_url = "/Ams/:ClientID/Groups"
    grouptype_url = "/Ams/:ClientID/GroupTypes"
    session_id = None

    #Group Options
    GROUP_ACCESSIBILITY_PRIVATE = 0
    GROUP_ACCESSIBILITY_OPEN = 1
    GROUP_ACCESSIBILITY_PUBLIC = 2
    GROUP_MEMBERSHIP_ALLOW_ANY = 0
    GROUP_MEMBERSHIP_BY_REQUEST = 1
    GROUP_MEMBERSHIP_ADMINONLY = 2
    GROUP_MESSAGING_DISABLE = 0
    GROUP_MESSAGING_ADMIN = 1
    GROUP_MESSAGING_MEMBERS = 2
    GROUP_EMAIL_ADMIN_DISABLE = 0
    GROUP_EMAIL_ADMIN_APPROVAL = 1
    GROUP_EMAIL_ADMIN_AUTOAPPROVE = 2
    GROUP_EMAIL_MEMBER_DISABLE = 0
    GROUP_EMAIL_MEMBER_ADMIN_APPROVAL = 1
    GROUP_EMAIL_MEMBER_AUTOAPPROVE = 2
    
    #GroupType Options
    GROUP_TYPE_CHAPTER = 30273
    GROUP_TYPE_COMMITTEE = 30274
    
    def GetHeaders(self):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",          
        }

        if self.session_id is not None:
            headers["x-ss-id"] = self.session_id

        return headers

    def Login(self):
        success = False
        self.session_id = None
        url = self.base_url + self.auth_url

        data = {
            'ClientID': os.environ['YM_CLIENTID'],
            'UserType': 'Admin',
            'Username': os.environ['YM_APIKEY'],
            'Password': os.environ['YM_APIPW']            
        }

        r = requests.post(url = url, headers=self.GetHeaders(), data=json.dumps(data))
        if r.ok:
            content = json.loads(r.content)
            self.session_id = content['SessionId']
            success = True

        return success

    def GetGroups(self):
        content = []
        url = self.base_url + self.group_url.replace(':ClientID', os.environ['YM_CLIENTID'])
        r = requests.get(url = url, headers=self.GetHeaders())
        if r.ok:
            content = json.loads(r.content)
        
        return content

    def GetGroupTypes(self):
        content = []
        url = self.base_url + self.grouptype_url.replace(':ClientID', os.environ['YM_CLIENTID'])
        r = requests.get(url = url, headers=self.GetHeaders())
        if r.ok:
            content = json.loads(r.content)
        
        return content

    def CreateGroup(self, typeID, name, shortDesc, content):
        content = []
        url = self.base_url + self.group_url.replace(':ClientID', os.environ['YM_CLIENTID'])
        data = {
            'TypeID': typeID,
            'Name': name,
            'ShortDescription': shortDesc,
            'WelcomeContent': content,
            'GroupCode': name.replace(' ','_').lower(),
            'Active': True,
            'Hidden': False,
            'Accessibility': self.GROUP_ACCESSIBILITY_PUBLIC,    
            'Membership': self.GROUP_MEMBERSHIP_ALLOW_ANY,
            'Messaging': self.GROUP_MESSAGING_MEMBERS,
            'SendNewsletter': False,
            'EnableFeed': True,
            'AdminCanExportMembers': False,
            'PhotoApproval': True,
            'EmailOptionsAdmin': self.GROUP_EMAIL_ADMIN_AUTOAPPROVE,
            'EmailOptionsMember': self.GROUP_EMAIL_MEMBER_AUTOAPPROVE
        }

        r = requests.post(url = url, headers=self.GetHeaders(), data=json.dumps(data))
        if r.ok:
            content = json.loads(r.content)
            return content
        elif r.content is not None:
            content = json.loads(r.content)
            if 'ResponseStatus' in content and 'Message' in content['ResponseStatus'] and 'timeout' in content['ResponseStatus']['Message'].lower():
                raise OWASPYMSessionTimeoutException('Session Timeout')


class OWASPYMException(Exception):
    __module__ = Exception.__module__

class OWASPYMLoginException(OWASPYMException):
    pass

class OWASPYMSessionTimeoutException(OWASPYMException):
    pass