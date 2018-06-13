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
import traceback

#==================================================#
# LOGIN DATA

# Fill in your details here to be posted to the login form.
payload = {
    'username': 's1610307097',
    'password': ''
}

#==================================================#
# GLOBALS

max_files = 0
failed_files = 0
session_success = True
continue_download = True
re_login = True
special_chars = {
    "\\", "?", "|", ":", "<", ">", "*"
} 

LOGIN_URL="https://hagenberg.elearning.fh-ooe.at/login/index.php"

#==================================================#
# USER CREDENTIALS

def get_user_credentials():
    if (not payload['username'] or payload['username'] == ''):
        payload['username'] = (input('Please insert your MatrNr.: ')).upper()
        if (payload['username'][0] != 'S'):
            payload['username'] = 'S' + payload['username']

    if (not payload['password'] or payload['password'] == ''):
        payload['password'] = getpass.getpass('Insert password for > ' + payload['username'] + ' <: ')

#==================================================#
#REPLACE

def replace_all(text, dic):
   for i in dic:
       text = text.replace(i, " ")
   return text

#==================================================#
# SESSION + DOWNLOADER

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
                max_files += 1
                file_name = file_retry[0]

                # remove / and ?; first and last character
                file_name = file_name[1:-1]

                try:
                    r = session.get(sub_page.url, stream=True)
                except requests.exceptions.RequestException as e:  # This is the correct syntax
                    print('\tfailed to download ' + file_name)
                    failed_files += 1

                print("\tdownloading " + file_name)

                with open(folder + '/'+ file_name, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk: # filter out keep-alive new chunks
                            f.write(chunk)

        except Exception as e:    # the exception instance
            failed_files += 1
            print("\n\r")
            print (e.args)      # arguments stored in .args
            traceback.print_exc(limit=200, file=sys.stdout)
            print("\n\r")
                
def get_sections(session, url):
    print('Fetching sections..')
    page = session.get(url)
    parsed_html = BeautifulSoup(page.text, "html.parser")
    directory=re.split(':', parsed_html.body.h1.text)[0]
    create_dir(directory)
    print("\r\n> Kurs: "+directory + ' <')
    themata=parsed_html.find_all('li', attrs={'role':'region','class':'section main clearfix'})
    
    for thema in themata:
        try:
            thema_name=re.findall('<span class="hidden sectionname">(.*?)<\/span>',str(thema))[0]
            links=re.findall('href=\"(http[s]?:\/\/hagenberg\.elearning\.fh-ooe\.at\/mod\/resource\/view\.php\?id\=[0-9]{4,}?)\"' ,str(thema))
            if len(links)>0 :
                print(thema_name)
                # strip of right whitespaces of dir
                d1 = (directory + '/'+ thema_name).rstrip()

                # make sure to replace special chars
                d1 = replace_all(d1, special_chars)

                create_dir(d1)
                for i in links:
                    download_page(session,i,d1)
        except Exception as e:
            print ("Unexpected error:", sys.exc_info()[0])
            print (e.args)      # arguments stored in .args
            traceback.print_exc(limit=200, file=sys.stdout)
            continue
                
        
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
        p = s.post(LOGIN_URL, data = payload)

        if (("Ungültige Anmeldedaten!" or "Invalid login") in p.text):
            session_success = False

        return s

#==================================================#
# MAIN + START

print('*******************************************************************************************')
print('   __  ___             ____      ___                    ________               ___   ______'+ '\r\n' +
'  /  |/  /__  ___  ___/ / /__   / _ \___ _    _____    /_  __/ /  ___ __ _    / _ | / / / /'+ '\r\n' +
' / /|_/ / _ \/ _ \/ _  / / -_) / // / _ \ |/|/ / _ \    / / / _ \/ -_)  ` \  / __ |/ / /_/ '+ '\r\n' +
'/_/  /_/\___/\___/\_,_/_/\__/ /____/\___/__,__/_//_/   /_/ /_//_/\__/_/_/_/ /_/ |_/_/_(_)  '+ '\r\n' +
'                                                                                           ')
print('*******************************************************************************************\r\n')


while (re_login):
    re_login = False

    get_user_credentials()
    print('Creating session for ' + payload['username'] + ' ....')
    current_session = get_session()

    if (session_success):
        while (continue_download):
            
            url = input("Please insert the moodle link (example: 'https://hagenberg.elearning.fh-ooe.at/course/view.php?id=6857'):\r\n")
            if ((len(url) > 17) and ("hagenberg" in url)):
                get_sections(current_session, url)

                print('\r\nFinished downloading ' + str(max_files - failed_files) + '/' + str(max_files) + ' files')
                if (failed_files != 0):
                    print('\t' + str(failed_files) + ' downloads failed')
                elif (max_files == 0):
                    print('Moodle course empty or wrong link.. (or not inscribed)')
            else:
                print("url to short or wrong..")

            print('\r\n- Again? - (y/n)')
            key = input()
            if (key.lower()[0] != ('y' or 'j')):
                continue_download = False
    else:
        print ('Failed creating session.. wrong password or username?')
        print('\r\n- Again? - (y/n)')
        key = input()
        if (key.lower()[0] == ('y' or 'j')): 
            re_login = True

            key = input('Re-enter username and password? (1 -> username, 2->password, both->3, none->any other key): \n\r > ')
            if (key == '1'): 
                payload['username'] = ''
            elif (key == '2'): 
                payload['password'] = ''
            elif (key == '3') :
                payload['username'] = ''
                payload['password'] = ''
            
            get_user_credentials()
            re_login = True
        
        

input("Press enter to exit..")