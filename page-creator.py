# page-creator
# Tool used for creating chapter and project pages
# for OWASP Community

from stripe.api_resources import payment_intent
from owaspzoom import OWASPZoom
import requests
import json
from github import *
from copper import *
from meetup import *
import random
import time
import unicodedata
import hashlib
import base64
import datetime
import re
from wufoo import *
from salesforce import *
from mailchimp3 import MailChimp
from mailchimp3.mailchimpclient import MailChimpError
import gspread
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import stripe
import io
from datetime import datetime
from datetime import timedelta
import csv
import chapterreport
import rebuild_milestones
from repo_users import add_users_to_repos
from import_members import import_members, MemberData
from googleapi import OWASPGoogle
from googleapiclient.http import MediaIoBaseDownload
from owaspjira import OWASPJira
import helperfuncs
#from docusign_esign import EnvelopesApi
#from docusign_esign import ApiClient

import random
#import emoji

mailchimp = MailChimp(mc_api=os.environ["MAILCHIMP_API_KEY"])


def build_committee_json():
    gh = OWASPGitHub()
    repos = gh.GetPublicRepositories('www-committee')

    for repo in repos: #change to use title in project repo.....
        repo['name'] = repo['name'].replace('www-committee-','').replace('-', ' ')
        repo['name'] = " ".join(w.capitalize() for w in repo['name'].split())

    repos.sort(key=lambda x: x['name'])
    repos.sort(key=lambda x: x['level'], reverse=True)

    sha = ''
    r = gh.GetFile('owasp.github.io', '_data/committees.json')
    if gh.TestResultCode(r.status_code):
        doc = json.loads(r.text)
        sha = doc['sha']

    contents = json.dumps(repos)
    r = gh.UpdateFile('owasp.github.io', '_data/committees.json', contents, sha)
    if gh.TestResultCode(r.status_code):
        logging.info('Updated _data/committees.json successfully')
    else:
        logging.error(f"Failed to update _data/committees.json: {r.text}")

def build_project_json():
    # we want to build certain json data files every now and then to keep the website data fresh.
    #for each repository, public, with www-project
    #get name of project, level, and type
    # store in json
    #write json file out to github.owasp.io _data folder
    gh = OWASPGitHub()
    repos = gh.GetPublicRepositories('www-project')

    for repo in repos: #change to use title in project repo.....
        repo['name'] = repo['name'].replace('www-project-','').replace('-', ' ')
        repo['name'] = " ".join(w.capitalize() for w in repo['name'].split())

    repos.sort(key=lambda x: x['name'])
    repos.sort(key=lambda x: x['level'], reverse=True)

    sha = ''
    r = gh.GetFile('owasp.github.io', '_data/projects.json')
    if gh.TestResultCode(r.status_code):
        doc = json.loads(r.text)
        sha = doc['sha']

    contents = json.dumps(repos, indent=4)
    r = gh.UpdateFile('owasp.github.io', '_data/projects.json', contents, sha)
    if gh.TestResultCode(r.status_code):
        logging.info('Updated _data/projects.json successfully')
    else:
        logging.error(f"Failed to update _data/projects.json: {r.text}")

def create_github_repo(github, group, grouptype, msglist):

    r = github.CreateRepository(group, grouptype)
    if github.TestResultCode(r.status_code):
        r = github.InitializeRepositoryPages(group, grouptype)
    if github.TestResultCode(r.status_code):
        r = github.EnablePages(group, grouptype)
    if github.TestResultCode(r.status_code):
        msg = "Pages created for %s" % group
        print(msg)
        msglist.append(msg)
    else:
        msg = "Failure creating pages for %s: %s" % (group, r.text)
        print(msg)
        msglist.append(msg)

def create_all_pages():
    fp = open("projects.txt")

    project_type_chapter = 1
    project_type_project = 0

    github = OWASPGitHub()
    msglist = []
    msg = ""
    group = fp.readline()
    while group:
        group = group.lower().replace("owasp ", "").replace(" project","").replace("\n","")
        msg = "Creating pages for group: %s\n" % group
        print(msg)
        msglist.append(msg)
        create_github_repo(github, group, project_type_project, msglist)
        group = fp.readline()

    fp.close()

    fp = open("chapters.txt")

    group = fp.readline()
    while group:
        group = group.lower().replace("owasp ", "").replace("chapter","").replace("\n", "")
        msg = "Creating pages for group: %s\n" % group
        print(msg)
        msglist.append(msg)
        create_github_repo(github, group, project_type_chapter, msglist)
        group = fp.readline()

    fp.close()

    fp = open("creator.log", "w")
    fp.writelines(msglist)
    fp.close()

def update_project_pages():
    fp = open("projects.txt")

    msglist = []
    msg = ""
    group = fp.readline()
    while group:
        group = group.lower().replace("owasp ", "").replace(" project","").replace("\n","").replace("/", "-").replace("\t", " ").replace("\r", "")
        group = group.strip()
        sp_index = group.rfind(" ")
        gtype = group[sp_index + 1:]
        group = group[:group.rfind(" ")]
        msg = f"GROUP: {group} \nTYPE: {gtype}\n"
        print(msg)
        msglist.append(msg)
        github = OWASPGitHub()
        r = github.GetFile(github.FormatRepoName(group, 0), 'index.md')
        if github.TestResultCode(r.status_code):
            doc = json.loads(r.text)
            content = base64.b64decode(doc["content"]).decode()
            lvl_ndx = content.find("level:")
            eol = content.find("\n", lvl_ndx)
            content = content[:eol + 1] + 'type: ' + gtype + '\n' + content[eol + 1:]

            r = github.UpdateFile(github.FormatRepoName(group, 0), 'index.md', content, doc["sha"])
            if github.TestResultCode(r.status_code):
                print("Update success\n")
            else:
                print(f"Update failed {r.text}")
        else:
            print(f"Failed to get index.md for {group}: {r.text}")

        group = fp.readline()

    fp.close()

def update_chapter_pages():
    fp = open("chapters.txt")
    msglist = []
    msg = ""
    group = fp.readline()
    while group:
        sp_index = group.find("REGION:") + 7
        gtype = group[sp_index + 1:]
        gtype = gtype.strip()
        group = group[:group.find("REGION:")]
        group = group.lower().replace("owasp ", "").replace(" chapter","").replace("\n","").replace("/", "-").replace("\t", " ").replace("\r", "")
        group = group.strip()
        msg = f"GROUP: {group} \nREGION: {gtype}\n"
        print(msg)
        msglist.append(msg)
        github = OWASPGitHub()
        r = github.GetFile(github.FormatRepoName(group, 1), 'index.md')
        if github.TestResultCode(r.status_code):
            doc = json.loads(r.text)
            content = base64.b64decode(doc["content"]).decode()

            front_ndx = content.find("---", content.find("---") + 3) # second instance of ---
            content = content[:front_ndx] + 'region: ' + gtype + '\n\n' + content[front_ndx:]

            r = github.UpdateFile(github.FormatRepoName(group, 1), 'index.md', content, doc["sha"])
            if github.TestResultCode(r.status_code):
                print("Update success\n")
            else:
                print(f"Update failed {r.text}")
        else:
            print(f"Failed to get index.md for {group}: {r.text}")

        group = fp.readline()

    fp.close()




def AddChaptersToChapterTeam():
    gh = OWASPGitHub()
    repos = gh.GetPublicRepositories('www-chapter')
    for repo in repos:
        repoName = repo['name']
        r = gh.AddRepoToTeam('chapter-administration', repoName)
        if not r.ok:
            print(f'Failed to add repo: {r.text}')

def MigrateSelectedPages(filepath):
    f = open(filepath)
    gh = OWASPGitHub()

    for line in f.readlines():
        line = line.replace(' ', '_')
        line = line.strip('\n')
        frompath = f"{line}.md"
        if 'attack' in filepath:
            topath = f'pages/attacks/{frompath}' #same file name
        else:
            topath = f'pages/vulnerabilities/{frompath}'

        r = gh.MoveFromOFtoOWASP(frompath, topath)
        if r.ok:
            print('Page moved')
        else:
            print(f'{frompath} failed to move: {r.text}')

    f.close()

def clean_of_project(content):
    rescontent = ''
    td_count = 0
    for line in content.split('\n'):
        if '{{' in line:
            line = line.replace('{{','')

        if '<td>' in line:
            td_count = td_count + 1
        else:
            rescontent += line
            rescontent += '\n'

        if td_count == 2:
            rescontent += line
            rescontent += '\n'
    return rescontent

def clean_of_chapter(content):
    rescontent = ''
    for line in content.split('\n'):
        if '{{' in line:
            line = line.replace('{{','')

        rescontent += line
        rescontent += '\n'

    return rescontent

def ReplaceLeaderFile(gh, repo):
    r = gh.GetFile(repo, 'leaders.md', gh.content_fragment)
    if r.ok:
        doc = json.loads(r.text)
        sha = doc['sha']
        content = '<!--### Leaders\n-->'
        gh.UpdateFile(repo, 'leaders.md', content, sha)

def ReplaceProjectInfoLeaderFile(gh, repo):
    r = gh.GetFile(repo, 'info.md', gh.content_fragment)
    if r.ok:
        doc = json.loads(r.text)
        sha = doc['sha']
        content = '<!--### Project Information\n* Project Level\n* Project Type\n* Version, etc\n\n### Downloads or Social Links\n* [Download](#)\n* [Social Link](#)\n\n### Code Repository\n* [repo](#)-->'
        gh.UpdateFile(repo, 'info.md', content, sha)
    ReplaceLeaderFile(gh, repo)

def ReplaceChapterInfoLeaderFile(gh, repo):
    r = gh.GetFile(repo, 'info.md', gh.content_fragment)
    if r.ok:
        doc = json.loads(r.text)
        sha = doc['sha']
        content = '<!--### Chapter Information\n* Chapter Region\n\n### Social Links\n* [Meetup](#)\n* [Social Link](#)-->\n'
        gh.UpdateFile(repo, 'info.md', content, sha)
    ReplaceLeaderFile(gh, repo)


