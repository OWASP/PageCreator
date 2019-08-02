# page-creator
# Tool used for creating chapter and project pages
# for OWASP Community

import requests
import json
from github import *

def main():
    chapter = "Test Chapter Two"
    
    github = OWASPGitHub()
    

    r = github.CreateRepository(chapter)
    if github.TestResultCode(r.status_code):
        r = github.InitializeRepositoryPages(chapter)
    if github.TestResultCode(r.status_code):
        r = github.EnablePages(chapter)
    if github.TestResultCode(r.status_code):
        print("Pages Created")
    else:
        print("Failure: " + r.text) 
        


main()