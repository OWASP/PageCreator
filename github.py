import requests
import json
import base64
from pathlib import Path
import os
import datetime

class OWASPGitHub:
    apitoken = os.environ["GH_APITOKEN"]
    user = "harold.blankenship@owasp.com"
    gh_endpoint = "https://api.github.com/"
    org_fragment = "orgs/OWASP/repos"
    repo_fragment = "repos/OWASP/:repo"
    commit_fragment = "repos/OWASP/:repo/commits"
    content_fragment = "repos/OWASP/:repo/contents/:path"
    pages_fragment = "repos/OWASP/:repo/pages"
    team_addrepo_fragment = "teams/:team_id/repos/OWASP/:repo"
    team_getbyname_fragment = "orgs/OWASP/teams/:team_slug"
    
    of_org_fragment = "orgs/OWASP-Foundation/repos"
    of_content_fragment = "repos/OWASP-Foundation/:repo/contents/:path"
    of_pages_fragment = "repos/OWASP-Foundation/:repo/pages"
    of_team_addrepo_fragment = "teams/:team_id/repos/OWASP-Foundation/:repo"
    of_team_getbyname_fragment = "orgs/OWASP-Foundation/teams/:team_slug"
    
    user_fragment = "users/:username"
    collaborator_fragment = "repos/OWASP/:repo/collaborators/:username"

    def CreateRepository(self, repoName, rtype):
        repoName = self.FormatRepoName(repoName, rtype)
        description = "OWASP Foundation Web Respository"
        data = { 
              "repo" : repoName, 
            "description": description
        }

        headers = {"Authorization": "token " + self.apitoken}
        r = requests.post(url = self.gh_endpoint + self.org_fragment, headers = headers, data=json.dumps(data))

        return r

    def InitializeRepositoryPages(self, repoName, rtype):
        groupName = repoName
        repoName = self.FormatRepoName(repoName, rtype)
        url = self.gh_endpoint + self.content_fragment
        url = url.replace(":repo", repoName)
        # change to use files.json....
        sfile = open("files.json")
        filestosend = json.load(sfile)
        for f in filestosend["files"]:
            r = self.SendFile( url, f['path'], "[GROUPNAME]", groupName)
            if not self.TestResultCode(r.status_code):
                break

        return r

    def SendFile(self, url, filename, replacetag = None, replacestr = None):
        pathname = filename.replace("docs/", "")
        url = url.replace(":path", pathname)
        sfile = open(filename)
        filecstr = sfile.read()
        if replacetag and replacestr:
            filecstr = filecstr.replace(replacetag, replacestr)

        bytestosend = base64.b64encode(filecstr.encode())   
        committer = {
            "name" : "OWASP Foundation",
            "email" : "owasp.foundation@owasp.org"
        }
        data = {
            "message" : "initialize repo",
            "committer" : committer,
            "content" : bytestosend.decode()
        }
        headers = {"Authorization": "token " + self.apitoken}
        r = requests.put(url = url, headers=headers, data=json.dumps(data))
        return r

    def EnablePages(self, repoName, rtype):
        headers = {"Authorization": "token " + self.apitoken,
            "Accept":"application/vnd.github.switcheroo-preview+json, application/vnd.github.mister-fantastic-preview+json, application/json"
        }
        repoName = self.FormatRepoName(repoName, rtype)
        url = self.gh_endpoint + self.pages_fragment
        url = url.replace(":repo", repoName)

        data = { "source" : { "branch" : "master" }}
        r = requests.post(url = url, headers=headers, data=json.dumps(data))

        return r

    def TestResultCode(self, rescode):
        if rescode == requests.codes.ok or rescode == requests.codes.created:
            return True

        return False

    def FormatRepoName(self, repoName, rtype):
        repoName = repoName.lower()
        repoName = repoName.replace('owasp', '')
        repoName = repoName.replace('project', '')
        repoName = repoName.strip()
        resName = ""
        if rtype == 0:
            resName = "www-project-"
        else:
            resName = "www-chapter-"
    
        return resName + repoName.replace(" ", "-").lower()


    def RebuildSite(self):
        headers = {"Authorization": "token " + self.apitoken,
            "Accept":"application/vnd.github.switcheroo-preview+json, application/vnd.github.mister-fantastic-preview+json, application/json, application/vnd.github.baptiste-preview+json"
        }
        
        done = False
        pageno = 1
        pageend = -1
        
        while not done:
            pagestr = "?page=%d" % pageno
            url = self.gh_endpoint + self.org_fragment + pagestr
            r = requests.get(url=url, headers = headers)
            
            if self.TestResultCode(r.status_code):
                repos = json.loads(r.text)
                if pageend == -1:
                    endlink = r.links["last"]["url"]
                    pageend = int(endlink[endlink.find("?page=") + 6:])
                
                if pageno == pageend:
                    done = True
                
                pageno = pageno + 1
                #repos = {"www--site-theme", "owasp.github.io", "www-project-zap"}
                for repo in repos:
                    repoName = repo["name"].lower()
                    istemplate = repo["is_template"]
                    print("checking " + repoName + "\n")
                    if not istemplate and (repoName.startswith("www-project") or repoName.startswith("www-chapter") or repoName.startswith("www--") or repoName.startswith("owasp.github")):
                        print("rebuilding " + repoName + "\n")
                        url = self.gh_endpoint + self.pages_fragment
                        url = url.replace(":repo",repoName)
                        r = requests.post(url = url + "/builds", headers=headers)

        return r

    def GetFile(self, repo, filepath, content_fragment = "repos/OWASP/:repo/contents/:path"):
        url = self.gh_endpoint + content_fragment
        url = url.replace(":repo", repo)
        url = url.replace(":path", filepath)
        
        headers = {"Authorization": "token " + self.apitoken}
        r = requests.get(url = url, headers=headers)
        return r

    def GetOFFile(self, repo, filepath):
        return self.GetFile(repo, filepath, self.of_content_fragment)

    def DeleteFile(self, repo, filepath):
        url = self.gh_endpoint + self.content_fragment
        url = url.replace(":repo", repo)
        url = url.replace(":path", filepath)

        committer = {
            "name" : "OWASP Foundation",
            "email" : "owasp.foundation@owasp.org"
        }
        headers = {"Authorization": "token " + self.apitoken}
        r = requests.delete(url = url, headers=headers)
        return r

    def UpdateFile(self, repo, filepath, contents, sha):
        url = self.gh_endpoint + self.content_fragment
        url = url.replace(":repo", repo)
        url = url.replace(":path", filepath)

        bytestosend = base64.b64encode(contents.encode())   
        committer = {
            "name" : "OWASP Foundation",
            "email" : "owasp.foundation@owasp.org"
        }
        data = {
            "message" : "remote update file",
            "committer" : committer,
            "content" : bytestosend.decode(),
            "sha" : sha
        }
        headers = {"Authorization": "token " + self.apitoken}
        r = requests.put(url = url, headers=headers, data=json.dumps(data))
        return r

    def GetPages(self, repoName):
        headers = {"Authorization": "token " + self.apitoken,
            "Accept":"application/vnd.github.switcheroo-preview+json, application/vnd.github.mister-fantastic-preview+json, application/json, application/vnd.github.baptiste-preview+json"
        }
        result = ''
        url = self.gh_endpoint + self.pages_fragment
        url = url.replace(':repo', repoName)
        r = requests.get(url=url, headers = headers)
        if r.ok:
            result = json.loads(r.text)
        
        return result
        

    def GetInactiveRepositories(self, matching=""):
       return self.GetPublicRepositories(matching=matching, inactive=True)

    def GetPublicRepositories(self, matching="", inactive=False):
        headers = {"Authorization": "token " + self.apitoken, "X-PrettyPrint":"1",
            "Accept":"application/vnd.github.switcheroo-preview+json, application/vnd.github.mister-fantastic-preview+json, application/json, application/vnd.github.baptiste-preview+json"
        }
        
        done = False
        pageno = 1
        pageend = -1
        
        results = []
        while not done:
            pagestr = "?page=%d" % pageno
            url = self.gh_endpoint + self.org_fragment + pagestr
            r = requests.get(url=url, headers = headers)
            
            if self.TestResultCode(r.status_code):
                repos = json.loads(r.text)
                if pageend == -1:
                    endlink = r.links['last']['url']
                    pageend = int(endlink[endlink.find('?page=') + 6:])
                
                if pageno == pageend:
                    done = True
                
                pageno = pageno + 1
                
                for repo in repos:
                    repoName = repo['name'].lower()
                    istemplate = repo['is_template']
                    haspages = repo['has_pages'] #false for Iran...maybe was never activated?
                        
                    if not matching or matching in repoName:
                        if not istemplate:
                            pages = None
                            if haspages:
                                pages = self.GetPages(repoName)
                            if (not pages or pages['status'] == None) and not inactive:
                                continue
                            elif (pages and pages['status'] != None) and inactive:
                                continue
                        else:
                            continue
                        addrepo = {}
                        addrepo['name'] = repoName
                        addrepo['url'] = f"https://owasp.org/{ repoName }/"
                    
                        cdate = datetime.datetime.strptime(repo['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                        udate = datetime.datetime.strptime(repo['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
                        addrepo['created'] = cdate.strftime('%c')
                        addrepo['updated'] = udate.strftime('%c')
                        r = self.GetFile(repoName, 'index.md')
                        if self.TestResultCode(r.status_code):
                            doc = json.loads(r.text)
                            content = base64.b64decode(doc['content']).decode()
                            ndx = content.find('title:')
                            eol = content.find('\n', ndx + 7)
                            if ndx >= 0:
                                title = content[ndx + 7:eol]
                                addrepo['title'] = title.strip()
                            else:
                                addrepo['title'] = repoName
                                
                            ndx = content.find('level:') + 6
                            eol = content.find("\n", ndx)
                            not_updated = (content.find("This is an example of a Project") >= 0)
                            if ndx < 0 or not_updated:
                                level = "-1"
                            else:
                                level = content[ndx:eol]
                            addrepo['level'] = level.strip() 
                            ndx = content.find('type:') + 5
                            eol = content.find("\n", ndx)
                            gtype = content[ndx:eol]
                            addrepo['type'] = gtype.strip()
                            ndx = content.find('region:') + 7
                            
                            if not_updated:
                                gtype = 'Needs Website Update'
                            elif ndx > 6: # -1 + 7
                                eol = content.find("\n", ndx)
                                gtype = content[ndx:eol]
                            else: 
                                gtype = 'Unknown'
                                
                            addrepo['region'] = gtype.strip()

                            ndx = content.find('pitch:') + 6
                            if ndx > 5: # -1 + 6
                                eol = content.find('\n', ndx)
                                gtype = content[ndx:eol]
                            else:
                                gtype = 'More info soon...' 
                            addrepo['pitch'] = gtype.strip()
                            ndx = content.find('meetup-group:')
                            if ndx > -1:
                                ndx += 13
                                eol = content.find('\n', ndx)
                            
                                mu = content[ndx:eol]
                                if len(mu.strip()) > 0:
                                    addrepo['meetup-group'] = mu.strip()
                            results.append(addrepo)



        return results


    def GetFilesMatching(self, repo, path, matching=''):
        rfiles = []
        url = self.gh_endpoint + self.content_fragment
        url = url.replace(":repo", repo)
        url = url.replace(":path", path)   
        headers = {"Authorization": "token " + self.apitoken}
        r = requests.get(url = url, headers=headers)
        if self.TestResultCode(r.status_code):
            contents = json.loads(r.text)
            for item in contents:
                if item['type'] == 'file':
                    if matching and item['name'].find(matching) > -1:
                        rfiles.append(item['name'])
                    elif not matching:
                        rfiles.append(item['name'])
    
        return r, rfiles

    def AddRepoToTeam(self, team, repo):
        getTeamUrl = self.team_getbyname_fragment.replace(':team_slug', team)
        headers = {"Authorization": "token " + self.apitoken,
            "Accept":"application/vnd.github.hellcat-preview+json, application/vnd.github.inertia-preview+json"
        }
        url = self.gh_endpoint + getTeamUrl
        r = requests.get(url = url, headers=headers)
        team_id = None
        if r.ok:
            jsonTeam = json.loads(r.text)
            team_id = jsonTeam['id']

        if team_id:
            repofrag = self.team_addrepo_fragment.replace(':team_id', str(team_id))
            repofrag = repofrag.replace(':repo', repo)
            headers = {"Authorization": "token " + self.apitoken,
                "Accept":"application/vnd.github.hellcat-preview+json, application/vnd.github.inertia-preview+json"
            }

            url = self.gh_endpoint + repofrag

            data = { "permission" : "admin"}
            jsonData = json.dumps(data)
            r = requests.put(url = url, headers=headers, data=jsonData)

        return r

    def MoveFromOFtoOWASP(self, frompath, topath):
        r = self.GetOFFile('OWASP-wiki-md', frompath)
        r2 = self.GetFile('www-community', topath)
        if r.ok and not r2.ok: # exists in 1, not in other
            doc = json.loads(r.text)
            content = base64.b64decode(doc["content"]).decode()
            fcontent = '---\n\n'
            fcontent += 'layout: col-sidebar\n'
            fcontent += f"title: {frompath.replace('_', ' ')}\n"
            fcontent += f'author: \n'
            fcontent += f'contributors: \n'
            if 'attacks/' in topath:
                fcontent += f"permalink: /attacks/{frompath.replace('.md','')}\n"
                fcontent += f"tag: attack, {frompath.replace('_', ' ')}\n"
            else :
                fcontent += f"permalink: /vulnerabilities/{frompath.replace('.md','')}\n"
                fcontent += f"tag: vulnerability, {frompath.replace('_', ' ')}\n"

            fcontent += 'auto-migrated: 1\n\n---\n\n'
            fcontent += content

            r = self.UpdateFile('www-community', topath, fcontent, '')

        return r

    def RepoExists(self, repoName):
        repofrag = self.repo_fragment.replace(':repo', repoName)
        headers = {"Authorization": "token " + self.apitoken,
                "Accept":"application/vnd.github.nebula-preview+json"
            }

        url = self.gh_endpoint + repofrag
        r = requests.get(url = url, headers=headers)
        return r

    def GetLastUpdate(self, repoName, file):
        repofrag = self.commit_fragment.replace(':repo', repoName)
        repofrag += f"?path={file}&page=1&per_page=1"
        headers = {"Authorization": "token " + self.apitoken,
                "Accept":"application/vnd.github.nebula-preview+json"
            }

        url = self.gh_endpoint + repofrag
        r = requests.get(url = url, headers=headers)
        datecommit = None
        if r.ok:
            res = json.loads(r.text)
            datecommit = res[0]['commit']['committer']['date']

        return datecommit

    def FindUser(self, user):
        url = self.gh_endpoint + self.user_fragment
        url = url.replace(":username", user)
        headers = {"Authorization": "token " + self.apitoken}
        r = requests.get(url = url, headers=headers)
        user = None
        if r.ok:
            try:
                user = json.loads(r.text)
            except json.JSONDecodeError:
                pass

        return user

    def AddUserToRepo(self, user, repo):
        repofrag = self.collaborator_fragment
        repofrag = repofrag.replace(':repo', repo)
        repofrag = repofrag.replace(':username', user)

        headers = {"Authorization": "token " + self.apitoken,
            "Accept":"application/vnd.github.hellcat-preview+json, application/vnd.github.inertia-preview+json"
        }

        url = self.gh_endpoint + repofrag

        # first do a get to see if they are already a user
        r = requests.get(url = url, headers=headers)
        if not r.ok:
            data = { "permission" : "admin"}
            jsonData = json.dumps(data)
            r = requests.put(url = url, headers=headers, data=jsonData)

        return r

    def ParseLeaderline(self, line):
        ename = line.find(']')
        name = line[line.find('[') + 1:line.find(']')]
        email = line[line.find('(', ename) + 1:line.find(')', ename)]
        return name, email

    def GetLeadersForRepo(self, repo):
        repo_leaders = []
        r = self.GetFile(repo, 'leaders.md')
        if r.ok:
            doc = json.loads(r.text)
            content = base64.b64decode(doc['content']).decode(encoding='utf-8')
            lines = content.split('\n')
            in_leaders = False
            for line in lines:
                testline = line.lower()
                if in_leaders and '###' in testline:
                    in_leaders = False
                    break
                
                if in_leaders and not testline.startswith('*'):
                    continue
                
                if(testline.startswith('###') and 'leader' not in testline):
                    continue
                elif(testline.startswith('###') and 'leader' in testline):
                    in_leaders = True
                    continue
                if in_leaders:
                    fstr = line.find('[')
                    if(line.startswith('*') and fstr > -1 and fstr < 4):
                        name, email = self.ParseLeaderline(line)
                        leader = {}
                        leader['name'] = name
                        leader['email'] = email.replace('mailto://','').replace('mailto:','')
                        
                        repo_leaders.append(leader)

        return repo_leaders