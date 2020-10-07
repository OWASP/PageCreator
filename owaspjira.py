import requests
import io
import base64
import os
import json

class OWASPJira():
    base_url = "https://owasporg.atlassian.net/rest/servicedeskapi/servicedesk/"
    osd_id = "4"
    nfrsd_id = "7"
    chapter_preapproval_id = "75"
    
    def GetHeaders(self):

        authstr = os.environ['JIRA_USER'] + ":" + os.environ['JIRA_API_TOKEN']
        headers = {
             "Authorization" : "Basic " + base64.b64encode(authstr.encode()).decode(),
            "X-ExperimentalApi" : "true"
        }
        return headers

    def GetServiceDesks(self):
        url = self.base_url
        headers = self.GetHeaders()

        r = requests.get(url = url, headers=headers)
        return r

    def CreateDropDownField(self): #, field_name, field_desc, options):
        field_to_create = {
                            "name":"Test Chapter Dropdown",
                            "description":"A dropdown of existing chapters",
                            "validValues":[{"label":"Chapter One","children":[]},
                                           {"label":"Chapter Two","children":[]},
                                           {"label":"Chapter Three","children":[]},
                                           {"label":"Chapter Four","children":[]},
                                           {"label":"Chapter Five","children":[]}],
                            "jiraSchema":{"type":"option","custom":"com.atlassian.jira.plugin.system.customfieldtypes:select",
                            }}

        field_url = f"{self.base_url}{self.nfrsd_id}/requesttype/{self.chapter_preapproval_id}/field"
        r = requests.post(url=field_url, headers=self.GetHeaders(), data=json.dumps(field_to_create))

        return r