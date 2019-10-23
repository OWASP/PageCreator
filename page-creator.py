# page-creator
# Tool used for creating chapter and project pages
# for OWASP Community

import requests
import json
from github import *
import base64

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

def main():
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

    update_chapter_pages()
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