def MigrateProjectPages():
    f = open('proj_migration.txt')
    gh = OWASPGitHub()
    err_lines = []
    repo = ''
    sha = ''
    for line in f.readlines():
        frompath = line.replace(' ', '_')
        frompath = frompath.strip('\n')
        frompath = frompath + '.md'
        if 'OWASP_Top_Ten' in frompath:
            frompath='Category:OWASP_Top_Ten_Project.md'
        elif 'Container_Security_Verification_Standard' in frompath:
            frompath='OWASP_Container_Security_Verification_Standard_(CSVS).md'
        elif 'Little_Web_Application_Firewall' in frompath:
            frompath='OWASP_LWAF.md'
        elif 'OWASP_PHP_Project' in frompath:
            frompath = 'Category:PHP.md'
        elif 'Enterprise_Security_API' in frompath:
            frompath = 'Category:OWASP_Enterprise_Security_API.md'
        elif 'OWASP_Security_Pins' in frompath:
            frompath = 'OWASP_Security_Pins_Project.md'
        elif 'OWASP_Code_Review_Guide' in frompath:
            frompath = 'Category:OWASP_Code_Review_Project.md'
        elif 'OWASP_EnDe_Project' in frompath:
            frompath = 'Category:OWASP_EnDe.md'
        elif 'OWASP_Secure_Coding_Practices_Quick_Reference' in frompath:
            frompath = 'OWASP_Secure_Coding_Practices_-_Quick_Reference_Guide.md'
        elif 'OWASP_Web_Application_Firewall_Evaluation' in frompath:
            frompath = 'WASC_OWASP_Web_Application_Firewall_Evaluation_Criteria_Project.md'
        elif 'Top_10_Fuer_Entwickler' in frompath:
            frompath = 'Category:OWASP_Top_10_fuer_Entwickler.md'
        elif 'Benchmark_Projeect' in frompath:
            frompath = 'Benchmark.md'
        elif 'OWASP_Node.js_Goat' in frompath:
            frompath = 'OWASP_Node_js_Goat_Project.md'
        elif 'BELVA' in frompath:
            frompath = 'OWASP_Basic_Expression_%26_Lexicon_Variation_Algorithms_(BELVA)_Project.md'
        elif 'DeepViolet' in frompath:
            frompath = 'OWASP_DeepViolet_TLS/SSL_Scanner.md'
        elif 'Internet_of_Things_Top_10' in frompath:
            frompath = 'OWASP_Internet_of_Things_Top_Ten_Project.md'
        elif 'Podcast' in frompath:
            frompath = 'OWASP_Podcast.md'
        elif 'Virtual_Patching_Best_Practices' in frompath:
            frompath = 'Virtual_Patching_Best_Practices.md'
        elif 'OWASP_CTF_Project' in frompath:
            frompath = 'Category:OWASP_CTF_Project.md'

        r = gh.GetFile('owasp-wiki-md', frompath, gh.of_content_fragment)
        if r.ok:
            doc = json.loads(r.text)
            repo = f"www-project-{line.replace('OWASP ', '').replace(' Project', '').replace(' ', '-').lower()}"
            repo = repo.replace('\n','')
            topath = 'index.md'
            r = gh.GetFile(repo, topath, gh.content_fragment)
            if r.ok:
                idoc = json.loads(r.text)
                icontent = base64.b64decode(idoc['content']).decode()
                sha = idoc['sha']
                if 'an example of a Project or Chapter' in icontent and "<div style='color:red;'>" in icontent: # a non-edited page that isn't a new chapter recently created
                    continue # do not process this file...
                elif 'an example of a Project or Chapter' not in icontent: # this is not a default page
                    continue

        if r.ok:# grab the index.md content and update with new header info
            content = base64.b64decode(doc["content"]).decode()
            fcontent = ''
            frontmatter = 0
            for iline in icontent.split('\n'):
                if frontmatter < 2:
                    if 'level: ' in iline:
                        iline =  'level: 0'
                    if iline == '---' and frontmatter == 1:
                        fcontent += 'auto-migrated: 1\n\n'
                    fcontent += iline
                    fcontent += '\n'

                    if iline == '---':
                        frontmatter += 1
                else:
                    break
            base_index = open('base_index.md')
            base_content = ''
            for baseline in base_index.readlines():
                base_content += baseline
            tindex = fcontent.find('title:')
            if tindex > -1:
                oldtitle = fcontent[tindex + 7:fcontent.find('\n', tindex + 7)]
                newtitle = oldtitle.title()
                newtitle = newtitle.replace('Owasp', 'OWASP')
                fcontent = fcontent.replace(oldtitle, newtitle)

            migrated_frontmatter = fcontent.replace('auto-migrated: 1\n\n', '')

            fcontent += base_content #The index.md file should be the base_index.md + front-matter
            r = gh.UpdateFile(repo, topath, fcontent, sha)
            if r.ok:
                mr = gh.GetFile(repo, 'migrated_content.md', gh.content_fragment)
                msha = ''
                if mr.ok:
                    mdoc = json.loads(mr.text)
                    msha = mdoc['sha']

                content = clean_of_project(content)
                migrated_content = migrated_frontmatter + content
                r = gh.UpdateFile(repo, 'migrated_content.md', migrated_content, msha)

        if r.ok:
            ReplaceProjectInfoLeaderFile(gh, repo)
            print(f'{repo} page migrated')
        else:
            err = f'{line} failed to migrate: {r.text}'
            err_lines.append(err)
            print(err)

    f.close()

    errf = open('proj_migration_errors.txt', 'w')
    errf.writelines(err_lines)
    errf.close()

def MigrateChapterPages():
    f = open('chap_migration.txt')
    gh = OWASPGitHub()
    err_lines = []
    repo = ''
    sha = ''
    for line in f.readlines():
        frompath = line.replace(' ', '_')
        frompath = frompath.strip('\n')
        frompath = frompath + '.md'

        r = gh.GetFile('owasp-wiki-md', frompath, gh.of_content_fragment)
        if r.ok:
            doc = json.loads(r.text)
            repo = f"www-chapter-{line.replace('OWASP ', '').replace(' Chapter', '').replace(' ', '-').lower()}"
            repo = repo.replace('\n','')
            topath = 'index.md'
            r = gh.GetFile(repo, topath, gh.content_fragment)
            if r.ok:
                idoc = json.loads(r.text)
                icontent = base64.b64decode(idoc['content']).decode()
                sha = idoc['sha']
                if 'an example of a Project or Chapter' in icontent and "<div style='color:red;'>" in icontent: # a non-edited page that isn't a new chapter recently created
                    continue # do not process this file...
                elif 'an example of a Project or Chapter' not in icontent: # this is not a default page
                    continue

        if r.ok: # grab the index.md content and update with new header info
            content = base64.b64decode(doc["content"]).decode()
            fcontent = ''
            frontmatter = 0
            for iline in icontent.split('\n'):
                if frontmatter < 2:
                    if 'level: ' in iline:
                        iline =  'level: 0'
                    if iline == '---' and frontmatter == 1:
                        fcontent += 'auto-migrated: 1\n\n'
                    fcontent += iline
                    fcontent += '\n'

                    if iline == '---':
                        frontmatter += 1

                else:
                    break

            base_index = open('base_index.md')
            base_content = ''
            for baseline in base_index.readlines():
                base_content += baseline
            tindex = fcontent.find('title:')
            if tindex > -1:
                oldtitle = fcontent[tindex + 7:fcontent.find('\n', tindex + 7)]
                newtitle = oldtitle.title()
                newtitle = newtitle.replace('Owasp', 'OWASP')
                fcontent = fcontent.replace(oldtitle, newtitle)

            migrated_frontmatter = fcontent.replace('auto-migrated: 1\n\n', '\n')

            fcontent += base_content #The index.md file should be the base_index.md + front-matter
            r = gh.UpdateFile(repo, topath, fcontent, sha)
            if r.ok:
                mr = gh.GetFile(repo, 'migrated_content.md', gh.content_fragment)
                msha = ''
                if mr.ok:
                    mdoc = json.loads(mr.text)
                    msha = mdoc['sha']

                content = clean_of_chapter(content)
                migrated_content = migrated_frontmatter + content
                r = gh.UpdateFile(repo, 'migrated_content.md', migrated_content, msha)

        if r.ok:
            ReplaceChapterInfoLeaderFile(gh, repo)
            print(f'{repo} page migrated')
        else:
            err = f'{line} failed to migrate: {r.text}'
            err_lines.append(err)
            print(err)

    f.close()

    errf = open('chapter_migration_errors.txt', 'w')
    errf.writelines(err_lines)
    errf.close()

def CreateProjectPageList():
    f = open('proj_migration.txt')
    #gh = OWASPGitHub()
    out_lines = []
    lines = f.readlines()
    total = len(lines)
    current = 1
    for line in lines:
        print(f'Processing {current} of {total}\n')
        current += 1
        frompath = line.replace(' ', '_')
        frompath = frompath.strip('\n')
        frompath = frompath + '.md'
        if 'OWASP_Top_Ten' in frompath:
            frompath='Category:OWASP_Top_Ten_Project.md'
        #r = gh.GetFile('owasp-wiki-md', frompath, gh.of_content_fragment)
        #if r.ok:
        out_lines.append(f"{frompath.replace('.md', '')}\n")
        #else:
        #    out_lines.append(f"Not found: {frompath.replace('md','')}\n")

    f.close()
    f = open('proj_pages.txt','w')
    f.writelines(out_lines)
    f.close()
    print('completed\n')

