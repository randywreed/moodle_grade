import spacy
import pytz
from datetime import datetime
import textstat
import pandas as pd
import html2text
import os,re
from nltk import word_tokenize
import nltk, spacy, textstat
from nltk import sent_tokenize, word_tokenize
from nltk.tree import *
import smtplib

course='Spring_2021_rel_1010_'
def strip_html_tags(htmlsubmissions):
    for i,hsub in enumerate(htmlsubmissions):
        txhub=html2text.html2text(hsub['text'])
        #print(txhub)
        htmlsubmissions[i]['text']=txhub
    return htmlsubmissions

def findUser(id, users):
    for person in users:
        if person['id']==id:
            return person['fullname']
    
def gradeIt(htmlsubmissions, course_users):   
    newvars=[]
    scnt=0
    mycolums=['id','name','total_words','Grade']
    for d in htmlsubmissions:
        out=[]
        raw=d['text']
        uid=d['userid']
        out=[]
        y=raw.split('\n\n')
        for para in y:
            para=para.replace('\n',' ')
            out.append(para)

        #Tokenize words in each paragraph. Add to list if more than 5 words
        allparagraphswdcnt=0
        outwdtokens=[]
        for para in out:
            wordTokens=word_tokenize(para)
            allparagraphswdcnt=allparagraphswdcnt+len(wordTokens)
            if (len(wordTokens)>5):
                #print (wordTokens)
                outwdtokens.append(wordTokens)
        #print(out)

        
        totnumwords=0
        for wrdcnt in outwdtokens:
            totnumwords+=len(wrdcnt)
            scnt=scnt+1
                #print('total number of words={0}, total sentences={1}'.format(totnumwords,sentnum))
        #print('total number of words=',totnumwords)
        name=findUser(uid,course_users)
        grade="-"
        if totnumwords>100:
            grade="Credit"
        else:
            grade="No Credit"
        newvars.append([uid,name, totnumwords,grade])
    
    return newvars   

def checkCSV(name,dflen):
    if os.path.isfile(name):
        pass
    else:
        return True
    df=pd.read_csv(name)
    if dflen>df.shape[0]:
        #new records added, update csv
        return True
    else:
        return False




spacy.load('en')
import sys
sys.path.append("moodle_api.py")
import configparser
config=configparser.ConfigParser()
config.read('/home/reedrw/.credentials/moodle.ini')
moodle_key=config['DEFAULT']['moodle_key']

import moodle_api
moodle_api.URL = "https://asulearn.appstate.edu/"
moodle_api.KEY=moodle_key
classID=config['DEFAULT']['moodle_classID']
config.read('email.ini')
efrom=config['DEFAULT']['from']
to=config['DEFAULT']['to']
appkey=config['DEFAULT']['appkey']
#print(classID)
server=smtplib.SMTP('smtp.gmail.com:587')
server.starttls()
server.login(efrom,appkey)
course_users = moodle_api.call('core_enrol_get_enrolled_users', courseid=classID)
assignments=moodle_api.call('mod_assign_get_assignments', courseids=[classID])
assignment=assignments['courses']
ostr=[]
for a in assignment:
  #print(a)
  for ass in a['assignments']:
    assignmentID=ass['id']
    assname=ass['name']
    #print('assignment=%s id=%s'% (ass['name'],ass['id']))
    submissons=moodle_api.call('mod_assign_get_submissions', assignmentids=[assignmentID])
    sub_assignments=submissons['assignments']
    htmlsubmissions=[]
    sub_submissions=sub_assignments[0]['submissions']
    tz=pytz.timezone('America/New_York')
    ddate=datetime.fromtimestamp(ass['duedate'],tz)
    strdate=ddate.strftime('%m-%d-%Y')
    if datetime.now().strftime('%m-%d-%Y')>strdate and len(sub_submissions)>(.8*len(course_users)):
        #print('assignment {} id= {} due={} submissions={}'.format(ass['name'],ass['id'],strdate, len(sub_submissions)))
        c=0
        for s in sub_submissions:
            uid=s['userid']
            for pl in s['plugins']:
                #print ('pl=',pl)
                if 'editorfields' in pl:
                #print ('editorfields=',pl['editorfields'])
                #print (pl['editorfields'][0]['text'])
                #print('user=',uid)
                    htmlsubmissions.append({'userid':uid, 'text':pl['editorfields'][0]['text']})
                    c=c+1
        #print(c)
        htmlsubmissions=strip_html_tags(htmlsubmissions=htmlsubmissions)
        newvars=gradeIt(htmlsubmissions=htmlsubmissions, course_users=course_users)
        mycolums=['id','name','total_words','Grade']
        df=pd.DataFrame(newvars, columns=mycolums)
        fname=assname+strdate
        output=course+fname+'grades.csv'
        #print(output)
        if checkCSV(output,df.shape[0]):
            df.to_csv(output, index=False)
            ostr.append(output)
            print('updated {}'.format(output))
estr="Subject: files update\n\nThe following files have been updated and need to be uploaded to asulearn \n"
for e in ostr:
    estr+=e+"\n "
server.sendmail(efrom,to,estr)