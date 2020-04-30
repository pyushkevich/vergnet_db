#!/usr/bin/env python3
import web
import httplib2
import csv
import os
import json
from oauth2client import client
from googleapiclient.discovery import build
from web import form
from database_v2 import update_database, create_indexes, write, dx_haschanged, db_info, get_field_list, prop, crit, del_merge
from query_sampler import query, get_query_list, return_all_properties
from custom_query import query_builder, merge, info_builder
import prettytable 
from csv_preprocessing import preprocess, tsv2csv, FDG_preprocess, quoteCSV, summary_preprocess
import zipfile
import uuid
#from test import test_ajax

##Globals
web.config.debug = False
email_re='(?:[a-z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&\'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])'
dupe_option=["VISCODE2", "VISCODE", "EXAMDATE", "SCANDATE", "UPDATE_STAMP", "USERDATE", "USERDATE2"]

web.config.session_parameters['cookie_name'] = 'webpy_session_id'
web.config.session_parameters['cookie_domain'] = os.environ.get('ADNIDB_COOKIE_DOMAIN', None)
web.config.session_parameters['timeout'] = 31536000 
web.config.session_parameters['ignore_expiry'] = True
web.config.session_parameters['ignore_change_ip'] = True
web.config.session_parameters['secret_key'] = 'JDQj2NVxVD4XZHW5lc6o'
web.config.session_parameters['expired_message'] = 'Session expired'

##Urls: each url correspond to a class
urls = ('/', 'Index',                        #homepage
        '/logout','Logout',                    #logout page
        '/query([/].*|)','Query',            #query pages
        '/db_update([/].*|)', 'Update',        #database update pages (useful ?)
        '/about','About',                    #about the web based interface (info about the db)
        '/api/oauth2cb','OAuthCallbackAPI',
        '/temp([/].*|)','Temp')                #ajax temporary treatment
    
app = web.application(urls, globals())        


# Get the root directory
rootdir=os.environ.get('ADNIDB_ROOT', None)
if rootdir is None:
    print('Environment variable ADNIDB_ROOT is not set')
    sys.exit(-1)

# This is used in lots of the queries
dir_path = os.path.join(rootdir,'instance')

# Global configuration entries
config = {
    'ADNIDB_IMPORT_SAVEDIR' : os.environ.get('ADNIDB_IMPORT_SAVEDIR', os.path.join(rootdir, 'instance/savefile')),
    'ADNIDB_NEO4J_IMPORT' :   os.environ.get('ADNIDB_NEO4J_IMPORT',   os.path.join(rootdir, 'instance/db/import'))
}

##Session
session_dir = os.path.join(rootdir, 'instance/sessions')
if not os.path.isdir(session_dir):
    os.makedirs(session_dir)

# Hack to make session play nice with the reloader (in debug mode)
s = web.session.Session(                    #def a session to stock log info
    app, web.session.DiskStore(session_dir),
    initializer={'logged_in':False,
        'username':'',
        'email':'',
        'last_uploaded_file':'',
        'result':'',
        'info_update':'',
        'semiauto_info_update':'',
        'return_uri':'',
        'err':'',
        'query':'',
        'queryshow':'',
        'querytbl':'',
        'queryinf':'',
        'temp_tables':set() })

# Enable automatic login (for testing purposes)
if os.environ.get('ADNIDB_AUTO_LOGIN', None) is not None:
    s._initializer['logged_in']=True


# Instance directory
        
s_data = s._initializer        #initialize the session

##Templates' folder
render = web.template.render('templates/',globals={'session':s})    #

###Function

##Read a html file and return it    
def read_text(filename):
    path='templates/'+filename+'.html'
    return open(path,'r').read()

#Create the dropdown for the query samples
def dropdown_query():    
    qL=get_query_list(False)
    dL=[('default','Choose a query')]
    for i,q in enumerate(qL):
        dL.append((str(i+1),q))
    return dL
    
