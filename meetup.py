import requests
import json
import base64
from pathlib import Path
import os

class OWASPMeetup:
    meetup_api_url = "https://api.meetup.com"
    
    def Login(self):
        login_url  = f"https://secure.meetup.com/oauth2/authorize?client_id={os.environ['MU_CONSUMER_KEY']}&redirect_uri={os.environ['MU_REDIRECT_URI']}&response_type=anonymous_code"
        