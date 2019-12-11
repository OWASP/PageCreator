# page-creator
# Tool used for creating chapter and project pages
# for OWASP Community

import requests
import json
from github import *
import base64
import datetime
from wufoo import *
from salesforce import *
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
        self.status = 'on-time'

    def SetDescription(self, desc):
        self.description = desc

    def SetOwner(self, owner):
        self.owner = owner

    def SetProjectName(self, pname):
        self.project_name = pname
    
    def SetProjectStatus(self, status):
        self.status = status

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

    if sndx > 0 and endx > sndx + 10:
        desc = milestone[sndx + 10:endx]
    desc = desc.strip(',')
    desc = desc.rstrip(',')
    desc = desc.strip()
    return desc

def get_milestone_parts(milestone):
    owner = ''
    desc = ''
    date = get_milestone_date(milestone)
    if date:
        owner = get_milestone_owner(milestone)
        desc = get_milestone_desc(milestone)

    return date, owner, desc

def get_milestone_status(date):
    status = 'on-time'
    d = datetime.date(*(int(s) for s in date.split('-')))
    td = datetime.date.today()
    delta = d - td
    if delta.days <= -5:
        status = 'overdue'
    elif delta.days > 30:
        status = 'future'


    return status

def get_project_milestones(content, pname):
    milestones = []
    sndx = content.find('Milestones') + 10
    endx = content.find('##', sndx)
    if sndx == -1:
        return milestones

    milestr = content[sndx:endx]
    milestr = milestr.replace('\n','')
    milestr = milestr.replace('- [', '* [')
    
    if not milestr.startswith('*'):
        milestr = milestr.replace('[ ]', '* [ ]')
        milestr = milestr.replace('[x]', '* [x]')

    mls = milestr.split('*')
    for ms in mls:
        if '[x]' in ms:
            continue
        ms = ms.replace('[ ]', '')
        date, owner, desc = get_milestone_parts(ms)
        if date:
            milestone = Milestone(date)
            milestone.owner = owner
            milestone.description = desc
            milestone.project_name = pname
            milestone.status = get_milestone_status(date)
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

def main():
    #sf = OWASPSalesforce()
    #if sf.Login().ok:
    #    res = sf.FindContact('Berman')

    #print(res)
    #MigrateProjectPages()
    MigrateChapterPages()

    #CreateProjectPageList()
    #MigrateSelectedPages('attack_files.txt')
    #MigrateSelectedPages('vuln_files.txt')
    #AddChaptersToChapterTeam()
    
    #build_staff_project_json()
    #print('Hello')
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
