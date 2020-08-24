import requests
import json
from github import *
from copper import *
from meetup import *
import gspread
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import time

import base64
import datetime

def add_user_to_repos(gh, gituser, repo_names, name, email):
    success = "ok"
    if gh.FindUser(gituser) != None:
        for repo_name in repo_names:
            # get leaders.md and check to see if leader...
            r = gh.GetFile(repo_name, 'leaders.md')
            if r.ok:
                doc = json.loads(r.text)
                contents = base64.b64decode(doc['content']).decode().lower()
                if name.lower() in contents or email.lower() in contents:
                    if not gh.AddUserToRepo(gituser, repo_name).ok:
                        success = "add failed for one or more repos"
                else:
                    success = 'Not listed as a leader on one or more repos'
            else:
                success = 'could not retrieve leaders file'
    else:
        success = "no such user"

    return success

def add_result_to_sheet(sheet, row, result):
    good_format_dict = {
        "backgroundColor": {
        "red": 0.0,
        "green": 1.0,
        "blue": .5
        }
    }

    bad_format_dict = {
        "backgroundColor": {
        "red": .91,
        "green": .45,
        "blue": .44
        }
    }

    warn_format_dict = {
        "backgroundColor": {
        "red": 1.0,
        "green": .86,
        "blue": .35
        }
    }

    # Colors are wrong somehow...

    done = False
    while not done:
        try:
            sheet.update_cell(row, 12, result)
            done = True
        except gspread.exceptions.APIError:
            time.sleep(100)
            
    dict_to_use = bad_format_dict
    if result == 'ok':
        dict_to_use = good_format_dict
    elif 'no such' in result:
        dict_to_use = warn_format_dict
    done = False
    while not done:
        try:
            sheet.format(f'A{row}:M{row}', dict_to_use)
            done = True
        except gspread.exceptions.APIError:
            time.sleep(100)

def find_repo_for_group(repos, group):
    # hardest part to this...determine which www- repo this group belongs to based on possibly user-input data...  :p
    rname = ''
    group = group.replace('OWASP', '').lower().strip()
    for repo in repos:
        reponame = repo['name'].replace('www-', '').replace('chapter-', '').replace('project-', '').replace('committee-', '').replace('-', ' ').replace('chapter','').replace('project','').replace('committee','')
        if reponame.strip() and (reponame in group or reponame == group):
            rname = repo['name']
            break

    return rname

def get_repo_names(repos, row):
    repo_names = []
    group = row['Select your chapter']
    if group and group != 'Other':
        repo = find_repo_for_group(repos, group)
        if repo:
            repo_names.append(repo)
    group = row['Type your chapter name']
    if group and group != 'Other':
        repo = find_repo_for_group(repos, group)
        if repo:
            repo_names.append(repo)
    group = row['Type your project name']
    if group and group != 'Other':
        repo = find_repo_for_group(repos, group)
        if repo:
            repo_names.append(repo)
    group = row['Select your project']
    if group and group != 'Other':
        repo = find_repo_for_group(repos, group)
        if repo:
            repo_names.append(repo)
        
    return repo_names

def add_users_to_repos():
    gh = OWASPGitHub()
    repos = gh.GetPublicRepositories('www-')

    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    client_secret = json.loads(os.environ['GOOGLE_CREDENTIALS'], strict=False)

    creds = ServiceAccountCredentials.from_json_keyfile_dict(client_secret, scope)
    client = gspread.authorize(creds)
    sheet_key = "1_2XHt_YaDjXCrGM1GoPFwdc6Wf0nfoMa6loyc17cp30"
    sheet = client.open_by_key(sheet_key).get_worksheet(0)
    records = sheet.get_all_records()
    repo_names = []
    row_ndx = 2
    for row in records:
        status = row['Status']
        if not status or status == '' or 'Not listed as a leader' in status:
            gituser = row['Github Username']
            name = row['Name'].strip() + ' ' + row['Last'].strip()
            email = row['Email associated with your chapter or project']
            repo_names = get_repo_names(repos, row)
            success = "no such repo found"
            if len(repo_names) > 0:
                success = add_user_to_repos(gh, gituser, repo_names, name, email)
            
            add_result_to_sheet(sheet, row_ndx, success)
        row_ndx = row_ndx + 1