def process_group_leaders(group, leaders, emails):
    gh = OWASPGitHub()
    www_group = gh.FormatRepoName(group, 0)
    www_cgroup = gh.FormatRepoName(group, 1)
    r = gh.RepoExists(www_group)
    if not r.ok:
        www_group = www_cgroup
    r = gh.RepoExists(www_group)
    if not r.ok:
        print(f'{www_group} does not exist.\n')
    else:
        r = gh.GetFile(www_group, 'leaders.md')
        if r.ok:
            doc = json.loads(r.text)
            sha = doc['sha']
            content = base64.b64decode(doc['content']).decode()
            lc = gh.GetLastUpdate(www_group, 'leaders.md')
            updated_recently = ('@' in content and '2019-12-28' in lc)
            # remove need for test by cleaning list
            #if (not ('@' in content) and not ('www.owasp.org' in content)) or ('leader.email@owasp.org' in content) or updated_recently:
            #we can replace the contents of this file
            content = '### Leaders\n\n'
            ndx = 0
            for leader in leaders:
                email = f'mailto:{emails[ndx].strip()}'
                if not '@owasp.org' in email:
                    email = 'mailto:' # no email, needs update
                content += f'* [{leader.strip()}]({email})\n'
                ndx = ndx + 1

            r = gh.UpdateFile(www_group, 'leaders.md', content, sha)
            if r.ok:
                print('Updated leaders file\n')
            else:
                print(f'FAILED to update {www_group}\n')

def add_leaders():
    curr_group = ''
    leaders = []
    emails = []

    f = open('all_leaders.csv')
    for line in f.readlines():
        line = line.replace('"', '')
        keys = line.split(',')
        keycount = len(keys)
        ldr_ndx = 2
        eml_ndx = 1
        tmp_group = keys[0]

        # Portland, Maine
        if keycount > 3:
            tmp_group = f'{tmp_group}, {keys[1]}'
            ldr_ndx = 3
            eml_ndx = 2

        if curr_group == '':
            curr_group = tmp_group
            leaders.append(keys[ldr_ndx])
            emails.append(keys[eml_ndx])
        elif curr_group != tmp_group:
            print(f'Processing {curr_group}:\n')
            ndx = 0
            for leader in leaders:
                print(f'\tLeader: {leader}, {emails[ndx]}\n')
                ndx = ndx + 1
            process_group_leaders(curr_group, leaders, emails)
            leaders.clear()
            emails.clear()
            curr_group = tmp_group
            leaders.append(keys[ldr_ndx])
            emails.append(keys[eml_ndx])
        else:
            leaders.append(keys[ldr_ndx])
            emails.append(keys[eml_ndx])

def replace_all(old, new, text):
    idx = 0
    while idx < len(text):
        index_l = text.lower().find(old.lower(), idx)
        if index_l == -1:
            return text
        text = text[:index_l] + new + text[index_l + len(old):]
        idx = index_l + len(new)
    return text

# this function checks for pdfs and corrects link for website if media: or still old wiki
def walk_text(text):
    idx = 0
    repl_pdf_link = '/www-pdf-archive/'
    repl_wiki_txt = ''
    pdf_text = '.pdf'

    while idx < len(text):
        index_l = text.lower().find(pdf_text, idx) # .pdf found in text
        if index_l == -1:
            return text  # no pdf, we are done

        p_ndx = text.lower().rfind('https://www.owasp.org', idx, index_l)
        lentxt = 0
        if p_ndx == -1:
            p_ndx = text.lower().rfind('media:', idx, index_l)
            if p_ndx > -1:
                lentxt = 6
        else:
            lentxt = (text.lower().rfind('/', idx, index_l) + 1) - p_ndx

        if p_ndx == -1:
            return text # the pdf is not linked with media or with www.owasp.org

        if text.lower().find(' ', p_ndx, index_l) == -1: # no spaces between the previous owasp or media and the pdf link
            text = text[:p_ndx] + repl_pdf_link + text[p_ndx + lentxt:]

        idx = text.lower().find(pdf_text, idx) + len(pdf_text)

    return text

def update_pdf_links():
    gh = OWASPGitHub()
    repos = gh.GetPublicRepositories()
    for repo in repos:
        repoName = repo['name']
        r = gh.GetFile(repoName, 'migrated_content.md')
        if r.ok:
            doc = json.loads(r.text)
            sha = doc['sha']
            base_content = base64.b64decode(doc['content']).decode()
            content = walk_text(base_content)
            if content != base_content:
                content = content.replace('title = "wikilink"', '')
                content = content.replace('"wikilink"', '')
                gh.UpdateFile(repoName, 'migrated_content.md', content, sha)

def replicate_404():
    gh = OWASPGitHub()
    r404 = gh.GetFile('owasp.github.io', '404.html')
    if r404.ok:
        doc = json.loads(r404.text)
        sha = doc['sha']
        content = base64.b64decode(doc['content']).decode()

    repos = gh.GetPublicRepositories()
    for repo in repos:
        repoName = repo['name']
        r = gh.GetFile(repoName, '404.html')
        if not r.ok and 'www-' in repoName:
            r = gh.UpdateFile(repoName, '404.html', content, '')
            if not r.ok:
                print(f'Failed to update {repoName}: {r.text}\n')
            else:
                print('Updated repo...\n')

def parse_leaderline(line):
    ename = line.find(']')
    name = line[line.find('[') + 1:line.find(']')]
    email = line[line.find('(', ename) + 1:line.find(')', ename)]
    return name, email

def add_to_leaders(repo, content, all_leaders, stype):
    lines = content.split('\n')
    max_leaders = 5
    leader_count = 0
    in_leaders = False
    for line in lines:
        testline = line.lower()
        if in_leaders and leader_count > 0 and not testline.startswith('*'):
            break

        if(testline.startswith('###') and 'leader' not in testline):
            break
        elif testline.startswith('###') and 'leader' in testline:
            in_leaders = True
            continue

        fstr = line.find('[')
        if(line.startswith('*') and fstr > -1 and fstr < 4):
            name, email = parse_leaderline(line)
            if 'leader.email@owasp.org' not in email and leader_count < max_leaders: # default
                leader = {}
                leader['name'] = name
                leader['email'] = email.replace('mailto://', '').replace('mailto:','').lower()
                leader['group'] = repo['title']
                leader['group-type'] = stype
                leader['group_url'] = repo['url']

                all_leaders.append(leader)
                leader_count = leader_count + 1


def build_leaders_json(gh):
    all_leaders = []
    repos = gh.GetPublicRepositories('www-')
    for repo in repos:
        stype = ''

        # temporary suspend check for testing
        #if 'www-projectchapter-example' in repo['url']:
        #    continue

        if 'www-chapter' in repo['url']:
            stype = 'chapter'
        elif 'www-committee' in repo['url']:
            stype = 'committee'
        elif 'www-project' in repo['url']:
            stype = 'project'
        elif 'www-revent' in repo['url']:
            stype = 'event'
        else:
            continue

        r = gh.GetFile(repo['name'], 'leaders.md')
        if r.ok:
            doc = json.loads(r.text)
            content = base64.b64decode(doc['content']).decode(encoding='utf-8')

            add_to_leaders(repo, content, all_leaders, stype)
        else:
            print(f"Could not get leaders.md file for {repo['name']}: {r.text}")

    r = gh.GetFile('owasp.github.io', '_data/leaders.json')
    sha = ''
    if r.ok:
        doc = json.loads(r.text)
        sha = doc['sha']

    r = gh.UpdateFile('owasp.github.io', '_data/leaders.json', json.dumps(all_leaders, ensure_ascii=False, indent = 4), sha)
    if r.ok:
        print('Update leaders json succeeded')
    else:
        print(f'Update leaders json failed: {r.status}')

def CollectMailchimpTags():
    audience = mailchimp.lists.members.all(os.environ["MAILCHIMP_LIST_ID"], get_all=True)

    print(len(audience['members']))

    for person in audience['members']:
        for tag in person['tags']:
            if('Dublin' in tag['name']):
                print(person['email_address'])

def build_chapter_json(gh):
    # we want to build certain json data files every now and then to keep the website data fresh.
    #for each repository, public, with www-project
    #get name of project, level, and type
    # store in json
    #write json file out to github.owasp.io _data folder
    repos = gh.GetPublicRepositories('www-chapter')

    fmt_str = "%a %b %d %H:%M:%S %Y"
    for repo in repos:
        repo['name'] = repo['name'].replace('www-chapter-','').replace('-', ' ')
        repo['name'] = " ".join(w.capitalize() for w in repo['name'].split())
        try:
            dobj = datetime.strptime(repo['created'], fmt_str)
            repo['created'] = dobj.strftime("%Y-%m-%d")
        except ValueError:
            pass
        try:
            dobj = datetime.strptime(repo['updated'], fmt_str)
            repo['updated'] = dobj.strftime("%Y-%m-%d")
        except ValueError:
            pass
        
        ecount = 0
        if 'meetup-group' in repo:
            mu = OWASPMeetup()
            mu.Login()
            estr = mu.GetGroupEvents(repo['meetup-group'], "past")
            if estr:
                events = json.loads(estr)
                today = datetime.today()
                for event in events:
                    eventdate = datetime.strptime(event['local_date'], '%Y-%m-%d')
                    tdelta = today - eventdate
                    if tdelta.days > 0 and tdelta.days < 365:
                        ecount = ecount + 1
        repo['meetings'] = ecount

                
    repos.sort(key=lambda x: x['name'])
    repos.sort(key=lambda x: x['region'], reverse=True)

    sha = ''
    r = gh.GetFile('owasp.github.io', '_data/chapters.json')
    if gh.TestResultCode(r.status_code):
        doc = json.loads(r.text)
        sha = doc['sha']

    contents = json.dumps(repos, indent=4)
    r = gh.UpdateFile('owasp.github.io', '_data/chapters.json', contents, sha)
    if gh.TestResultCode(r.status_code):
        print('Updated _data/chapters.json successfully')
    else:
        print(f"Failed to update _data/chapters.json: {r.text}")

