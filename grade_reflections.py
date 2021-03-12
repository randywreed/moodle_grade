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
from scipy.stats import zscore
import statistics
import numpy as np

course='Spring_2021_rel_1010_'

def createZscore(df):
  #create z-score

  namedf=df[['name']]
  zdf=df[df.columns.difference(['name'])].apply(zscore)
  ndf=namedf.join(zdf)
  return(ndf)

def addZavg(ndf):
  ndf['z-average'] = ndf.iloc[:,1:].mean(axis=1)
  #print(df.head())
  return ndf


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

def QuantileAdd(df,quantlist):
  #return a dataframe with quantile score column added
  #quant=df['z-average'].quantile(quantlist)
  #add a column to the df
  #df['quantile'] = pd.qcut(df['b'], quantlist, labels=False)

  df['quantile']=pd.qcut(df['total_words'],quantlist,labels=False,duplicates='drop')
  return df

def gradeIt(htmlsubmissions, course_users, grade_type,config_type):   
    qlist=[0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1]
    lowerqlist=[0,.1,.2,.6,1]
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
        if grade_type==-9:
            if totnumwords>100:
                grade="Credit"
            else:
                grade="No Credit"
        newvars.append([uid,name, totnumwords,grade])
    cdf=pd.DataFrame(newvars,columns=['uid','name','total_words','grade'])
    if grade_type>0:
        zcurdf=cdf[cdf['total_words']<50].copy()
        print('number of 0 studnets',zcurdf.shape)
        curdf=cdf[cdf['total_words']>50]
        print('total words mean=',curdf['total_words'].mean())
        print('quarter total words mean=',curdf['total_words'].mean()*.25)
        lcurdf=curdf[curdf['total_words']<curdf['total_words'].mean()*.25].copy()
        print('number of students w total words below .25 the mean=',lcurdf.shape)
        ncurdf=curdf[curdf['total_words']>curdf['total_words'].mean()*.50].copy(deep=True)
        # those between .25 and .50 of average
        bwrds=curdf['total_words'].mean()*.25
        uwrds=curdf['total_words'].mean()*.50
        acurdf=curdf[curdf['total_words'].between(bwrds, uwrds, inclusive=True)].copy()
        #acurdf=curdf[(curdf['total_words']>curdf['total_words'].mean()*.25) & (curdf<=curdf['total_words'].mean()*.50)].copy()
        print('total student between 1/4 and 1/2 the mean=',acurdf.shape)
        # score those using lowerqlist
        acurdf=QuantileAdd(acurdf, lowerqlist)
        #print(acurdf)
        acurdf['quantile']=acurdf['quantile']+3
        #print(ncurdf)
        print('total students above 1/2 the mean=',curdf.shape)
        #print('type ncurdf=',type(ncurdf))
        ncurdf=QuantileAdd(ncurdf,lowerqlist)
        #print(ncurdf)
        #anyone above 7 raise to 10
        tcurdf=ncurdf[ncurdf['quantile']>7].copy()
        bcurdf=ncurdf[ncurdf['quantile']<8].copy()
        print('number of students at top=',tcurdf.shape)
        if len(tcurdf.index)>0:
            tcurdf.loc[:,'quantile']=10

        bcurdf['quantile']=bcurdf['quantile']+7

        print('current count=',bcurdf.shape)
        if len(zcurdf.index)>0:
            zcurdf.loc[:,'quantile']=0
            print('zero count=',zcurdf.shape)
        if len(lcurdf.index)>0:
            lcurdf.loc[:,'quantile']=3
            print('bottom count=',lcurdf.shape)
        bcurdf=bcurdf.append(zcurdf, ignore_index=True)
        bcurdf=bcurdf.append(lcurdf, ignore_index=True)
        bcurdf=bcurdf.append(acurdf, ignore_index=True)
        bcurdf=bcurdf.append(tcurdf, ignore_index=True)
        print('final count=',bcurdf.shape)
        #curdf
        #cdf['uid'].isin(bcurdf['uid']),'grade']=bcurdf['quantile']
        cdf['grade']=cdf['uid'].map(bcurdf.set_index('uid')['quantile']).fillna(cdf['grade'])
        

    return cdf   

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
    #grade_type=-9 credit/no credit, >0 points
    grade_type=ass['grade']
    #check if files are accepted
    config_type="onlinetxt"
    for config in ass['configs']:
        if config['plugin']=="file" and config['subtype']=="assignsubmission" and config['name']=="enabled":
            config_type="filetxt"
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
        df=gradeIt(htmlsubmissions=htmlsubmissions, course_users=course_users,grade_type=grade_type,config_type=config_type)
        fester=''
        if config_type=="filetxt":
            #check if people have files but no text, and flag them
            zerodf=df[df['total_words']==0].copy()
            if zerodf.shape[0]>0:
                for x,z in zerodf.iterrows():
                    subs=list(filter(lambda uid: uid['userid']==z['uid'],sub_submissions))
                    for s1 in subs:
                        if s1['userid']==z['uid']:
                            for p in s1['plugins']:
                                if "fileareas" in p:
                                    for f in p['fileareas']:
                                        if 'files' in f:
                                            for fl in f['files']:
                                                if fl['filesize']>0:
                                                    fester+=findUser(s1['userid'],course_users)+" got a zero but turned in a file for assingment {} - manually check \n".format(assname)
                        

        #mycolums=['id','name','total_words','Grade']
        #df=pd.DataFrame(newvars, columns=mycolums)
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
estr+=fester
server.sendmail(efrom,to,estr)