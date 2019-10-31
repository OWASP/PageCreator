# page-creator
# Tool used for creating chapter and project pages
# for OWASP Community

import requests
import json
from github import *
import base64
import datetime

class Leader:
    def __init__(self, name, email):
        self.name = name
        self.email = email

class Milestone:
    def __init__(self, strdate):
        self.milestone_date = strdate
        self.description = ''
        self.owner = ''
        self.project_name = ''

    def SetDescription(self, desc):
        self.description = desc

    def SetOwner(self, owner):
        self.owner = owner

    def SetProjectName(self, pname):
        self.project_name = pname

class StaffProject:
    def __init__(self, name):
        self.name = name
        self.milestones = []
        self.description = ''
        self.leaders = []
        self.url = ''

    def AddMilestone(self, milestone):
        milestone.SetProjectName(self.name)
        self.milestones.append(milestone)

    def AddLeader(self, leader):
        self.leaders.append(leader)

    def SetDescription(self, desc):
        self.description = desc

    def SetUrl(self, url):
        self.url = url

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

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

def get_page_name(content):
    name = ''
    sndx = content.find('title:') + 7
    endx = content.find('\n', sndx)
    if sndx > -1:
        name = content[sndx:endx]
    return name

def get_project_description(content):
    desc = ''
    sndx = content.find('Overview') + 8
    if sndx > -1:
        endx = content.find('##', sndx)
        desc = content[sndx:endx]
        desc = desc.replace('\n','')
        desc = desc.strip()

    return desc

def get_project_leaders(content):
    leaders = []
    
    sndx = content.find('Leadership') + 10
    endx = content.find('##', sndx)
    if sndx == -1:
        return leaders

    leaderstr = content[sndx:endx]
    leaderstr = leaderstr.replace('\n','')
    ldrs = leaderstr.split('*')
    for ldr in ldrs:
        ndx = ldr.find('[')
        if ndx > -1:
            name = ldr[ndx + 1:]
            name = name[:name.find(']'):]
            name = name.replace('- Lead', '')
            mndx = ldr.find('(mailto:')
            mail = ''
            if mndx > -1:
                mail = ldr[mndx + 8:]
                mail = mail[:mail.find(')')]
                mail = mail[:mail.find('?')]
            if name:
                leader = Leader(name, mail)
                leaders.append(leader)

    return leaders

def get_milestone_date(milestone):
    date = ''
    ndx = milestone.find(' ') + 1
    if ndx > -1:
        date = milestone[ndx:ndx + 11] # date must be in format 2020-01-01
        date = date.strip()
        dateparts = []
        if date:
            dateparts = date.split('-')
        try:
            int(dateparts[0])
            int(dateparts[1])
            int(dateparts[2])
        except Exception:
            date = '' #invalid date for milestone
            pass

    return date.strip()

def get_milestone_owner(milestone):
    owner = ''
    milestone = milestone.replace('\n','')
    milestone = milestone.strip()
    ndx = milestone.rfind(']') #aside from \n or spaces this should be the last character
    if ndx == len(milestone) -1:
        sndx = milestone.rfind('[') + 1
        if sndx > 0:
            owner = milestone[sndx:ndx]
            owner = owner.strip()
    lowner = owner.lower()
    if not owner or 'completed' in lowner or 'done' in lowner:
        owner = 'No Owner'

    return owner.strip()

def get_milestone_desc(milestone):
    desc = ''
    sndx = milestone.find(' ') + 1 # start of date
    milestone = milestone.replace('\n','')
    milestone = milestone.strip()
    endx = milestone.rfind(']') #aside from \n or spaces this should be the last character
    if endx == len(milestone) -1:
        endx = milestone.rfind('[') # start of 'owner'
    else:
        endx = len(milestone)

    if sndx > 0 and endx > sndx + 11:
        desc = milestone[sndx + 11:endx]
    desc = desc.strip()
    desc = desc.rstrip(',')
    return desc