def build_inactive_chapters_json(gh):
    repos = gh.GetPublicRepositories('www-chapter', True)

    for repo in repos:
        repo['name'] = repo['name'].replace('www-chapter-','').replace('-', ' ')
        repo['name'] = " ".join(w.capitalize() for w in repo['name'].split())

    repos.sort(key=lambda x: x['name'])
    repos.sort(key=lambda x: x['region'], reverse=True)

    sha = ''
    r = gh.GetFile('owasp.github.io', '_data/inactive_chapters.json')
    if gh.TestResultCode(r.status_code):
        doc = json.loads(r.text)
        sha = doc['sha']

    contents = json.dumps(repos)
    r = gh.UpdateFile('owasp.github.io', '_data/inactive_chapters.json', contents, sha)
    if gh.TestResultCode(r.status_code):
        logging.info('Updated _data/inactive_chapters.json successfully')
    else:
        logging.error(f"Failed to update _data/inactive_chapters.json: {r.text}")

def GetContactInfo():
    names = []
    sf = OWASPSalesforce()
    sf.Login()
    with open('contacts.txt', 'r') as f:
        for line in f.readlines():
           qry = f"Select FirstName, LastName, Email From Contact Where Id = '{line.strip()}'"
           records = sf.Query(qry)
           fname = ''
           lname = ''
           email = ''
           if len(records) > 0:
                if 'FirstName' in records[0]:
                    fname = records[0]['FirstName']
                if 'LastName' in records[0]:
                    lname = records[0]['LastName']
                if 'Email' in records[0]:
                    email = records[0]['Email']
                names.append(f"{fname}, {lname}, {email}\n")
           else:
                print(f'No record found for {line.strip()}')

    with open('contacts_resolved.txt', 'w') as of:
        of.writelines(names)

def GetLeaders(gh, chapter_repo):
    r = gh.GetFile(chapter_repo, 'leaders.md')
    all_leaders = []
    if r.ok:
        doc = json.loads(r.text)
        content = base64.b64decode(doc['content']).decode(encoding='utf-8')
        lines = content.split('\n')
        for line in lines:
            fstr = line.find('[')
            if(line.startswith('###') and 'Leaders' not in line):
                break

            if(line.startswith('*') and fstr > -1 and fstr < 4):
                name, email = parse_leaderline(line)
                if email:
                    email = email.replace('mailto:\\', '')
                    email = email.replace('mailto://', '')
                    email = email.replace('mailto:', '')
                    all_leaders.append(email)

    return all_leaders

def GetRegion(cp, region):
    cp_region = None
    if region == 'Africa':
        cp_region = cp.cp_project_chapter_region_option_africa
    elif region == 'Asia':
        cp_region = cp.cp_project_chapter_region_option_asia
    elif region == 'Europe':
        cp_region = cp.cp_project_chapter_region_option_europe
    elif region == 'Oceania':
        cp_region = cp.cp_project_chapter_region_option_oceania
    elif region == 'South America':
        cp_region = cp.cp_project_chapter_region_option_southamerica
    elif region == 'North America' or region == 'United States':
        cp_region = cp.cp_project_chapter_region_option_northamerica

    return cp_region


def DoCopperCreate():
    gh = OWASPGitHub()
    committees = gh.GetPublicRepositories('www-committee')
    cp = OWASPCopper()
    failed_list = []
    for committee in committees:
        if len(cp.FindProject('Project - ' + committee['title'])) > 0:
            continue
        leaders = GetLeaders(gh, committee['name'])
        print(f"Attempting to create project: {committee['title']}")
        r = cp.CreateProject('Project - ' + committee['title'],
                        leaders,
                        cp.cp_project_type_option_committee,
                        cp.cp_project_chapter_status_option_active,
                        '',
                        '',
                        '',
                        'https://github.com/owasp/' + committee['name'])

        if r:
            print(f"Created Copper project: {committee['title']}")
        else:
            print(f"Failed to create: {committee['title']}")
            failed_list.append(committee['name'] + '\n')

    with open('failed_copper_committees.txt', 'w') as f:
        f.writelines(failed_list)



def deEmojify(text):
    EMOJI_PATTERN = re.compile(
        "(["
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251" 
        "])"
    )

    return EMOJI_PATTERN.sub(u'', text)

def add_to_events(gh, mue, events, repo):
    
    if len(mue) <= 0 or 'errors' in mue:
        return events
    group = repo.replace('www-chapter-','')
    group = group.replace('www-project-','')
    group = group.replace('www-committee-','')
    group = group.replace('-', ' ')

    group = " ".join(w.capitalize() for w in group.split())
                
    for mevent in mue:
        event = {}
        today = datetime.today()
        eventdate = datetime.strptime(mevent['local_date'], '%Y-%m-%d')
        tdelta = eventdate - today
        if tdelta.days >= 0 and tdelta.days < 30:
            event['group'] = group
            event['repo'] = repo
            event['name'] = mevent['name']
            event['date'] = mevent['local_date']
            event['time'] = mevent['local_time']
            event['link'] = mevent['link']
            event['timezone'] = mevent['group']['timezone']
            if 'description' in mevent:
                event['description'] = deEmojify(mevent['description'])
            else:
                event['description'] = ''
                
            events.append(event)

    return events

def create_chapter_events(gh, mu):
    repos = gh.GetPublicRepositories('www-chapter')
    
    events = []
    for repo in repos:
        if 'meetup-group' in repo and repo['meetup-group']:
            if mu.Login():
                mstr = mu.GetGroupEvents(repo['meetup-group'])
                if mstr:
                    muej = json.loads(mstr)
                    add_to_events(gh, muej, events, repo['name'])
                

    if len(events) <= 0:
        return
        
    r = gh.GetFile('owasp.github.io', '_data/chapter_events.json')
    sha = ''
    if r.ok:
        doc = json.loads(r.text)
        sha = doc['sha']
    
    contents = json.dumps(events, indent=4)
    r = gh.UpdateFile('owasp.github.io', '_data/chapter_events.json', contents, sha)
    if r.ok:
        logging.info('Updated _data/chapter_events.json successfully')
    else:
        logging.error(f"Failed to update _data/chapter_events.json: {r.text}")

def create_community_events(gh, mu):
    repos = gh.GetPublicRepositories('www-')
    
    events = []
    for repo in repos:
        if 'www-chapter' not in repo['name'] and 'www-project' not in repo['name'] and 'www-committee' not in repo['name']:
            continue

        if 'meetup-group' in repo and repo['meetup-group']:
            if mu.Login():
                mstr = mu.GetGroupEvents(repo['meetup-group'])
                if mstr:
                    muej = json.loads(mstr)
                    add_to_events(gh, muej, events, repo['name'])
                

    if len(events) <= 0:
        return
        
    r = gh.GetFile('www-community', '_data/community_events.json')
    sha = ''
    if r.ok:
        doc = json.loads(r.text)
        sha = doc['sha']
    
    contents = json.dumps(events, indent=4)
    r = gh.UpdateFile('www-community', '_data/community_events.json', contents, sha)
    if r.ok:
        logging.info('Updated _data/community_events.json successfully')
    else:
        logging.error(f"Failed to update _data/community_events.json: {r.text}")

def add_chapter_meetups(gh, mu, outfile):

    outlines = []
    with open("chapter-meetups.txt") as fp:
        for line in fp:
            splits = line.split(':')
            repo = splits[0]
            meetup = splits[1]
            country = ''
            postal = ''
            if len(splits) > 2:
                country = splits[2]
            if len(splits) > 3:
                postal = splits[3]

            sha = ''
            r = gh.GetFile(repo, 'index.md')
            if gh.TestResultCode(r.status_code):
                doc = json.loads(r.text)
                sha = doc['sha']
                content = base64.b64decode(doc["content"]).decode()
                fndx = content.find('---')
                sndx = content.find('---', fndx + 3) - 2
                hasmu = content.find('meetup-group:')
                if hasmu > 0 and hasmu < sndx:
                    print('index.md already has meetup-group')
                    outlines.append(f'index.md already has meetup-group\n')
                    continue

                docstart = content[0:sndx] + '\n'
                addstr = 'meetup-group: ' + meetup + '\n'
                addstr += 'country: ' + country + '\n'
                addstr += 'postal-code: ' + postal + '\n'
                docend = content[sndx + 2:]
                if not docend.startswith('\n') and not addstr.endswith('\n\n'):
                    addstr += '\n'

                content = docstart + addstr + docend

                r = gh.UpdateFile(repo, 'index.md', content, sha)
                if gh.TestResultCode(r.status_code):
                    print('Updated index.md successfully')
                    outlines.append('Updated index.md successfully\n')
                else:
                    print(f"Failed to update index.md: {r.text}")
                    outlines.append(f'Failed to update index.md: {r.text}')
    outfile.writelines(outlines)

def retrieve_member_counts(zoom_accounts):
    counts = []
    og = OWASPGoogle()
    for za in zoom_accounts:
        data = {'account': za, 'count': 0 }
        members = og.GetGroupMembers(za)
        data['count'] = len(members['members'])
        counts.append(data)

    return sorted(counts, key=lambda group: group['count'])

def send_onetime_secret(leaders, secret):
    headers = {
        'Authorization':f"Basic {base64.b64encode((os.environ['OTS_USER'] + ':' + os.environ['OTS_API_KEY']).encode()).decode()}"
    }
    for leader in leaders:
        r = requests.post(f"https://onetimesecret.com/api/v1/share/?secret=Zoom%20Password%20is%20{secret}&recipient={leader['email']}", headers=headers)
        if not r.ok:
            print(r.text)

