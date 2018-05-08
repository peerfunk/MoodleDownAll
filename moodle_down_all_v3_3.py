# -*- coding: utf-8 -*-
import pip

def import_or_install(package):
    try:
        __import__(package)
    except ImportError:
        pip.main(['install', package])

import_or_install('requests')
import_or_install('bs4')
import_or_install('getpass')

import requests
import re
import os
import sys
from bs4 import BeautifulSoup
import urllib.request
from urllib.parse import unquote
import getpass

# Fill in your details here to be posted to the login form.
payload = {
    'username': '',
    'password': ''
}

failed_files = 0
max_files = 0
session_success = True

LOGIN_URL="https://hagenberg.elearning.fh-ooe.at/login/index.php"

def get_files(session,url):
    directory=re.split('=', url)[1]
    print(directory)
    if not os.path.exists(directory):
        os.makedirs(directory)
    page = session.get(url)
    links=re.findall('href=\"(http[s]?:\/\/hagenberg\.elearning\.fh-ooe\.at\/mod\/resource\/view\.php\?id\=[0-9]{4,}?)\"' ,page.text)
    for i in links:
        download_page(session,i,directory)

def download_page(session, url, folder):
    global max_files
    global failed_files

    sub_page = session.get(url)

    file = re.findall('\"(http[s]?\:\/\/hagenberg\.elearning\.fh-ooe\.at\/pluginfile\.php\/[0-9]*?\/mod_resource\/content.*?)\"',sub_page.text)

    if (len(file) != 0):
        # decode UTF-8 and unquote URL quoting
        local_filename = unquote(file[0].split('/')[-1])

        max_files+=1
        try:
            r = session.get(file[0], stream=True)
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            print('\tfailed to download ' + local_filename)
            failed_files+=1

        print("\tdownloading " + local_filename)

        with open(folder + '/'+ local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
    else:
        # If the subpage itself is a file
        # Download the file from `url` and save it locally under `file_name`:

        myre = re.compile("\/[a-zA-Z0-9_-]+\.\w+\?{1}")
        file_retry = myre.findall(sub_page.url)

        try:
            if (len(file_retry) != 0):
                max_files+=1
                file_name = file_retry[0]

                # remove / and ?; first and last character
                file_name = file_name[1:-1]

                try:
                    r = session.get(sub_page.url, stream=True)
                except requests.exceptions.RequestException as e:  # This is the correct syntax
                    print('\tfailed to download ' + file_name)
                    failed_files+=1

                print("\tdownloading " + file_name)

                with open(folder + '/'+ file_name, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk: # filter out keep-alive new chunks
                            f.write(chunk)

        except Exception as e:    # the exception instance
            failed_files+=1
            print (e.args)      # arguments stored in .args
            print (e)
                
def get_sections(session, url):
    print('Fetching sections..')
    page = session.get(url)
    parsed_html = BeautifulSoup(page.text, "html.parser")
    directory=re.split(':', parsed_html.body.h1.text)[0]
    create_dir(directory)
    print("\r\n> Kurs: "+directory + ' <')
    themata=parsed_html.find_all('li', attrs={'role':'region','class':'section main clearfix'})

    for thema in themata:
        thema_name=re.findall('<span class="hidden sectionname">(.*?)<\/span>',str(thema))[0]
        links=re.findall('href=\"(http[s]?:\/\/hagenberg\.elearning\.fh-ooe\.at\/mod\/resource\/view\.php\?id\=[0-9]{4,}?)\"' ,str(thema))
        if len(links)>0 :
            print(thema_name)
            # strip of right whitespaces of dir
            d1 = (directory + '/'+ thema_name).rstrip()
            create_dir(d1)
            for i in links:
                download_page(session,i,d1)
                
        
def get_url_date(day, month, year):
    cal_url ="https://hagenberg.elearning.fh-ooe.at/calendar/view.php?view=month&"
    return cal_url + "cal_d=" + day + "&cal_m="+month + "&cal_y=" + year

def extract_dict(webpage):
    return re.findall('<td data-core_calendar-title="(.*?)" data-.*?href=&quot;https:\/\/hagenberg\.elearning\.fh-ooe\.at\/calendar\/view\.php\?view=day.*?&gt;(.*?)&lt.*?<a href="(.*?)">', webpage)

def create_dir(directory):
      if not os.path.exists(directory):
        os.makedirs(directory)

def get_dates_for(session, day, month, year):
        r = session.get(get_url_date(day,month,year))
        #print(extract_dict(r.text))
        out = open("index.html", 'w', encoding='utf8')
        out.writelines((r.text))
        out.close()
        return  (extract_dict(r.text))

def get_courses(session):
    r =session.get("https://hagenberg.elearning.fh-ooe.at/my/index.php")
    return re.findall('<h3><a title="(.*?)"',r.text)

def get_session():
    global session_success
    with requests.Session() as s:
        p = s.post(LOGIN_URL, data=payload)

        if (p.status_code != requests.codes.ok):
            session_success = False
        return s

def get_user_credentials():
    if (not payload['username']):
        payload['username'] = (input('Please insert MatrNr.: ')).upper()
        if (payload['username'][0] != 'S'):
            payload['username'] = 'S' + payload['username']

    if (not payload['password']):
        payload['password'] = getpass.getpass('Insert password for > ' + payload['username'] + ' <: ')

print('*******************************************************************************************')
print('   __  ___             ____      ___                    ________               ___   ______'+ '\r\n' +
'  /  |/  /__  ___  ___/ / /__   / _ \___ _    _____    /_  __/ /  ___ __ _    / _ | / / / /'+ '\r\n' +
' / /|_/ / _ \/ _ \/ _  / / -_) / // / _ \ |/|/ / _ \    / / / _ \/ -_)  ` \  / __ |/ / /_/ '+ '\r\n' +
'/_/  /_/\___/\___/\_,_/_/\__/ /____/\___/__,__/_//_/   /_/ /_//_/\__/_/_/_/ /_/ |_/_/_(_)  '+ '\r\n' +
'                                                                                           ')
print('*******************************************************************************************\r\n')

get_user_credentials()
print('Creating session for ' + payload['username'] + ' ....')
s1=get_session()

if (session_success):
    while True:
        url = input("Bitte Moodle-Kurs-URL eingeben('https://hagenberg.elearning.fh-ooe.at/course/view.php?id=6857'):\r\n")
        get_sections(s1,url)

        print('\r\nFinished downloading ' + str(max_files - failed_files) + '/' + str(max_files) + ' files')
        if (failed_files != 0):
            print('\t' + str(failed_files) + ' downloads failed')
        elif (max_files == 0):
            print('Moodle course empty or session was created with wrong credentials..')
        print('\r\n- Again? - (y/n)')
        s = input()
        if (s.lower()[0] != 'y'):
            break
else:
    print('failed to create a session... wrong pw or username?')