#Create the list of all the query samples
def list_query():
    q=get_query_list(False)
    L=get_query_list(True)
    html='<div id="query-list"><ul>'
    for i,l in enumerate(L):
        html+='<li>'+q[i]+': '+l+'{}'.format('</li>' if i!=len(L)-1 else '</li></ul></div>')
    return html

#Upper the neo4j link words    
def query_upper(q):
    q=q.replace("<","&lt;")
    q=q.replace(">",'&gt;')
    q=q.replace('\n','</br>')
    q=q.replace('with','WITH')
    q=q.replace('where','WHERE')
    q=q.replace('match','MATCH')
    q=q.replace('case','CASE')
    q=q.replace('when','WHEN')
    q=q.replace('end','END')
    q=q.replace('then','THEN')
    q=q.replace('else','ELSE')
    q=q.replace('as','AS')
    q=q.replace('optional','OPTIONAL')
    q=q.replace('return','RETURN')
    q=q.replace('unwind','UNWIND')
    q=q.replace('collect','COLLECT')
    return q

#function to upload files
def upload_file(file,filedir,local_name=None):
    if 'myfile' in file: # to check if the file-object is created
        filepath=file.myfile.filename.replace('\\','/') # replaces the windows-style slashes with linux ones.
        filepath_base,filepath_ext = os.path.splitext(filepath)

        # Store either using the uploaded filename or user-passed in filename
        filename = filepath.split('/')[-1] if local_name is None else local_name + filepath_ext

        newfilepath=dir_path +'/tempfiles/'+ filename
        newfilepath=newfilepath.replace('\\','/') # replaces the windows-style slashes with linux ones.
        newfilename=newfilepath.split('/')[-1] # splits the and chooses the last part (the filename with extension)
        if not os.path.isdir(dir_path + '/tempfiles'):
            os.makedirs(dir_path + '/tempfiles')
        
        # Read the uploaded file
        file=file.myfile.file.read()

        # Writes the file to a new filename
        print('Saving uploaded file to ', newfilepath)
        fout = open(newfilepath,'wb') # creates the file where the uploaded file should be stored
        fout.write(file) # writes the uploaded file to the newly created file.
        fout.close() # closes the file, upload complete.
        
        if 'tsv' in filename:
            filepath=tsv2csv(newfilename,newfilepath)
            filename=newfilepath.split('/')[-1].replace('.tsv','.csv')
            for dir in filedir:
                fout = open(dir +'/'+ filename,"w",newline="") # creates the file where the uploaded file should be stored
                with open(filepath,'r') as file:
                    for line in file:
                        fout.write(line) 
                fout.close()
                
        elif 'FDG' in filename:
            filepath = FDG_preprocess(newfilepath)
            filename = filepath
            for dir in filedir:
                fout = open(dir +'/'+ filename,"w",newline="") # creates the file where the uploaded file should be stored
                with open(filepath,'r') as file:
                    for line in file:
                        fout.write(line) 
                fout.close()
                
        elif 'scanner_summary' in filename:
            filepath = summary_preprocess(newfilepath)
            filename = filepath
            for dir in filedir:
                fout = open(dir +'/'+ filename,"w",newline="") # creates the file where the uploaded file should be stored
                with open(filepath,'r') as file:
                    for line in file:
                        fout.write(line) 
                fout.close()
                
        else:
            for dir in filedir:
                fout = open(dir +'/'+ filename,"w",newline="") # creates the file where the uploaded file should be stored
                with open(newfilepath,'r') as file:
                    for line in file:
                        fout.write(line) 
                fout.close()
        
        os.remove(newfilepath)
        
    else:
        filepath=file.replace('\\','/')
        filename=filepath.split('/')[-1]
        print(filepath,filename)
        if 'tsv' in filename:
            filepath=tsv2csv(filename,filepath)
            filename=filepath.split('/')[-1].replace('.tsv','.csv')
            for dir in filedir:
                fout = open(dir +'/'+ filename,"w",newline="") # creates the file where the uploaded file should be stored
                with open(filepath,'r') as file:
                    for line in file:
                        fout.write(line) 
                fout.close()
                
        elif 'FDG' in filename:
            filepath = FDG_preprocess(filepath)
            filename = filepath
            for dir in filedir:
                fout = open(dir +'/'+ filename,"w",newline="") # creates the file where the uploaded file should be stored
                with open(filepath,'r') as file:
                    for line in file:
                        fout.write(line) 
                fout.close()
                
        elif 'scanner_summary' in filename:
            filepath = summary_preprocess(filepath)
            filename = filepath
            for dir in filedir:
                fout = open(dir +'/'+ filename,"w",newline="") # creates the file where the uploaded file should be stored
                with open(filepath,'r') as file:
                    for line in file:
                        fout.write(line) 
                fout.close()        
                
        else:
            for dir in filedir:
                fout = open(dir +'/'+ filename,'w',newline='') # creates the file where the uploaded file should be stored\\
                with open(filepath,'r',newline='') as file:
                    for line in file:
                        fout.write(line) 
                fout.close() # closes the file, upload complete.            
        
    return filename
    