def get_milestone_parts(milestone):
    owner = ''
    desc = ''
    date = get_milestone_date(milestone)
    if date:
        owner = get_milestone_owner(milestone)
        desc = get_milestone_desc(milestone)

    return date, owner, desc


def get_project_milestones(content, pname):
    milestones = []
    sndx = content.find('Milestones') + 10
    endx = content.find('##', sndx)
    if sndx == -1:
        return milestones

    milestr = content[sndx:endx]
    milestr = milestr.replace('\n','')
    if milestr.startswith('*'):
        milestr = milestr.replace('[ ]','')
        milestr = milestr.replace('[x]', '')
    else:
        milestr = milestr.replace('[ ]', '*')
        milestr = milestr.replace('[x]', '*')

    mls = milestr.split('*')
    for ms in mls:
        date, owner, desc = get_milestone_parts(ms)
        if date:
            milestone = Milestone(date)
            milestone.owner = owner
            milestone.description = desc
            milestone.project_name = pname
            milestones.append(milestone)
                    
    return milestones

def build_staff_milestone_json(projects):
    gh = OWASPGitHub()
    milestones = []
    for project in projects:
        for milestone in project.milestones:
            milestones.append(milestone)

    milestones.sort(key=lambda x: x.milestone_date)
    contents = json.dumps(milestones, default=lambda x: x.__dict__, indent=4)
    r = gh.GetFile('www-staff', '_data/milestones.json')
    sha = ''
    if gh.TestResultCode(r.status_code):
        doc = json.loads(r.text)
        sha = doc['sha']
    r = gh.UpdateFile('www-staff', '_data/milestones.json', contents, sha)
    if gh.TestResultCode(r.status_code):
        print('Updated www-staff/_data/milestones.json successfully')
    else:
        print(f"Failed to update www-staff/_data/milestones.json: {r.text}")

def build_staff_project_json():
    gh = OWASPGitHub()
    repo = 'www-staff'
    path = 'projects'

    files = []
    r, rfiles = gh.GetFilesMatching(repo, path, '')
    if gh.TestResultCode(r.status_code):
        files = files + rfiles
    else: 
        print(f'Failed to get files: {r.text}')
        
    projects = []
    for pfile in files:
        if '-template.md' in pfile:
            continue
        r = gh.GetFile('www-staff', f'projects/{pfile}')
        sha = ''
        if gh.TestResultCode(r.status_code):
            doc = json.loads(r.text)
            content = base64.b64decode(doc['content']).decode()
            name = get_page_name(content)
            if name:
                project = StaffProject(get_page_name(content))
                project.url = f"https://www2.owasp.org/www-staff/projects/{pfile.replace('.md','')}"
                project.description = get_project_description(content)
                project.leaders = get_project_leaders(content)
                project.milestones = get_project_milestones(content, project.name)
                projects.append(project)
        else:
            print(f'Failed to get {pfile}:{r.text}')

    contents = json.dumps(projects, default=lambda x: x.__dict__, indent=4)
    
    build_staff_milestone_json(projects)

    r = gh.GetFile('www-staff', '_data/projects.json')
    sha = ''
    if gh.TestResultCode(r.status_code):
        doc = json.loads(r.text)
        sha = doc['sha']
    r = gh.UpdateFile('www-staff', '_data/projects.json', contents, sha)
    if gh.TestResultCode(r.status_code):
        print('Updated www-staff/_data/projects.json successfully')
    else:
        print(f"Failed to update www-staff/_data/projects.json: {r.text}")

def main():
    build_staff_project_json()

    # github = OWASPGitHub()
    # group = "deepviolet-tls-ssl-scanner"
    # grouptype = 0
    # r = github.InitializeRepositoryPages(group, grouptype)
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

    # gh = OWASPGitHub()
    # repos = gh.GetPublicRepositories('www-project')
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