def create_zoom_account(chapter_url):
    #creating a zoom account requires
    #  1.) creating a [chapter-name]-leaders@owasp.org group account
    #  2.) adding leaders to group
    #  3.) determining which zoom group to put them in (currently 4 groups)

    #  4.) sending onetimesecret link with password to person who requested access
    chapter_name = chapter_url.replace('www-projectchapter-','').replace('www-chapter-', '').replace('www-project-', '').replace(' ', '-')
    leadersemail = f"{chapter_name}-leaders@owasp.org"

    leaders = []
    gh = OWASPGitHub()
    leaders = gh.GetLeadersForRepo(chapter_url)

    if len(leaders) > 0:
        og = OWASPGoogle()
        result = og.FindGroup(leadersemail)
        if result == None:
            result = og.CreateGroup(leadersemail)
        if not 'Failed' in result:
            for leader in leaders:
                og.AddMemberToGroup(leadersemail, leader['email'])

        if not 'Failed' in result:
            zoom_accounts = ['leaders-zoom-one@owasp.org', 'leaders-zoom-two@owasp.org', 'leaders-zoom-three@owasp.org', 'leaders-zoom-four@owasp.org']
            retrieve_member_counts(zoom_accounts)
            # the list is sorted by count so first one is golden..
            result = og.FindGroup(zoom_accounts[0])
            if result != None and not 'Failed' in result:
                og.AddMemberToGroup(zoom_accounts[0], leadersemail)

            zoom_account = zoom_accounts[0][0:zoom_accounts[0].find('@')]

            send_onetime_secret(leaders, os.environ[zoom_account.replace('-', '_') +'_pass'])

    return None

def AddStripeMembershipToCopper():
    stripe.api_key = os.environ['STRIPE_SECRET']
    customers = stripe.Customer.list(limit=100)
    count = 0
    for customer in customers.auto_paging_iter():
        if not customer.name or customer.name.strip() == '':
            UpdateCustomerName(stripe, customer)

        metadata = customer.get('metadata', None)
        count = count + 1
        if metadata and metadata.get('membership_type', None) and metadata.get('membership_start', None):
            AddToMemberOpportunityIfNotExist(customer, metadata)

        print(f"Checking {count}", end="\r", flush=True)

def DetectStripeMembershipNotInCopper():
    stripe.api_key = os.environ['STRIPE_SECRET']
    customers = stripe.Customer.list(limit=100)
    count = 0
    for customer in customers.auto_paging_iter():
        metadata = customer.get('metadata', None)
        count = count + 1
        if metadata and metadata.get('membership_type', None) and metadata.get('membership_start', None):
            copper = OWASPCopper()
            mstart = metadata.get('membership_start', None)
            mend = metadata.get('membership_end', None)
            mtype = metadata.get('membership_type', None)
            mrecurr = metadata.get('membership_recurring', None)

            member = MemberData(customer.get('name'), customer.email.lower(), "", "", "", mstart, mend, mtype, mrecurr)
            sub = member.GetSubscriptionData()
            if not copper.FindMemberOpportunity(customer.email, sub):
                #copper.CreateOWASPMembership(customer.id, customer.name, customer.email, sub)
                print(f"Customer {customer.email} with membership type {mtype}, starting on {mstart} and ending on {mend} NOT in Copper")

        print(f"Checking {count}", end="\r", flush=True)

def UpdateCustomerName(stripe, cust):
    payments = stripe.PaymentIntent.list(customer=cust.id)
    subscriptions = stripe.Subscription.list(customer=cust.id)
    name = None

    for payment in payments:
        metadata = payment.get('metadata', None)
        if metadata:
            name = metadata.get('name','').strip()
            if name != '':
                break

    if not name or name == '':
        for sub in subscriptions:
            metadata = sub.get('metadata', None)
            if metadata:
                name = metadata.get('name','').strip()
                if name != '':
                    break
    if not name or name == '':
        name = 'Unknown'

    stripe.Customer.modify(cust.id, name=name)
    cust.name = name

def AddToMemberOpportunityIfNotExist(customer, metadata):
    copper = OWASPCopper()
    mstart = metadata.get('membership_start', None)
    mend = metadata.get('membership_end', None)
    mtype = metadata.get('membership_type', None)
    mrecurr = metadata.get('membership_recurring', None)

    member = MemberData(customer.get('name'), customer.email.lower(), "", "", "", mstart, mend, mtype, mrecurr)
    sub = member.GetSubscriptionData()
    if not copper.FindMemberOpportunity(customer.email, sub):
        copper.CreateOWASPMembership(customer.id, customer.name, customer.email, sub)
        print(f"Added {customer.email} with membership type {mtype}, starting on {mstart} and ending on {mend}")

def verify_cleanup(cfile):
    with open(cfile) as csvfile:
        reader = csv.DictReader(csvfile)
        stripe.api_key = os.environ['STRIPE_SECRET']
        total = 295144
        count = 0
        for row in reader:
            count = count + 1
            wait_call = True
            cid = row['id']
            print(f"{count} of {total}")
            cleanup = row['cleanup_customer (metadata)']
            drop_off = 1.0
            if cleanup == 'TRUE':
                while wait_call:
                    wait_call = False
                    try:
                        customer = stripe.Customer.retrieve(cid)
                        if customer:
                            metadata = customer.get('metadata', None)
                            if metadata and (metadata.get('membership_type', None) or metadata.get('membership_end', None) or metadata.get('membership_recurring', None) or metadata.get('membership_start', None)):
                                print(f"WARNING: Customer {cid} has metadata!")
                            payments = stripe.PaymentIntent.list(customer=cid)
                            if payments:
                                for payment in payments:
                                    if payment.status != 'canceled':
                                        print(f"WARNING: Customer {cid} has made payments!")
                            subscriptions = stripe.Subscription.list(customer=cid)
                            if subscriptions:
                                print(f"WARNING: Customer {cid} has subscriptions!")
                            invoices = stripe.Invoice.list(customer=cid)
                            if invoices:
                                print(f"WARNING: Customer {cid} has invoices!")
                            orders = stripe.Order.list(customer = cid)
                            if orders:
                                print(f"WARNING: Customer {cid} has orders!")
                        drop_off = 1
                    except:
                        wait_call = True
                        # possibly raised an exception because limited Stripe API calls...
                        time.sleep((4 + drop_off) * random.randint(1,4))
                        drop_off *= 1.25
                        pass

# def get_docusign_docs():
#     api_client = ApiClient()
#     api_client.host = "account-d.docusign.com"
#     api_client.set_default_header(header_name="Authorization", header_value=f"Bearer {os.environ['DOCUSIGN_APITOKEN']}")
#     env_api = EnvelopesApi(api_client)
#     # moronic api requires from_date or similar to list envelopes because, you know, they cannot just list all the envelopes
#     # and, of course, to list envelopes, you should call is list_status_changes....
#     envelopes = env_api.list_status_changes()
#     docs = env_api.list_documents(account_id=os.environ['DOCUSIGN_ACCOUNT'], envelope_id=err...we need to list envelopes first?)

def update_customer_metadata_null():
    #stripe.api_key = os.environ['STRIPE_SECRET']
    customers = stripe.Customer.list(email="harold.blankenship@owasp.com", api_key=os.environ['STRIPE_SECRET'])
    for customer in customers.auto_paging_iter():
        stripe.Customer.modify(customer.id, metadata={'membership_end': ''}, api_key=os.environ['STRIPE_SECRET']) # this version works so long as emptry string is passed....passing None does NOT work

    list_id = os.environ['MAILCHIMP_LIST_ID']
    email = 'harold.blankenship@owasp.com'
    searchres = mailchimp.search_members.get(query=f"{email}", list_id=list_id)
    members = searchres['exact_matches']['members']
    merge_fields = {}
    merge_fields['MEMEND'] = '' # blank is correct way to do mailchimp (not None)
    member_data = {
        "email_address": email,
        "status_if_new": "subscribed",
        "merge_fields": merge_fields
    }
    count = 0
    for member in members:
        subscriber_hash = hashlib.md5(email.encode('utf-8')).hexdigest()
        list_member = mailchimp.lists.members.create_or_update(os.environ['MAILCHIMP_LIST_ID'], subscriber_hash, member_data) # status_if_new is required and this may be more info than expected/needed
        count = count + 1
        print(f"Updating {count}", end="\r", flush=True)

    print("done")

def update_www_repos_main():
    gh = OWASPGitHub()
    repos = gh.GetPublicRepositories('www-chapter')
    for repo in repos:
        repoName = repo['name']
        r = gh.GetFile(repoName, '_config.yml')
        if r.ok and 'www-' in repoName:
            doc = json.loads(r.text)
            sha = doc['sha']
            content = base64.b64decode(doc['content']).decode()
            if 'www--site-theme' in content and not '@main' in content:
                content = content.replace('www--site-theme', 'www--site-theme@main')
                r = gh.UpdateFile(repoName, '_config.yml', content, sha)
                if not r.ok:
                    print(f'Failed to update {repoName}: {r.text}\n')
                else:
                    print(f'Updated repo {repoName}\n')

def update_www_repos_site():
    gh = OWASPGitHub()
    repos = gh.GetPublicRepositories('www-')
    for repo in repos:
        repoName = repo['name']
        r = gh.GetFile(repoName, '.gitignore')
        if r.ok and 'www-' in repoName:
            doc = json.loads(r.text)
            sha = doc['sha']
            content = base64.b64decode(doc['content']).decode()
            if not '_site' in content:
                content += '\n_site/\n'
                                
                r = gh.UpdateFile(repoName, '.gitignore', content, sha)
                if not r.ok:
                    print(f'Failed to update {repoName}: {r.text}\n')
                else:
                    print(f'Updated repo {repoName}\n')

def do_stripe_verify_recurring():
    users = []
    stripe.api_key = os.environ['STRIPE_SECRET']
    customers = stripe.Customer.list(limit=500)
    
    start_check = datetime(2019, 1, 1, 0, 0, 0, 0)
    end_check = datetime(2021, 4, 30, 23, 59, 59)

    count = 0
    cp = OWASPCopper()
    for customer in customers.auto_paging_iter():
        metadata = customer.get('metadata', None)
        if metadata and metadata.get('membership_type', None):
            endstr = metadata.get('membership_end', None)
            if endstr:
                mem_end_date = cp.GetDatetimeHelper(endstr) 
                if mem_end_date >= start_check and mem_end_date <= end_check:
                    subscriptions = stripe.Subscription.list(customer = customer.id)
                    for sub in subscriptions:
                        if sub.status == 'canceled' or sub.cancel_at_period_end:
                            recurring = metadata.get('membership_recurring', None)
                            if recurring == 'no':
                                searchres = mailchimp.search_members.get(query=f"email={customer.get('email')}", list_id=os.environ['MAILCHIMP_LIST_ID'])
                                members = searchres['full_search']['members']
                                for member in members:
                                    membership_recurring = member['merge_fields']['MEMRECUR']
                                    if membership_recurring == 'yes' and recurring == 'no': # we found a problem
                                        users.append(customer.get('email'))



    print(f"done: {users}")

