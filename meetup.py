import requests
import json
import base64
from pathlib import Path
import os
from datetime import datetime, timedelta
import jwt
from jwt import algorithms
import cryptography
import urllib
from cryptography.hazmat.primitives import serialization

class OWASPMeetup:
    meetup_api_url = "https://api.meetup.com"
    meetup_gql_url = "https://api.meetup.com/gql"
    access_token = '42e61f8bca8abaa0323fada6203352b1'
    refresh_token = ''
    oauth_token = ''
    oauth_token_secret = ''

    def GetHeaders(self):
        headers = {
            'Content-Type': 'application/json'
        }

        return headers

    def RefreshToken(self):
        headers = {
            'Accept': 'application/json',
            'X-OAuth-Scopes': 'event_management, basic, group_content_edit'
        }
        
        login_url  = f"https://secure.meetup.com/oauth2/access?client_id={os.environ['MU_CONSUMER_KEY']}&client_secret={os.environ['MU_SECRET']}&code={auth_code}&redirect_uri={os.environ['MU_REDIRECT_URI']}&grant_type=refresh_token"
        res = requests.post(login_url, headers=headers)
        json_res = json.loads(res.text)
        self.access_token = json_res['access_token']
        self.refresh_token = json_res['refresh_token']


    def Login(self):
        payload = {
          "sub":os.environ['MU_USER_ID'],
          "iss":os.environ['MU_CONSUMER_KEY'],
          "aud":"api.meetup.com",
          "exp":"120"
        }
        jwtheaders = {"kid":os.environ['MU_KEY_ID'],
                      "alg":"RS256"}

        keystr = os.environ["MU_RSA_KEY"]
        key = serialization.load_pem_private_key(keystr.encode(), None)
        encoded = jwt.encode(payload=payload, key=keystr, algorithm='RS256', headers=jwtheaders)

        #login_url = f"https://secure.meetup.com/oauth2/authorize?client_id={os.environ['MU_CONSUMER_KEY']}&redirect_uri={os.environ['MU_REDIRECT_URI']}&response_type=anonymous_code&scope=basic+event_management+group_content_edit"
        #login_url = f"https://secure.meetup.com/oauth2/authorize?client_id={os.environ['MU_CONSUMER_KEY']}&redirect_uri={os.environ['MU_REDIRECT_URI']}&response_type=code"
        headers = {
            'Accept': 'application/x-www-form-url-encoded',
            'X-OAuth-Scopes': 'event_management, basic, group_content_edit'
        }

        #res = requests.post(login_url, headers=headers)
        #result = False
        #if '"code":' in res.text:
        try:
            #json_res = json.loads(res.text)
            #auth_code = json_res['code']
            #login_url  = f"https://secure.meetup.com/oauth2/access?client_id={os.environ['MU_CONSUMER_KEY']}&client_secret={os.environ['MU_SECRET']}&code={auth_code}&redirect_uri={os.environ['MU_REDIRECT_URI']}&grant_type=authorization_code"
            login_url = f"https://secure.meetup.com/oauth2/access" # https://secure.meetup.com/oauth2/access
            urldata = {
                 "grant_type" : "urn:ietf:params:oauth:grant-type:jwt-bearer",
                 "assertion" : encoded
             }
             #grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer
             #&assertion={SIGNED_JWT}
            urle = urllib.parse.urlencode(urldata)
            res = requests.post(login_url, headers=headers, data=urldata)
            print(res.text)
            json_res = json.loads(res.text)
            self.access_token = json_res['access_token']
            self.refresh_token = json_res['refresh_token']

            #this login no longer works....
            # headers = {
            #     'Accept': 'application/json',
            #     'Authorization': f'Bearer {self.access_token}'
            # }
            # login_url = f"https://api.meetup.com/sessions?email={os.environ['MU_USER_NAME']}&password={os.environ['MU_USER_PW']}"
            # res = requests.post(login_url, headers=headers)
            # json_res = json.loads(res.text)
            # self.oauth_token = json_res['oauth_token']
            # self.oauth_token_secret = json_res['oauth_token_secret']
            result = True

        except:
            result = False

        return result

    def GetGroupIdFromGroupname(self, groupname):
        headers = self.GetHeaders()
        querystr = "query {"
        querystr += " groupByUrlname(urlname: \"" + groupname + "\")"
        querystr += "{ id }"
        querystr += "}"

        query_data = {
            "query": querystr
        }
        
        res = requests.post(self.meetup_gql_url, headers=headers, data=json.dumps(query_data))
        id = ""
        if res.ok:
            jgroup = json.loads(res.text)
            if jgroup['data']['groupByUrlname']:
                id = jgroup['data']['groupByUrlname']['id']
        return id


    def GetGroupEvents(self, groupname, earliest='', status=''):
        headers = self.GetHeaders()

        id = self.GetGroupIdFromGroupname(groupname)
        if not status:
            status = "UPCOMING"
        datemax = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        datemin = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        if earliest:
            datemin = earliest #here, we are assuming an ISO 8601 format date

        query = "query { proNetworkByUrlname(urlname: \"OWASP\") {"
        query += "eventsSearch(filter: { status: :STATUS groups: [ \":GROUPID\" ] "
        query += f"eventDateMin: \"{datemin}\" eventDateMax: \"{datemax}\"" 
        query += "  }, input: { first: 100 }) {"
        query += " count pageInfo { endCursor } edges { node { id title eventUrl dateTime timezone description }}}}}"
        query = query.replace(":GROUPID",id).replace(":STATUS", status.upper())
        query_data = {
            "query": query
        }
        res = requests.post(self.meetup_gql_url, headers=headers, data=json.dumps(query_data))
        
        json_res = ''
        if res.ok:
            json_res = res.text

        return json_res
