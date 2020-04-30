from py2neo import Graph, Database, Node, Relationship
from meta_deta import result
import csv
import sys
import webbrowser
import os 
import json

#from query_typer import create_query3
db=Database("http://localhost:7474/browser")
graph=Graph(password="adni")
meta_file='DATADIC.csv'

#dir_path = os.path.dirname(os.path.realpath(__file__))

# TODO: there needs to be a consistent way to define instance path
dir_path = os.path.join(os.environ['ADNIDB_ROOT'], 'instance')

    #list of some of ADNI spreadsheets used for the db
csvfiles_list=['ADAS_ADNI1','ADAS_ADNIGO23','AMYMETA','AMYQC','APOE','ARM','AV45FOLLOW','AV45META','AV45QC','CDR',
    'DXSUM_PDXCONV_ADNIALL','GDSCALE','MEDHIST','MMSE','MOCA','MODHACH','MRI_INFARCTS',
    'MRI3META','MRIMETA','MRILIST','NEUROBAT','NPI','NPIQ','PET_META_LIST','PETMETA','PTDEMOG','TAUMETA','TAUQC',
    'UCBERKELEYAV45','UCBERKELEYAV1451','UCBERKELEYAV1451_PVC','UCD_ADNI1_WMH','UCD_ADNI2_WMH',
    'UPENNBIOMK','VITALS','MRI3TListWithNIFTIPath', 'TAU_fileloc', 'Amyloid_fileloc','stats_lr_cleanup','UCBERKELEYFDG',
    'APOERES','allvols','Mengjin_query']

    #helper for upload of files
def add_property(q,field_list):
    for field in field_list:
        q+="{}:row.{}, ".format(field,field)
    q+=" RID:row.RID}) \
        ON CREATE SET "
    for field in field_list:
        q+="n.{}=row.{}, ".format(field,field)
    q+=" n.RID=row.RID"
    return q

    #get a list with all the fields of a csv file 
def get_field_list(csv_file_name,field_list):
    filename=dir_path+"/savefile/"+csv_file_name
    f=csv.reader(open(filename,newline=''))
    #print(filename)
    #field_list=[]
    header=next(f)
    for field in header:
        if field!='RID' and field not in field_list:
            field_list.append(field)
    #return field_list
    
    ##Create the query to create a node 
    #csv_file_name : name of the .csv file where the data you need is 
    #node_type : type of Node you want to create; can be 'Person', 'Exam' (where all the diagnosis data are), 'TauPET' (TauPETScan data)
def create_query_node(csv_file_name,node_type):
            
    field_list=[]
    #field_list=get_field_list(csv_file_name)
    get_field_list(csv_file_name,field_list)
        
    q="load csv with headers from \"file:///" + csv_file_name +" \" as row "
    if node_type=='Person':
        q+="MERGE (n:Person{RID:row.RID})\
            ON CREATE SET n.RID = row.RID"    
    else:
        q+="MERGE (n:"+node_type+"{"
        q = add_property(q,field_list)
    print(q)
    return q

    ##Create the query to create a relationship b/w two nodes
    #node1_label, node2_label : nodes' labels 
    #matching_properties : properties you use to match the nodes (by default ['RID'])
def create_query_relationship(node1_label, node2_label, matching_properties=['RID']):
    q="MATCH (a:{}),(b:{}) WHERE ".format(node1_label,node2_label)
    for i,property in enumerate(matching_properties):
        q+="a.{}=b.{} {}".format(property, property, 'AND ' if i!=len(matching_properties)-1 else '  ')
    q+=" CREATE (a)-[:HAS {RID:b.RID, VISCODE2:b.VISCODE2}]->(b)"
    return q
    
    ##Update the database from different .csv files
    #csv_file_names : a list of csv files' name
def update_database(csv_file_names):
    tx=graph.begin()
    cursors = []
    for csv_file_name in csv_file_names:
        csv=csv_file_name.replace('_temp.csv','')
        for i,name in enumerate(csvfiles_list): 
            if csv.startswith(name):
                ind=i
        if 'ind' not in locals():
            csvfiles_list.append(csv)
            ind=len(csvfiles_list)-1
        csv = csvfiles_list[ind]    
        create_indexes(csv)
        cursors.append(tx.run(create_query_node(csv_file_name,'Person')))
        cursors.append(tx.run(create_query_node(csv_file_name,csv)))
        cursors.append(tx.run(create_query_relationship('Person',csv)))
        
    delete_duplicates(cursors,tx,csv)
    tx.commit()    
    info_dict={"contains_updates":False, "nodes_created":0, "relationships_created":0, "exectime":0}
    for cursor in cursors:
        stats=cursor.stats()
        exectime=0 # cursor.summary().result_available_after+cursor.summary().result_consumed_after
        if (stats["contained_updates"]):
            info_dict["contains_updates"]=True
            info_dict["nodes_created"]+=stats["nodes_created"]-stats["nodes_deleted"]
            info_dict["relationships_created"]+=stats["relationships_created"]-stats["relationships_deleted"]
            info_dict["exectime"]+=exectime
    return info_dict
    
    #remove potential duplicates from the db after a file upload
def delete_duplicates(cursors,tx,csv):
    #tx.run("MATCH (n:Person), (m:Person) WHERE n.RID = m.RID AND ID(n)<ID(m) detach delete m")
    cursors.append(tx.run("MATCH (n:TAUMETA), (m:TAUMETA) WHERE n.RID = m.RID AND ID(n)<ID(m) AND n.VISCODE2 = m.VISCODE2 AND n.ID=m.ID detach delete m")) #remove duplicate of TAUMETA nodes' who haven't scandate
    cursors.append(tx.run("MATCH (a:Person)-[r]->(b:{}) WITH a, type(r) as type, collect(r) as rels, b WHERE size(rels) > 1 UNWIND tail(rels) as rel DELETE rel".format(csv)))    
    cursors.append(tx.run("MATCH (t:TAUMETA) WHERE t.SCANDATE = \"\" REMOVE t.SCANDATE"))

    ##Create a new property for every TAUMETA nodes to know if the diagnosis of the subject has changed since his first tau scan