def get_custom_field(fields, id):
    for field in fields:
        if field['custom_field_definition_id'] == id:
            return field['value']

    return None

def get_membership_data():
    start = time.time()

    member_data = { 'month':0, 'one':0, 'two':0, 'lifetime':0, 'student':0, 'complimentary':0, 'honorary':0 }
    cp = OWASPCopper()
    done = False
    page = 1
    today = datetime.today()

    while(not done):
        retopp = cp.ListOpportunities(page_number=page, status_ids=[1], pipeline_ids=[cp.cp_opportunity_pipeline_id_membership]) # all Won Opportunities for Individual Membership
        if retopp != '':
            opportunities = json.loads(retopp)
            if len(opportunities) < 200:
                done = True

            for opp in opportunities:
                end_val = get_custom_field(opp['custom_fields'], cp.cp_opportunity_end_date)
                if end_val != None:
                    end_date = datetime.fromtimestamp(end_val)
                    if end_date and end_date < today:
                        continue
                if end_val == None and 'lifetime' not in opp['name'].lower():
                    continue
                
                close_date = cp.GetDatetimeHelper(opp['close_date'])
                if close_date == None:
                    close_date = datetime.fromtimestamp(opp['date_created'])
                if close_date.month == today.month:
                    member_data['month'] = member_data['month'] + 1

                if 'student' in opp['name'].lower():
                    member_data['student'] = member_data['student'] + 1
                elif 'complimentary' in opp['name'].lower():
                    member_data['complimentary'] = member_data['complimentary'] + 1
                elif 'honorary' in opp['name'].lower():
                    member_data['honorary'] = member_data['honorary'] + 1
                elif 'one' in opp['name'].lower():
                    member_data['one'] = member_data['one'] + 1
                elif 'two' in opp['name'].lower():
                    member_data['two'] = member_data['two'] + 1
                elif 'lifetime' in opp['name'].lower():
                    member_data['lifetime'] = member_data['lifetime'] + 1

                #memrecurr = get_custom_field(opp['custom_fields'], cp.cp_opportunity_autorenew_checkbox)
                #primary_contact_id = opp['primary_contact_id']
                #person_json = cp.GetPerson(primary_contact_id)
                
                #customer_email = 'none'
                #customer_name = 'none'
                #if person_json != '':
                #    person = json.loads(person_json)
                #    if 'emails' in person:
                #        customer_email = person['emails']
                #    customer_name = person['name']
            page = page + 1
    total_members = member_data['student'] + member_data['complimentary'] + member_data['honorary'] + member_data['one'] + member_data['two'] + member_data['lifetime']

    msgtext = f"member total:{total_members}\tthis month:{member_data['month']}\n\tone:{member_data['one']}\ttwo:{member_data['two']}\n\tstudent:{member_data['student']}\tcomplimentary:{member_data['complimentary']}\n\tlifetime:{member_data['lifetime']}\thonorary:{member_data['honorary']}"
    end = time.time()
    print(msgtext + f"\n Time Taken: {end - start}")

def verify_membership():
    twofile = open('twoyears.txt', 'r')
    lines = twofile.readlines()
    total = len(lines)
    count = 0
    cp = OWASPCopper()
    for member in lines:
        opps = cp.FindOpportunities(member)
        found = False
        for opp in opps:
            topp = cp.GetOpportunity(opp['id'])
            if topp != None and 'Two' in topp['name']: # Good enough for now
                found = True
                break
        
        if not found:
            print(f"Member not found in Copper: {member}")
            count = count + 1
        
    print(f"Total Checked: {total}\nNot Found:{count}")

def do_fix_twoyear():
    # need to loop through Stripe customers
    # if membership_type = two and membership_recurring=yes
    # look up customer in mailchimp
    # update mailchimp to membership_recurring=no
    # update stripe to membership_recurring=no
    stripe.api_key = os.environ['STRIPE_SECRET']
    customers = stripe.Customer.list(limit=100)
    count = 0
    for customer in customers.auto_paging_iter():
        metadata = customer.get('metadata', None)
        if metadata and metadata.get('membership_type', None) == 'two' and metadata.get('membership_recurring', 'no') == 'yes':
            list_id = os.environ['MAILCHIMP_LIST_ID']
            email = customer.get('email').lower()
            stripe.Customer.modify(customer.id, metadata={'membership_recurring':'no'})
            searchres = mailchimp.search_members.get(query=f"{email}", list_id=list_id)
            members = searchres['exact_matches']['members']
            merge_fields = {}
            merge_fields['MEMRECUR'] = 'no'
            member_data = {
                "email_address": email,
                "status_if_new": "subscribed",
                "merge_fields": merge_fields
            }

            for member in members:
                subscriber_hash = hashlib.md5(email.encode('utf-8')).hexdigest()
                list_member = mailchimp.lists.members.create_or_update(os.environ['MAILCHIMP_LIST_ID'], subscriber_hash, member_data) # status_if_new is required and this may be more info than expected/needed
                count = count + 1
                print(f"Updating {count}", end="\r", flush=True)


def do_check_for_members(): # using Christian's 'not found' list, let's see if we can find a member...
    f = open('email-not-in-copper.txt', 'r')
    emails = f.readlines()
    cp = OWASPCopper()
    today = datetime.today()
    gh = OWASPGitHub()
    leaders = []
    r = gh.GetFile('owasp.github.io', '_data/leaders.json')
    if r.ok:
        doc = json.loads(r.text)
        content = base64.b64decode(doc['content']).decode()
        ldrobjs = json.loads(content)
        for leader in ldrobjs:
            leaders.append(leader['email'].lower())

    for email in emails:
        email = email.strip().lower()
        opp = cp.FindMemberOpportunity(email) # this will return an unexpired member opportunity if one exists....            
        if opp != None: # Good enough for now
            print(f'Found membership for {email}')
        
        if email in leaders:
            print(f'Found email in leaders list for {email}')
                
    print('Done')    

def add_email_to_stripe_if_not_exist(customer, owasp_email):
    try:
        metadata = customer.get('metadata', None)
        if metadata and not 'owasp_email' in metadata:
            print(f"{owasp_email} will be added to customer {customer['name']}")
            stripe.Customer.modify(customer.id, metadata={'owasp_email': owasp_email})
            print("Email added.")
        else:
            print('metadata is null or else owasp_email already exists')
    except:
        print('failure add_email_to_stripe_if_not_exist')
        pass

def find_owasp_email(member, cp):
    result = ''
    if member:
        for email in member['emails']:
            if '@owasp.org' in email['email']:
                return email
    
        og = OWASPGoogle()
        for email in member['emails']:
            user = og.GetUser(email['email'])
            if user:
                for email in user['emails']:
                    if '@owasp.org' in email['address']: # the user has a Google user but the email was not in Copper Member
                        cp.UpdatePerson(member['id'], other_email=email['address'])
                        return { 'email': email['address'] }

    return result

def update_stripe_with_owasp_email():
    # go through members...<-- what to use for this?  Copper?  Stripe?  Stripe is too slow, use Copper
    # get copper user
    # if copper user has an @owasp.org email address, update stripe owasp_email with address
    cp = OWASPCopper()
    members = cp.ListMembers(member_type='one') #lifetime, complimentary, student, two, one
    for member in members:
        stripe_customer = cp.GetCustomFieldHelper(cp.cp_person_stripe_number, member['custom_fields'])
        if stripe_customer != None:
            stripe.api_key = os.environ['STRIPE_SECRET']
            customer_id = stripe_customer
            if 'https' in stripe_customer:
                customer_id = stripe_customer[stripe_customer.rfind('/') + 1:]
            try:
                customer = stripe.Customer.retrieve(customer_id)
                metadata = customer.get('metadata', None)
                if metadata and not 'owasp_email' in metadata: # change to only query for email from Google if we do not know it....
                    print(f"No owasp email found in Stripe for {customer['name']}")
                    owasp_email = find_owasp_email(member, cp)
                    if owasp_email:
                        add_email_to_stripe_if_not_exist(customer, owasp_email['email'])
                    else:
                        print('No owasp email found')
            except Exception as e:
                print(f"Exception: {e}")
                pass
def get_membership_type(opp):
    memtype = 'Unknown'
    if 'Complimentary' in opp['name']:
        memtype = 'complimentary'
    elif 'One' in opp['name']:
        memtype = 'one'
    elif 'Two' in opp['name']:
        memtype = 'two'
    elif 'Lifetime' in opp['name']:
        memtype = 'lifetime'

    return memtype

def get_membership_start(opp):
    start = helperfuncs.get_datetime_helper(opp['close_date'])
    retstr = 'YYYY-mm-dd'
    if start != None:
        retstr = start.strftime('%Y-%m-%d')
    
    return retstr

def get_membership_end(cp, opp):
    end = helperfuncs.get_datetime_helper(cp.GetCustomFieldHelper(cp.cp_opportunity_end_date, opp['custom_fields']))
    endstr = ''
    if end != None:
        endstr = end.strftime('%Y-%m-%d')

    return endstr

def get_membership_recurring(cp, opp):
    retstr = 'no'
    if cp.GetCustomFieldHelper(cp.cp_opportunity_autorenew_checkbox, opp['custom_fields']):
        retstr = 'yes'

    return retstr

def fill_leader_details(memberinfo):
    gh = OWASPGitHub()
    r = gh.GetFile('owasp.github.io', '_data/leaders.json')
    leader_infos = []
    if r.ok:
        doc = json.loads(r.text)
        content = base64.b64decode(doc['content']).decode(encoding='utf-8')
        leaders = json.loads(content)
        for email in memberinfo['emails']:
            leader = next((sub for sub in leaders if sub['email'] == email['email']), None)
            if leader:
                leader_infos.append(leader)
        
        memberinfo['leader_info'] = leader_infos

    return memberinfo


