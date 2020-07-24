import requests
import json
import base64
from pathlib import Path
import os
import logging

class OWASPWufoo:
    apitoken = os.environ["WF_APIKEY"]
    baseurl = "https://owasp.wufoo.com/api/v3/forms/"

    OPERATOR_CONTAINS = 'Contains'
    OPERATOR_NOT_CONTAINS = 'Does_not_contain'
    OPERATOR_BEGINS_WITH = 'Begins_with'
    OPERATOR_ENDS_WITH = 'Ends_with'
    OPERATOR_LESS_THAN = 'Is_less_than'
    OPERATOR_GREATER_THAN = 'Is_greater_than'
    OPERATOR_ON = 'Is_on' 
    OPERATOR_BEFORE = 'Is_before'
    OPERATOR_AFTER = 'Is_after'
    OPERATOR_NOT_EQUAL = "Is_not_equal_to"
    OPERATOR_EQUAL = 'Is_equal_to'
    OPERATOR_EXISTS = 'Is_not_NULL'

    def GetFieldFromFormEntry(self, form, entryid, fieldid, operator, param):
        #https://owasp.wufoo.com/api/v3/forms/join-owasp-as-a-student/entries.xml?Filter1=EntryId+Is_equal_to+3
        auth = base64.b64encode(f'{self.apitoken}:{os.environ["WF_APIPASS"]}')
        headers = { 'Authorization': f'Basic { auth }' }
        url = f'{self.baseurl}{form}/entries.json?system=1&Filter1={fieldid}+{operator}+{param}'
        result = ''
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            jsonEntries = json.loads(r.text)
            if len(jsonEntries) > 0:
                jsonEntry = jsonEntries[0]
                result = jsonEntry[fieldid]

        return result
            
        






