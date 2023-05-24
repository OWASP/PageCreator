from stripe.api_resources import payment_intent
import requests
import json
from github import *
import random
import time
import unicodedata
import hashlib
import base64
import datetime
import re
import gspread
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import io
from datetime import datetime
from datetime import timedelta
import csv
from googleapi import OWASPGoogle
from googleapiclient.http import MediaIoBaseDownload
import helperfuncs
from datetime import datetime, timedelta



def delete_suspended_users():
    do_not_delete = ["sarah.baso@owasp.org", "samantha.groves@owasp.org", "laura.grau@owasp.org","noreen.whysel@owasp.org","paul.ritchie@owasp.org",
                     "tiffany.long@owasp.org","claudia.aviles-casanova@owasp.org","kate.hartmann@owasp.org","alison.shrader@owasp.org","alison.mcnamee@owasp.org",
                     "matt.tesauro@owaspfoundation.org","matt.tesauro@owasp.com","karen.staley@owasp.org","mike.mccamon@owasp.org","mike.mccamon@owaspfoundation.org",
                     "mike.mccamon@owasp.com", "accountant@owasp.org"]

    cfile = "suspended_users_3.28.2023.csv"
    goog = OWASPGoogle()
    fields = []
    saverows = []

    with open(cfile, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        fields = reader.fieldnames
        for row in reader:
            if row['email'] in do_not_delete:
                continue
            if goog.DeleteUser(row['email']):
                row['deleted'] = "DELETED"
                saverows.append(row)
            else:
                row['deleted'] = "NOT DELETED"
                saverows.append(row)
                
    os.remove(cfile)

    with open(cfile, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = fields)
        writer.writeheader()
        writer.writerows(saverows)

    print('done')

delete_suspended_users()