def get_member_info(data):
    logging.info(data)
    emailaddress = data['email']
    today = datetime.today()
    member_info = {}
    cp = OWASPCopper()
    opp = None
    person = None
    opptxt = cp.FindMemberOpportunity(emailaddress)
    if opptxt != None:
        opp = json.loads(opptxt)
    pertext = cp.FindPersonByEmail(emailaddress)
    if pertext != '':
        people = json.loads(pertext)
        if len(people) > 0:
            person = people[0]

    if opp and person:
        member_info['membership_type'] = get_membership_type(opp)
        member_info['membership_start'] = get_membership_start(opp)
        member_info['membership_end'] = get_membership_end(cp, opp)
        member_info['membership_recurring'] = get_membership_recurring(cp, opp)
        member_info['name'] = person['name']
        member_info['emails'] = person['emails']
        member_info['address'] = person['address']
        member_info['phone_numbers'] = person['phone_numbers']
        member_info['member_number'] = cp.GetCustomFieldHelper(cp.cp_person_stripe_number, person['custom_fields'])
        member_info = fill_leader_details(member_info)
    elif not opp:
        logging.info(f"Failed to get opportunity")
    else:
        logging.info(f"Failed to get person")
        
    logging.info(f"Member information: {member_info}")
    return member_info         

def payments_match_years(customer, mem_type, years):
    if mem_type == 'complimentary' and years > 1:
        return False
    elif mem_type == 'complimentary':
        return True

    payment_intents = stripe.PaymentIntent.list(api_key=os.environ['STRIPE_SECRET'],customer=customer, limit=100)
    paycount = 0
    for pi in payment_intents.auto_paging_iter():
        descriptor = pi.get('statement_descriptor', None)
        purchase_type = None
        pi_metadata = pi.get('metadata', None)
        if pi_metadata:
            purchase_type = pi_metadata.get('purchase_type', None)
        if ((descriptor and 'MEMBERSHIP' in descriptor) or (purchase_type == 'membership')) and pi.status == 'succeeded':
            if mem_type == 'two':
                paycount += 2
            else:
                paycount += 1
                
    #Some subscriptions have invoices instead of payment_intents....
    invoices = stripe.Invoice.list(api_key=os.environ['STRIPE_SECRET'],customer=customer, limit=100)
    for inv in invoices.auto_paging_iter():
        lines = inv.get('lines', None)
        for line in lines:
            descriptor = line.get('description', None)
            if descriptor and 'Membership' in descriptor:
                if mem_type == 'two':
                    paycount += 2
                else:
                    paycount += 1

    return (paycount >= years)


def find_extended_enddate_members():
    check_list = []
    customers = stripe.Customer.list(api_key=os.environ['STRIPE_SECRET'], limit=100)
    count = 0
    for customer in customers.auto_paging_iter():
        count = count + 1
        print(f"Current: {count}, check_list size: {len(check_list)}", end="\r", flush=True)
        metadata = customer.get('metadata', None)
        if metadata and metadata.get('membership_type', None): #this is a member
            mem_type = metadata.get('membership_type')
            mem_end = metadata.get('membership_end', None)
            if mem_type == 'lifetime':
                continue # we are not looking at lifetime members

            if not mem_end: # should not happen except for lifetime members and we skip those
                print(f"Failed to retrieve membership end date for customer {customer.email}\n")
            else:
                memend_date = helperfuncs.get_datetime_helper(mem_end)
                today = datetime.today()
                years = memend_date.year - today.year
                if years > 0 and not payments_match_years(customer, mem_type, years):
                    check_list.append(customer.email + '\t' + mem_end + '\t' + mem_type + '\n') 
                
    with open('check_members.txt', 'w+') as f:
        f.writelines(check_list)

    print('check_members.txt written')            

def update_mailchimp_memend(email, end, marketing):
    searchres = mailchimp.search_members.get(query=f"{email}", list_id=os.environ['MAILCHIMP_LIST_ID'])
    members = searchres['exact_matches']['members']
    merge_fields = {}
    merge_fields['MEMEND'] = end
    member_data = {
        "email_address": email,
        "status_if_new": "subscribed",
        "status": "subscribed",
        "merge_fields": merge_fields,
        "marketing_permissions": [{ "marketing_permission_id": os.environ["MAILCHIMP_MKTG_PERMISSIONS_ID"], "enabled": marketing }]
    }

    for member in members:
        subscriber_hash = hashlib.md5(email.encode('utf-8')).hexdigest()
        try:
            mailchimp.lists.members.create_or_update(os.environ['MAILCHIMP_LIST_ID'], subscriber_hash, member_data) # status_if_new is required and this may be more info than expected/needed
        except MailChimpError as me:
            if 'Compliance' in me.args[0]['title']:
                continue                
        

def update_subscription_members():
    subs = stripe.Subscription.list(api_key=os.environ['STRIPE_SECRET'])
    count = 0
    for sub in subs.auto_paging_iter():
        if sub['status'] == 'active' or sub['status'] == 'trialing':
            metadata = sub.get('metadata', None)
            if metadata and metadata.get('purchase_type', None) == 'membership':
                mem_end = datetime.utcfromtimestamp(sub['current_period_end']).strftime("%m/%d/%Y")
                mem_end_date = helperfuncs.get_datetime_helper(mem_end)
                customer = stripe.Customer.retrieve(sub['customer'], api_key=os.environ['STRIPE_SECRET'])
                custmeta = customer.get('metadata', None)
                cmem_end = custmeta.get('membership_end', None)
                if cmem_end:
                    cmem_end_date = helperfuncs.get_datetime_helper(custmeta['membership_end'])
                    if custmeta and mem_end_date.year > cmem_end_date.year:       
                        mailing_list = metadata.get('mailing_list', 'False')
                        market = False
                        if mailing_list == 'True':
                            market = True                 
                        update_mailchimp_memend(customer.email.lower(), mem_end, market)
                        cp = OWASPCopper()
                        
                        opp = cp.FindMemberOpportunity(customer.email)
                        jperson = cp.FindPersonByEmail(customer.email)
                        person = None
                        if jperson and jperson != '':
                            person = json.loads(jperson)[0]

                        if opp == None and person:
                            custmeta['membership_end'] = mem_end
                            if 'membership_start' not in custmeta:
                                custmeta['membership_start'] = datetime.utcfromtimestamp(sub['start_date']).strftime("%m/%d/%Y")
                            cp.CreateOWASPMembership(person['id'], customer.name, customer.email, custmeta)
                        stripe.Customer.modify(customer.id, metadata={ "membership_end": mem_end }, api_key=os.environ['STRIPE_SECRET'])
        count = count + 1

    print(f"Done with {count} subscriptions.")

