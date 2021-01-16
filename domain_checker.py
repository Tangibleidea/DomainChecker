import requests
import re
import urllib3
import os
from datetime import datetime
#from pytz import timezone
from github import Github

ISSUE_COUNT= 0
FILTERLIST_URL = "https://easylist-downloads.adblockplus.org/koreanlist+easylist.txt"
ISSUE_BODY= ""

def printIssue(mystr):
    global ISSUE_BODY
    print(mystr)
    ISSUE_BODY += mystr + "\n"

def publishAnIssue():
    global ISSUE_COUNT, ISSUE_BODY
    if ISSUE_COUNT == 0:
        print("no any issue to publish.")
        return
    access_token = os.environ['MY_GITHUB_TOKEN']
    repository_name= "DomainChecker"

    # german_timezone = timezone('Europe/Berlin')
    # today = datetime.now(german_timezone)
    # today_data = today.strftime("%d.%m.%Y")
    title= "Found "+str(ISSUE_COUNT)+" domain issue(s)."

    g = Github(access_token)
    repo = g.get_user().get_repo(repository_name)
    res= repo.create_issue(title=title, body=ISSUE_BODY)
    print(res)

def readSourceFromABPFilters(url, target):
    global ISSUE_COUNT, ISSUE_BODY
    http = urllib3.PoolManager()
    response = http.request('GET', url)
    data = response.data.decode('utf-8')

    target= target.replace("http://", "")
    target= target.replace("https://", "")

    number_of_domain= extract_number(target)
    _pattern= target.replace(str(number_of_domain), "(\d{1,3}|\*)")

    for line in data.splitlines():
        searched= re.search(_pattern, line)
        # found a target domain
        if(searched):
            # substringed : only a domain
            # extracted : only a number of domain
            substringed= line[searched.start():searched.end()]
            extracted= extract_number(substringed)
            if(extracted == -1):
                printIssue(line +" :arrow_right: (nothing to fix) :thumbsup:")
                continue
            # number of the written filter is old.
            if(extracted < number_of_domain):
                ISSUE_COUNT += 1
                renewed_filter= line.replace(str(extracted), str(number_of_domain))
                printIssue(str(ISSUE_COUNT) + ". Filter update suggestion:\n" + line + " :arrow_right: " + renewed_filter)
            elif(extracted == number_of_domain):
                printIssue(line +" :arrow_right: (nothing to fix) :thumbsup:")
    printIssue("")

def extract_number(url):
    parsed_int_list= re.findall("\d+", url)
    if len(parsed_int_list) == 0:
        #raise Exception("no any digits in url("+url+")")
        print("no any digits in url("+url+")")
        return -1
    parsed_int= int(parsed_int_list[0])
    return parsed_int

def url_ok(url):
    global ISSUE_BODY
    if "http" not in url:
        url = "https://"+ url

    working_domains= []
    parsed_int= extract_number(url)
    found_domain_works= False
    which_number_latest_works = 0
    i= parsed_int-1

    while True:
        if found_domain_works and i > parsed_int+1 and not which_number_latest_works == i-1:
            break
        if i > 100:
            printIssue("")
            break
        try:
            replaced= url.replace(str(parsed_int), str(i))
            r = requests.head(replaced)
            if r.status_code != 200:
                printIssue(replaced + ": status("+r.status_code+") :grey_question:")
            else:
                printIssue(replaced+": working fine :white_check_mark:")
                found_domain_works= True
                which_number_latest_works= i
                working_domains.append(replaced)
            i=i+1
        except Exception:
            printIssue(replaced+": not working :no_entry_sign:")
            i=i+1
            continue
    return working_domains

file1 = open('domain_checklist.txt', 'r') 
Lines = file1.readlines() 
count = 0 
for line in Lines: 
    if(line.startswith("#")): # ignore comments
        continue

    working_domains= url_ok(line.strip())
    for domain in working_domains:
        readSourceFromABPFilters(FILTERLIST_URL, domain)
        
publishAnIssue()