def dx_haschanged(dict):
    tx=graph.begin()
    cursors=[]
    cursors.append(tx.run("match (p:Person)-->(t:TAUMETA) \
    with  p.RID as rid,min(t.SCANDATE) as mindate \
    match P=(d:DXSUM_PDXCONV_ADNIALL)<--(p:Person{RID:rid})-->(t:TAUMETA{SCANDATE:mindate}) \
    where d.EXAMDATE<>\"\"     and d.VISCODE2=t.VISCODE2 \
    foreach(n in nodes(P) | set t.DX= \
    case when d.DIAGNOSIS<>\"\" then d.DIAGNOSIS else \
    case when d.DXCHANGE<>\"\" then d.DXCHANGE else \
    case when d.DXCONV<>\"\" then d.DXCONV else \"\" \
    end end end)"))
    cursors.append(tx.run("match (p:Person)-->(t:TAUMETA) \
    with  p.RID as rid,min(t.SCANDATE) as mindate \
    match P=(d:DXSUM_PDXCONV_ADNIALL)<--(p:Person{RID:rid})-->(t:TAUMETA{SCANDATE:mindate}) \
    where d.EXAMDATE<>\"\" and d.VISCODE2<>t.VISCODE2  and date(mindate)-duration('P1Y')<date(d.EXAMDATE) AND date(mindate)+duration('P1Y')>date(d.EXAMDATE) \
    foreach(n in nodes(P) | set t.DXCHANGED= \
    case when d.DIAGNOSIS<>\"\" and d.DIAGNOSIS=t.DX then 0 when d.DIAGNOSIS<>\"\" and d.DIAGNOSIS<>t.DX then 1 else \
    case when d.DXCHANGE<>\"\" and d.DXCHANGE=t.DX then 0 when d.DXCHANGE<>\"\" and d.DXCHANGE<>t.DX then 1 else \
    case when d.DXCONV<>\"\" and d.DXCONV=t.DX then 0 when d.DXCONV<>\"\" and d.DXCONV<>t.DX then 1 else 1 \
    end end end)"))
    tx.commit()
    for cursor in cursors:
        stats=cursor.stats()
        #print(type(cursor.summary()))
        exectime=0 # cursor.summary().result_available_after+cursor.summary().result_consumed_after
        if (stats["contained_updates"]):
            dict["contains_updates"]=True
            dict["nodes_created"]+=stats["nodes_created"]-stats["nodes_deleted"]
            dict["relationships_created"]+=stats["relationships_created"]-stats["relationships_deleted"]
            dict["exectime"]+=exectime
    return dict
    
    ##Create all the idexes of your database
def create_indexes(csv):
    indexes=graph.run("call db.indexes()").data()
    index_label=[]
    for i in range(len(indexes)):index_label.append(indexes[i]["tokenNames"])
    tx=graph.begin()
    if csv not in index_label and csv!="PET_META_LIST":
        tx.run("CREATE INDEX ON :{}(RID,VISCODE2)".format(csv))
    elif csv not in index_label and csv=="PET_META_LIST":
        tx.run("CREATE INDEX ON :{}(Subject)".format(csv))
    tx.commit()

    #create a spreadsheet from query result
def write(query,table):
    out_dir=os.path.join(dir_path, 'savefile/result')
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    with open(os.path.join(out_dir, 'result.csv'),'w',newline='') as r:
        try:
            data=graph.run(query).data()
        except Exception as e:
            s = str(e)
            data=[]
            return -1
        if data==[]: 
            return     0
        header=list(data[0].keys())
        writer=csv.DictWriter(r,fieldnames=header)
        writer.writeheader()
        writer.writerows(data)
        print('Done')
    result(dir_path+"/savefile/meta/"+meta_file,dir_path+"/savefile/result/"+'result.csv',table)
    return 1
    
    #remove temporary file used for a merging action
def del_merge(filename):
    tx=graph.begin()
    q1="match (n:{}) detach delete n".format(filename)
    q2="DROP INDEX ON :{}(RID, VISCODE2)".format(filename)
    tx.run(q1)
    tx.commit()
    try:
        tx=graph.begin()
        tx.run(q2)
        tx.commit()    
    except Exception as e:
        pass
   
    #return either entire information about the db or all the db labels
def db_info(arg):
    if arg=="about":
        info1=graph.run("MATCH (n) RETURN DISTINCT labels(n) as NodeType, count(*) AS SampleSize ORDER BY NodeType").data()
        info2=graph.run("MATCH ()-->() RETURN count(*) AS Relationships").data()
        info=info1+info2
    elif arg=="build_info":
        info=graph.run("call db.labels()").data()
    return info

    #return all the properties of one label
def prop(label):
    q = "match (n:{}) return keys(n) order by keys(n) limit 1".format(label)
    temp = graph.run(q).data()
    temp = temp[0]
    temp = temp["keys(n)"]
    info = sorted(temp)
    return info

    #create two lists of matching criteria for the query builder
def crit(label):
    crit = dict()
    if label == "PET_META_LIST":
        crit["PETTYPE"]={'match':['e','ne'], 'prop':["FDG/Other","Amyloid","TAU"]}
        crit["RIGHTONE"]={'match':[], 'prop':["No","Yes"]}
    elif label == "MRILIST":        
        crit["MRITYPE"]={'match':[], 'prop':["T1","T2"]}

    return json.dumps(crit)