###Form

##Query sample form    
querySForm=form.Form(
    form.Dropdown('Queries',
        dropdown_query(),
        form.notnull,
        form.Validator('Please, select a query',lambda f: f!='default'),
        onChange="printQuery()",
        id="Queries"),
    form.Button('Submit',type='submit',class_="pure-button"))
    
#Taken from source code of alfabis_server/app.py of paul yushkevich
class OAuthHelper:

    def __init__(self):
        self.flow = client.flow_from_clientsecrets(
            os.environ['ADNIDB_CLIENT_SECRET'],
            scope=[
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile'],
            redirect_uri=web.ctx.home+"/api/oauth2cb")

    def auth_url(self):
        return self.flow.step1_get_authorize_url()

    def authorize(self, auth_code):
        # Obtain credentials from the auth code
        self.credentials = self.flow.step2_exchange(auth_code)

        # Get use information from Google
        self.http_auth = self.credentials.authorize(httplib2.Http())
        user_info_service = build('oauth2','v2',http=self.http_auth)
        user_info = user_info_service.userinfo().get().execute()

        return user_info    
    
###Url Classes

##Def the homepage
class Index:  
    def GET(self):
        auth_url = None
        if s.logged_in == False:
            auth_url = OAuthHelper().auth_url()
        s.return_uri=web.ctx.home
        return render.page_style('index',text=read_text('index'),auth_url=auth_url)

class OAuthCallbackAPI:

    def GET(self):

    # Get the code from callback
        auth_code = web.input().code

        # Authorize via code
        user_info = OAuthHelper().authorize(auth_code)

        s.email = user_info.get('email')
        s.username = user_info.get('name')
        s.logged_in = True

        # Redirect to the home page
        raise web.seeother(s.return_uri)        
        
##Def the log out page
class Logout:
    def GET(self):
        s.kill()
        s.logged_in=False
        raise web.seeother('/')

##Def the query pages    
class Query:
    def GET(self,args):
        if args=='/sample':
            qf=querySForm()
            s.result=''
            return render.page_style('query',subpage=args,form=qf,text=list_query())
        
        if args=='/result':

            # Time to delete the temporary tables!
            for ttab in s.temp_tables:
                del_merge(ttab)
                filedir = [ config['ADNIDB_IMPORT_SAVEDIR'], config['ADNIDB_NEO4J_IMPORT'] ]
                for dir in filedir:
                    os.remove("%s/%s_temp.csv" % (dir, ttab))
            s.temp_tables = set()

            return render.page_style('query',subpage=args)

        if args=='/csv':
           csv_path = os.path.join(dir_path, 'savefile/result/final_result.csv') 
           web.header('Content-Disposition', 'attachment; filename="query_result.csv"')
           web.header('Content-type','text/csv')
           web.header('Content-transfer-encoding','binary') 
           return open(csv_path, 'rb').read()
        
        if args=='/tsv':
           csv_path = os.path.join(dir_path, 'savefile/result/final_result.tsv') 
           web.header('Content-Disposition', 'attachment; filename="query_result.tsv"')
           web.header('Content-type','text/tsv')
           web.header('Content-transfer-encoding','binary') 
           return open(csv_path, 'rb').read()
        
        if args=='/builder':
            return render.page_style('query',subpage=args,text=read_text('build')) 
        
        if args=='/show':
            return render.page_style('query',subpage=args)
        
        if args=='/merge':
            return render.page_style('query',subpage=args,text=read_text('merge'))
            
        if args=='/' or args=='':
            return render.page_style('query',subpage=args)
            
    def POST(self,args):
        if args=='/sample':    
            result_tbl=prettytable.PrettyTable()
            qf=querySForm()
            w=web.input()
            if not (qf.validates()):
                return render.page_style('query',subpage=args,form=qf,text=list_query())
            else:
                querynum=int(w['Queries'])
                q,tbl=query(querynum)
                write(q,tbl)
                csvfile=dir_path+"/savefile/result/"+'final_result.csv'
                input=open(csvfile,newline='')
                reader=csv.reader(input)
                result_tbl.field_names = [x.strip() for x in next(reader)]
                for row in reader:
                    result_tbl.add_row([x.strip() for x in row])
                s.result=(result_tbl.get_html_string(attributes={"id":"result-table","class":"pure-table pure-table-bordered","width":"100"}),get_query_list(True)[querynum-1])
                input.close()
                raise web.seeother('/query/result')
                
        if args=='/builder':
            qOptional = dict()
            qMajor = dict()
            qMerge = dict()
            w = web.input(major="", major_table="", majorOp=[], optional=[], optional0Op=[], optional1Op=[], 
                optional2Op=[], optional3Op=[], optional4Op=[], optional5Op=[], optional6Op=[],
                optional7Op=[], stdinfo =[])
                
            keys=list(w.keys())
            mergetemp = dict()
            qMajor[w.major_table] = w.majorOp
            
            if ('majdatesel' in keys): mergetemp['date'] = w.majdatesel
            else: mergetemp['date'] = ""
            if ('majviscodesel' in keys): mergetemp['viscode'] = w.majviscodesel
            else: mergetemp['viscode'] = ""    
                
            qMerge[w.major_table] = mergetemp

            for i, op in enumerate(w.optional):
                qOptional[op] = w["optional" + str(i) + "Op"]
                if ("custommerge" + str(i) in keys): 
                    if (w["merge" + str(i)] == "date"):    qMerge[op] = {w["merge" + str(i)]: [w["custommerge" + str(i)], w["datecustommerge" + str(i)]]}
                    else: qMerge[op] = {w["merge" + str(i)]: w["custommerge" + str(i)]}
                else: qMerge[op] = {w["merge" + str(i)]: ""}

            q, tbl = query_builder(qMajor, qOptional, qMerge, w.stdinfo)
            
            info = info_builder(qMajor, qOptional, qMerge, w.stdinfo)
            
            s.query = q
            s.queryshow = query_upper(q)
            s.querytbl = tbl
            s.queryinf = info

            # Also store the temporary table to delete
            if w.major_table.startswith("tmp_"):
                print(s.temp_tables, type(s.temp_tables), {w.major_table}, type({w.major_table}))
                if len(s.temp_tables) > 0:
                    s.temp_tables = s.temp_tables | { w.major_table }
                else:
                    s.temp_tables = { w.major_table }

            raise web.seeother('/query/show')
            
        if args=='/merge':
            result_tbl=prettytable.PrettyTable()
            w=web.input(myfile={},mergewith=[],datedl='',datedb=[])
            mergewith=w['mergewith']
            filedir = [ config['ADNIDB_IMPORT_SAVEDIR'], config['ADNIDB_NEO4J_IMPORT'] ]
            if w['myfile']!={}:
                dates = [x.strip() for x in w['datedl'].split(';')]
                
                filename=upload_file(w,filedir,local_name="tmp_" + uuid.uuid4().hex)
                input = filename.replace('.csv','')
                preprocess(filename,filedir)
                filename=filename.replace('.csv','_temp.csv')
                quoteCSV(filename, filedir)
                info = update_database([filename])
                if "TAUMETA" in filename: dx_haschanged(info)
                q,tbl,info=merge(input, mergewith, dates)
                
            else:
                dates = w["datedb"]
                input=w['dbfilemerge']
                q,tbl,info=merge(input, mergewith, dates)
                tbl.append(input)

            write(q,tbl)
            csvfile=dir_path+"/savefile/result/"+'final_result.csv'
            input=open(csvfile,newline='')
            reader=csv.reader(input)
            result_tbl.field_names = [x.strip() for x in next(reader)]
            for row in reader:
                result_tbl.add_row([x.strip() for x in row])
            s.result=(result_tbl.get_html_string(attributes={"id":"result-table","class":"pure-table pure-table-bordered"}),info)
            input.close()
            if w['myfile']!={}:
                del_merge(filename.replace('_temp.csv',''))
                for dir in filedir:
                    os.remove(dir+'/'+filename)
            raise web.seeother('/query/result')

        if args=="/show":
            q = s.query
            tbl = s.querytbl
            info = s.queryinf

            we = write(q, tbl)
            
            if we > 0:
                result_tbl = prettytable.PrettyTable()
                s.err = ""
                csvfile=dir_path+"/savefile/result/"+'final_result.csv'
                reader=csv.reader(open(csvfile,newline=''))
                result_tbl.field_names = [x.strip() for x in next(reader)]
                for row in reader:
                    result_tbl.add_row([x.strip() for x in row])
                s.result=(result_tbl.get_html_string(attributes={"id":"result-table","class":"pure-table pure-table-bordered"}), info)
                raise web.seeother('/query/result')
            
            elif we == 0:
                s.err = "This query did not return any data"
                
            else:
                s.err = "There was a construction error in this query. Make sure you did not try to merge with an empty property (i.e. you selected VISCODE but there's no available visit code for the main spreadsheet)."
                
            raise web.seeother('/query/builder')        
            
##Def the database update pages                    
class Update:
    def GET(self,args):
        if args=='/manual':
            return render.page_style('db_update',subpage=args,text=read_text('manual_update'))
        
        if args=='/dl_spreadsheet':
            return render.page_style('db_update',subpage=args,text=read_text('download_db'))
        
        return render.page_style('db_update',subpage=args)
    
    def POST(self,args):
        if args=='/manual':
            x = web.input(myfile={})
            filedir = [ config['ADNIDB_IMPORT_SAVEDIR'], config['ADNIDB_NEO4J_IMPORT'] ]
            filename=upload_file(x,filedir)            
            s.last_uploaded_file=filename
            preprocess(filename,filedir)
            filename=filename.replace('.csv','_temp.csv')
            quoteCSV(filename, filedir)
            info = update_database([filename])
            if "TAUMETA" in filename: dx_haschanged(info)
            s.info_update=info
            raise web.seeother('/db_update/manual')

##Def the 'about' page        
class About:
    def GET(self):
        return render.page_style('about')

##Def a temp page for ajax request
class Temp: 
    def GET(self,args):
        if "query_sample" in args:
            args=args.replace('/query_sample/','')
            q,tbl=query(int(args))
            q=query_upper(q)
            if "DXSUM" in tbl:
                tbl.remove("DXSUM")
                tbl.remove("PDXCONV")
                tbl.append("DXSUM_PDXCONV_ADNIALL")
            return q
            
        if "about" in args:
            csvfiles = [f.replace('_temp','') for f in os.listdir(dir_path+"/savefile/") if os.path.isfile(os.path.join(dir_path+"/savefile/", f))]
            csvfiles = sorted(csvfiles)
            info = db_info("about")
            return csvfiles,info
            
        if "dl_spreadsheet" in args:
            csvfiles = [f for f in os.listdir(dir_path+"/savefile/") if os.path.isfile(os.path.join(dir_path+"/savefile/", f))]
            csvfiles = sorted(csvfiles)
            return csvfiles
            
        if "build_info" in args:
            if "label" in args:
                temp = db_info("build_info")
                labels=[]
                for dict in temp:
                    if not dict['label']=='Person':
                        labels.append(dict['label'])
                labels=sorted(labels)
                return labels
    
    def POST(self, args):
        if "build_info" in args:
            if "prop" in args:
                x=web.input()
                print(x["label"])
                properties = prop(x["label"])
                properties.remove('RID')
                datevars=[x for x in properties if ("SCANDATE" in x.upper())]
                visvars=[x for x in properties if ("VISCODE2" in x.upper())]
                #return json.dumps(properties)
                return json.dumps({'label': x["label"], 'date':datevars, 'viscode':visvars, 'prop':properties})
                
            if "crit" in args:
                x=web.input()
                dcrit=dict()
                dcrit=crit(x["label"])
                return dcrit
                
            if "opvar" in args:
                x=web.input()
                labels=prop(x.csvname)
                if (x.type == "date"): vars = [x for x in labels if ("SCANDATE" in x.upper())]
                else: vars = [x for x in labels if ("VISCODE2" in x.upper())]
                return json.dumps(vars)

            if "upload" in args:
                w=web.input(myfile={})
                filedir = [ config['ADNIDB_IMPORT_SAVEDIR'], config['ADNIDB_NEO4J_IMPORT'] ]

                if w['myfile']!={}:
                    
                    # Assign the spreadsheet a temporary name
                    temp_name = "tmp_" + uuid.uuid4().hex

                    # Upload the file and add to database
                    filename=upload_file(w,filedir,local_name=temp_name)
                    preprocess(filename,filedir)
                    filename=filename.replace('.csv','_temp.csv')
                    quoteCSV(filename, filedir)
                    info = update_database([filename])
                    if "TAUMETA" in filename: dx_haschanged(info)

                    properties = prop(temp_name)
                    properties.remove('RID')
                    datevars=[x for x in properties if ("SCANDATE" in x.upper())]
                    visvars=[x for x in properties if ("VISCODE2" in x.upper())]
                    return json.dumps({'label': temp_name, 'date':datevars, 'viscode':visvars, 'prop':properties})

                else:
                    return None
                
        if "merge" in args:    
            if "datevar" in args:
                x=web.input()
                labels=prop(x["csvname"])
                datevars=[x for x in labels if ("SCANDATE" in x.upper())]
                return datevars
                
        if "dl_spreadsheet" in args:
            data = web.input()
            csvlist = list(data.keys())[0]
            csvlist = csvlist.replace('{"csvs":["','').replace('"]}','').split('","')
            temp = dict()
            temp['uri'] = []
            temp['name'] = []
            print('hiho')
            
            # Create a temporary zipfile for save
            zip = os.path.join(dir_path, 'savefile/result/spreadsheets.zip')
            with zipfile.ZipFile(zip, 'w') as myzip:
                for file in csvlist:
                    local_file = os.path.join(dir_path, 'savefile/%s.csv' % (file,))
                    filename = '{}.csv'.format(file.replace('_temp',''))
                    myzip.write(local_file, filename)

            # Send the zip file
            web.header('Content-Disposition', 'attachment; filename="spreadsheets.zip"')
            web.header('Content-type','application/zip')
            web.header('Content-transfer-encoding','binary') 
            return open(zip, 'rb').read()

application = app.wsgifunc()                            
if __name__=="__main__":
    app.run()
