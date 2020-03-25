import requests
import json
import base64
from pathlib import Path
import os
import datetime

class OWASPGitHub:
    apitoken = os.environ["APITOKEN"]
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
    

    def CreateRepository(self, repoName, rtype):
        repoName = self.FormatRepoName(repoName, rtype)
        description = "OWASP Foundation Web Respository"
        data = { 
            "name": repoName, 
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
        

    def GetPublicRepositories(self, matching=""):
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
                    haspages = repo['has_pages']
                    if not istemplate and haspages:
                        pages = self.GetPages(repoName)
                        if pages['status'] == None:
                            continue
                        
                        if not matching or matching in repoName:
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