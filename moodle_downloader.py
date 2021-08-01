import pip

def import_or_install(package):
    try:
        __import__(package)
    except ImportError:
        pip.main(['install', package])

import_or_install('requests')
import_or_install('bs4')


from bs4 import BeautifulSoup
import urllib.request
import requests
from urllib.parse import unquote
import re
import os
import unicodedata
import json

## CHANGE THIS! ##
cookies = {'MoodleSessionlmsfhooe': '','dtCookie':''}
##################
def DownloadCoursesOverview(link):
    #Get the sessionkey for Jquery API session
    r = requests.post(link, allow_redirects=False, cookies=cookies)
    soup = BeautifulSoup(r.content, "html.parser")
    data = soup.find("script",text=re.compile(".*M\.cfg = ({.*});.*", re.MULTILINE|re.DOTALL))
    js = re.search("M\.cfg = ({.*?});",str(data.contents))
    json_object = json.loads(str(js.group(1)))
    sessionkey = json_object["sesskey"]
    #Download API content
    apiURL = "https://elearning.fh-ooe.at/lib/ajax/service.php?sesskey=" + sessionkey + "&info=core_course_get_enrolled_courses_by_timeline_classification"
    print(apiURL)
    apiRequest = '[{"index":0,"methodname":"core_course_get_enrolled_courses_by_timeline_classification","args":{"offset":0,"limit":0,"classification":"allincludinghidden","sort":"fullname","customfieldname":"filtercat","customfieldvalue":"300"}}]'
    r = requests.get(apiURL, allow_redirects=False, cookies=cookies, data=apiRequest)
    json_object = json.loads(r.content)
    #print(json_object[0]["data"]["courses"])
    for course in json_object[0]["data"]["courses"]:
        print(course["viewurl"])
        DownloadCoursePage(course["viewurl"])
    open("1.html" , 'wb').write(r.content)
def DownloadCoursePage(link):
    r = requests.get(link, allow_redirects=False, cookies=cookies)
    soup = BeautifulSoup(r.content, "html.parser")
    coursName = slugify(soup.title.string)
    CreateDir(coursName)
    open(coursName + "/index.html" , 'wb').write(r.content)
    #Get sections in a course
    sections = soup.find_all("li", id=re.compile("section-[0-9]+"))
    #Get Files of section
    for section in sections:
        files = section.find_all("li", class_='resource')
        fileLinks = [ l.a["href"] for l in files if l]
        print("DownloadFiles",fileLinks)
        for l in fileLinks:
            DownloadFiles(l,coursName)
def DownloadFiles(link, saveFolder):
    r = requests.get(link, allow_redirects=False, cookies=cookies)
    open("1.html" , 'wb').write(r.content)
    soup = BeautifulSoup(r.content, "html.parser")
    try:
        fileLink = soup.a["href"]
        filename=fileLink.split("/")[-1]
        print("Downloading File:", filename)
        r = requests.get(fileLink, allow_redirects=False, cookies=cookies)
        print("save to", saveFolder + "/" + filename)
        open(saveFolder + "/" + filename, 'wb').write(r.content)
    except:
        print("Failed to Download link:",link)
        r = requests.get(link, allow_redirects=False, cookies=cookies)
        filename = link.split("=")[-1]+".html"
        print("Downloading to File: ", saveFolder + "/" + filename)
        open(saveFolder + "/" + filename , 'wb').write(r.content)
def CreateDir(dirName):
    try:
        os.makedirs(dirName)    
        print("Directory " , dirName ,  " Created ")
    except FileExistsError:
        print("Directory " , dirName ,  " already exists")
def slugify(value, allow_unicode=False):
    return value.replace("%","").replace(":","")

DownloadCoursesOverview("https://elearning.fh-ooe.at/my/")
