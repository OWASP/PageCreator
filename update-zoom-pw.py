import sys
import os
from googleapi import OWASPGoogle
import helperfuncs
import sendgrid
from sendgrid.helpers.mail import *

def mail_results(user_email):
    #user_email = 'harold.blankenship@owasp.com'
    subject = 'Credential for your zoom access'
    msg = f"To access your chapter zoom account, use the provided account name and this following password: {os.environ['leaders_zoom_two_pass']}"

    from_email = From('noreply@owasp.org', 'OWASP')
    to_email = To(user_email)
    content = Content("text/plain", msg)
    message = Mail(from_email, to_email, subject, content)

    try:
        sgClient = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sgClient.client.mail.send.post(request_body=message.get())
        print(response)
        return True
    except Exception as ex:
        template = "An exception of type {0} occurred while sending an email. Arguments:\n{1!r}"
        err = template.format(type(ex).__name__, ex.args)
        print(err)

    return False

def reshare_zoom_credentials(zoom_account):
    og = OWASPGoogle()
    result = og.GetGroupMembers(zoom_account)
    for group in result['members']:
        inner = og.GetGroupMembers(group['email'])
        for member in inner['members']:
            mail_results(member['email'])
        
    #print(helperfuncs.send_onetime_secret(emails, zoom_pw))
 
def main():
    reshare_zoom_credentials('leaders-zoom-two@owasp.org')
    #print(helperfuncs.send_onetime_secret(['harold.blankenship@owasp.com'], os.environ['leaders_zoom_two_pass']))

if __name__ == "__main__":
    main()