def main():
    #do_stripe_verify_recurring()

    google = OWASPGoogle()
    users = google.GetAllUsers('brian.mcgroarty@owasp.org')
    print(users)
    
    #find_extended_enddate_members()    
    # These were done 7.29.2021
    #import_members('2021-appsec-us-member-import.csv')
    
    # cp = OWASPCopper()
    # opp = cp.FindMemberOpportunity('ervin.hegedus@owasp.org')
    # print(opp)
    # DetectStripeMembershipNotInCopper()

    #update_www_repos_site()
    # update_subscription_members()
    # update_www_repos_site()
    # customers = stripe.Customer.list(email="harold.blankenship@owasp.com", api_key=os.environ['STRIPE_SECRET'])
    # for customer in customers.auto_paging_iter():
    #     stripe.Customer.modify(
    #             customer.id,
    #             metadata={
    #                 "membership_notified": "",
    #                 "membership_notified_date": "",
    #                 "membership_last_notification": ""
    #             },
    #             api_key=os.environ["STRIPE_SECRET"]
    #         )

    
    #gh = OWASPGitHub()
    #repos = gh.GetPublicRepositories('www-chapter-')
    #for repo in repos:
    #     if 'miami' in repo['name'] or 'kuala' in repo['name'] or 'jose' in repo['name']:
    #         print(repo['name'])

    #create_community_events(OWASPGitHub(), OWASPMeetup())
    # google = OWASPGoogle()
    # files = google.GetUserFiles('harold.blankenship@owasp.org')
    # for file in files:
    #     if('.jpg' in file['name']):
    #         request = google.drive.files().get_media(fileId=file['id'])
    #         fh = io.BytesIO()
    #         downloader = MediaIoBaseDownload(fh, request)
    #         done = False
    #         while done is False:
    #             status, done = downloader.next_chunk()
    #             print("Download %d%%." % int(status.progress() * 100))

    #         with open(file['name'], "wb") as outfile:
    #             outfile.write(fh.getbuffer())
    # print('done')
    #data = { 'email': 'harold.blankenship@owasp.org' }
    #print(get_member_info(data))
    
    # Next Question: how to get class data for members?

    # Also update chapters to show # of meetings in last 12 months....


    #update_customer_metadata_null()

    #do_check_for_members()

    #cop = OWASPCopper()
    #print(cop.FindPersonByEmail("nicole@geekymoms.com"))
    #update_stripe_with_owasp_email()

    # og = OWASPGoogle()
    # user = og.GetUser('aaron.blankenbeker@gmail.com')
    # print(user)

    #do_fix_twoyear()
    # cp = OWASPCopper()
    # opp = json.loads(cp.FindMemberOpportunity('harold.blankenship@owasp.org'))
    # print(f"Opportunity: {opp}")
    # pers = cp.FindPersonByEmail('harold.blankenship@owasp.org')
    # if len(pers) > 0:
    #     print(f"Person: {json.loads(pers)[0]}")

    #membership_data = {
    #    'membership_type':'one',
    #    'membership_start': '2018-01-19',
    #    'membership_end': '2023-03-03',
    #    'membership_recurring': 'no'
    #}

    #gu = OWASPGoogle()
    #gu.UpdateUserData('harold.blankenship@owasp.org', membership_data)
    #gu.CreateEmailAddress('harold.blankenship@owasp.org', 'harold', 'blankenship')
    #str = "\ud83e\uddb8\ud83c\udffc\u200d\u2640\ufe0f\ud83e\uddb8\ud83e\uddb8\ud83c\udffd\u200d\u2642\ufe0f Return of The Security Champions! Ep. 2 [en,jitsi,yt,ch]"
    #print(deEmojify(str))

    #verify_membership()

    #get_membership_data()

    #do_stripe_verify_recurring()
    
    #update_www_repos_main()

    # trying to figure out what Top 10 Card Game not in repos...
    #gh = OWASPGitHub()
    #projects = gh.GetPublicRepositories(matching="www-project-")
    #for project in projects:
    #    if 'card' in project['url']:
    #        print(project)
    # first_name = 'Cartêgeña'
    # last_name = "d'Oros"

    # nfn = unicodedata.normalize('NFD', first_name)
    # nln = unicodedata.normalize('NFD', last_name)
    # nfn = ''.join([c for c in nfn if not unicodedata.combining(c)])
    # nln = ''.join([c for c in nln if not unicodedata.combining(c)])
    # r2 = re.compile(r'[^a-zA-Z0-9]')
    # first_name = r2.sub('',nfn)
    # last_name = r2.sub('', nln)

    # print(first_name + '.' + last_name + '@someother.edu')

    
    #get_docusign_docs()

    #ipaddrs = ['123.45.234.33:5555']
    #ipaddr = ipaddrs[0][:ipaddrs[0].find(':')]
    #print(ipaddr)

    # customer_name = "Yang Ju Ryul"
    # first_name = customer_name.lower().strip().split(' ')[0]
    # last_name = ''.join((customer_name.lower() + '').split(' ')[1:]).strip()

    # if first_name != None and last_name != None:
    #     og = OWASPGoogle()
    #     preferred_email = first_name + '.' + last_name + '@owasp.org'
    #     email_list = og.GetPossibleEmailAddresses(preferred_email)

    #     print(email_list)
    #verify_cleanup('customers_1.csv')

    #AddStripeMembershipToCopper()
    # copper = OWASPCopper()
    # pjson = copper.FindPersonByEmail('harold.blankenship@owasp.com')
    # person = json.loads(pjson)[0]
    # memend = datetime.fromtimestamp(copper.GetCustomFieldHelper(copper.cp_person_membership_end, person['custom_fields']))
    # print(memend)

    #create_zoom_account('www-projectchapter-example')
    #og = OWASPGoogle()
    #og.AddMemberToGroup('leaders-zoom-one@owasp.org', 'example-leaders@owasp.org', 'MEMBER', 'GROUP')
    #zoom_accounts = ['leaders-zoom-one@owasp.org', 'leaders-zoom-two@owasp.org', 'leaders-zoom-three@owasp.org', 'leaders-zoom-four@owasp.org']
    #print(retrieve_member_counts(zoom_accounts))
    #leaders = ['harold.blankenship@owasp.com']
    #send_onetime_secret(leaders, 'ThisIsMyGroup')
    #oz = OWASPZoom()
    #print(oz.GetUser('INl4oy6fQ4aojKSqUSMylA'))
    #gh = OWASPGitHub()
    #build_leaders_json(gh)

    #leaders = gh.GetLeadersForRepo('www-chapter-austin')
    #print(leaders)
    #og = OWASPGoogle()
    #jsonobj = og.GetGroupMembers('leaders-zoom-one@owasp.org')
    #print(len(jsonobj['members']))
    #print(og.GetGroupSettings('baltimore-leaders@owasp.org'))
    #create_zoom_account('www-projectchapter-example')
    #oj = OWASPJira()
    #print(oj.CreateDropDownField().text)

    #customer = { 'name':'John von Hosenshertz III'}
    #first_name = customer['name'].lower().strip().split(' ')[0]
    #last_name = ''.join((customer['name'].lower() + '').split(' ')[1:]).strip()

    #print(first_name + '.' + last_name + '@owasp.org'
    # response_str = "harold@owasp.org"
    # response = {
    #         "status": "ERROR",
    #         "errors": response_str
    #     }

    # obj = json.dumps(response)
    # print(obj)MANAGER'
    #og = OWASPGoogle()
    #print(og.GetPossibleEmailAddresses('harold.blankenship@owasp.org'))
    #print(og.CreateEmailAddress("kithwood@gmail.com", "harold", "test2"))

    #import_members('gappsec_members_9.30.2020.csv')

    # cp = OWASPCopper()
    # person = cp.FindPersonByEmail('plupiani@bcgeng.com')
    # print(person)
    # person = cp.FindPersonByEmail('pluplupiani@bcgeng.com')
    # print(person)
    # persons = cp.ListMembers()
    # for person in persons:
    #     print(person)
    #     print('\n----------------------------------\n')
    # print(len(persons))

    #add_users_to_repos()

    #create_chapter_events(OWASPGitHub(), OWASPMeetup())
    #create_community_events(gh, mu)
    #chapterreport.do_chapter_report()
    #rebuild_milestones.build_staff_project_json()
    #with open('meetup_results.txt', 'w+') as outfile:
    #    add_chapter_meetups(gh, mu, outfile)

    # mu = OWASPMeetup()
    # if mu.Login():
    #     print(mu.GetGroupEvents('OWASP-London'))

    # with open('members_emails.txt', 'r') as f:
    #     lines = f.readlines()
    #     for emailaddr in lines:
    #         stripe.api_key = os.environ['STRIPE_SECRET']
    #         customers = stripe.Customer.list(email=emailaddr.strip())
    #         if not customers.is_empty:
    #             customer = customers.data[0]
    #             metadata = customer.get('metadata', {})

    #             membership_type = metadata.get('membership_type', None)
    #             if membership_type and membership_type != 'lifetime':
    #                 mendstr = metadata.get('membership_end', None)
    #                 if mendstr != None:
    #                     mend = datetime.datetime.strptime(mendstr, "%m/%d/%Y")
    #                 else:
    #                     mend = None

    #                 if mend and mend >= datetime.datetime.now():
    #                     print('membership verified')
    #                 else:
    #                     print(f'membership ended: {mend}')
    #             elif membership_type == 'lifetime':
    #                 print('membership verified')
    #             else:
    #                 print(f'not a member with email {emailaddr.strip()}')
    #         else:
    #             print(f'not a member with email {emailaddr.strip()}')


    # test = time.time()
    # key = Fernet.generate_key()
    # f = Fernet(key)
    # token = f.encrypt(b"my deep dark secret")
    # #print(token)
    # result = f.decrypt(token)
    # print(time.time() - test)

    # test = time.time()
    # token = encrypt("sdfh88sfhe90sd8700sd9f8", "my deep dark secret")
    # #print(token)
    # result = decrypt("sdfh88sfhe90sd8700sd9f8", token)
    # print(time.time() - test)


   # DoCopperCreate()
   #cp = OWASPCopper()
   #pid = cp.CreatePerson('Jay Tester', 'tester@test.owasp.com')

    #r = cp.ListProjects()
    #r = cp.ListOpportunities()
    # r = cp.FindPersonByName('Blank')
    #r = cp.FindPersonByEmail('harold.blankenship@owasp.com')
    #person = json.loads(r)
    #print(person[0]['id'])
    #r = cp.CreateOpportunity('Test Opportunity', 'harold.blankenship@owasp.com')
    #print(r)
    
    #r = cp.GetProject('Chapter - Los Angeles')
    #print(r)
    #GetContactInfo()
    # ans = 'y' if 'yes' in ['no','maybe'] else 'n'
    # print(ans)
    #gh = OWASPGitHub()
    #repos = gh.GetPublicRepositories('www-chapter', inactive=True)

    #print(repos)
    #build_inactive_chapters_json(gh)

    #build_chapter_json(OWASPGitHub())

    #CollectMailchimpTags()
    #build_staff_project_json()
    #r = gh.GetPages("www-chapter-louisville")
    #print(r)
    #print('\n')
    #r = gh.GetPages("www-project-zap")
    #print(r)
    #print('\n')
    #add_leaders()
    #sf = OWASPSalesforce()
    #if sf.Login().ok:
    #    res = sf.FindContact('Berman')

    #print(res)
    #MigrateProjectPages()membership_typeeRepositoryPages(group, grouptype)
    # if github.TestResultCode(r.status_code):
    #     r = github.EnablePages(group, grouptype)

    # if github.TestResultCode(r.status_code):
    #     print("Done")
    # else:
    #     print(r.text)
    #create_all_pages()
    #update_project_pages()

    # update_chapter_pages()
    # gtype = 'United States'
    # teststr = '---\n\ntext1: john\ntext2: steven\ntext3:homer\n\n---\n\n'
    # front_ndx = teststr.find("---", teststr.find("---") + 3)
    # content = teststr[:front_ndx] + 'region: ' + gtype + '\n\n' + teststr[front_ndx:]
    # print(content)

    #gh = OWASPGitHub()
    #repos = gh.GetPublicRepositories('www-project')
    # repos.sort(key=lambda x: x['name'])
    # repos.sort(key=lambda x: x['level'], reverse=True)

    # for repo in repos:
    #     repo['name'] = repo['name'].replace('www-project-','').replace('-', ' ')
    #     repo['name'] = " ".join(w.capitalize() for w in repo['name'].split())

    # sha = ''
    # r = gh.GetFile('owasp.github.io', '_data/projects.json')
    # if gh.TestResultCode(r.status_code):
    #     doc = json.loads(r.text)
    #     sha = doc['sha']

    # contents = json.dumps(repos)
    # r = gh.UpdateFile('owasp.github.io', '_data/projects.json', contents, sha)
    # if gh.TestResultCode(r.status_code):
    #     print('Success!')
    # else:
    #     print(f"Failed: {r.text}")

main()
