from database_v2 import dx_haschanged, write, get_field_list
import os

# TODO: there needs to be a consistent way to define instance path
dir_path = os.path.join(os.environ['ADNIDB_ROOT'], 'instance')


def return_all_properties(node_letter,csvfilename):
	savefiles=os.listdir(dir_path+"/savefile/")
	eligible=[]
	field_list=[]
	for csv in savefiles:
		if csvfilename in csv:eligible.append(csv)
	for file in eligible:
		get_field_list(file,field_list)
	q=", "
	for i,field in enumerate(field_list):
		if field!="ID":
			if field!="SCANDATE":
				q+="{}.{} as {}{} ".format(node_letter,field, field,',' if i<len(field_list)-1 else '')
			else:
				q+="{}.{} as SCANDATE{} ".format(node_letter,field,',' if i<len(field_list)-1 else '')
	return q
	
def query1(info):	
	q="MATCH (p:Person)-->(t:TAUMETA) \n\
	WITH p.RID AS rid,min(t.SCANDATE) AS mindate \n\
	MATCH (d:DXSUM_PDXCONV_ADNIALL{VISCODE2:t.VISCODE2})<--(p:Person{RID:rid})-->(t:TAUMETA{SCANDATE:mindate}) \n\
	RETURN toInteger(p.RID) AS RID, mindate AS TauPETScanDate, d.SCANDATE AS ExamDate, \n\
	case when d.DXCHANGE<>'' then d.DXCHANGE else d.DIAGNOSIS end as DXCHANGE, d.DXCONV AS DXCONV order by RID"
	if info==False:return q
	else:return "For all subjects with a tau PET scan, list their earliest tau scan and the nearest diagnosis in time."
		
def query2(info):
	q="MATCH (p:Person)-->(t:TAUMETA) \n\
	WITH  p.RID AS rid,min(t.SCANDATE) AS mindate \n\
	MATCH (d:DXSUM_PDXCONV_ADNIALL{VISCODE2:t.VISCODE2})<--(p:Person{RID:rid})-->(t:TAUMETA{SCANDATE:mindate}) WHERE t.DXCHANGED=0 OR NOT exists(t.DXCHANGED) \n\
	RETURN toInteger(p.RID) AS RID, mindate AS TauPETScanDate, d.SCANDATE AS ExamDate, case when d.DXCHANGE<>'' then d.DXCHANGE else d.DIAGNOSIS end as DXCHANGE, d.DXCONV AS DXCONV order by RID"
	if info==False:return q
	else:
		return "For all subjects with a tau PET scan, list their earliest tau scan and the nearest diagnosis in time. Exclude subjects whose diagnosis has changed from 1 year before to 1 year after the tau scan."

def query3(info):
	q="MATCH (p:Person)-->(t:TAUMETA) \n\
	WITH  p.RID AS rid,min(t.SCANDATE) AS mindate \n\
	MATCH (d:DXSUM_PDXCONV_ADNIALL{VISCODE2:t.VISCODE2})<--(p:Person{RID:rid})-->(t:TAUMETA{SCANDATE:mindate}) \n\
	OPTIONAL MATCH (p)--(n:NEUROBAT{VISCODE2:t.VISCODE2}) \n\
	OPTIONAL MATCH (p)--(m:MMSE{VISCODE2:t.VISCODE2}) \n\
	RETURN toInteger(p.RID) AS RID, mindate AS TauPETScanDate, d.SCANDATE AS ExamDate, \n\
	case when d.DXCHANGE<>'' then d.DXCHANGE else d.DIAGNOSIS end as DXCHANGE, d.DXCONV AS DXCONV, \n\
	n.AVDELTOT AS AVDELTOT, m.MMSCORE AS MMSCORE order by RID"
	if info==False:return q
	else:return "For all subjects with a tau PET scan, after you have listed their earliest tau scan and the nearest diagnosis in time, also add the nearest cognitive data."

def query4(info):
	q="MATCH (p:Person)--(m:MRI3META) \n\
	WHERE toInteger(p.RID)>1999 \n\
	return toInteger(p.RID) AS RID"
	q+=return_all_properties("m","MRI3META")
	q+="ORDER BY RID, SCANDATE"
	if info==False:return q
	else:return "Get all MRI scan information for subjects in ADNI2-GO-3 (RID>1999), sorted by RID then scandate."

def query5(info):
	q="MATCH (p:Person)--(P:PET_META_LIST) \n\
	WHERE toInteger(P.PETTYPE)=2 and toInteger(P.RIGHTONE)=1 \n\
	WITH p, P \n\
	OPTIONAL MATCH (p)--(tau:TAUMETA) \n\
	WHERE tau.SCANDATE=P.SCANDATE \n\
	RETURN toInteger(p.RID) AS RID, P.Subject AS ID, tau.VISCODE AS VISCODE, \n\
	case when tau.VISCODE2 is not null then tau.VISCODE2 \n\
	when tau.VISCODE='bl' then 'bl' else '' end AS VISCODE2, \n\
	P.PHASE AS PHASE, P.SCANDATE AS SCANDATE, P.Sequence AS SEQUENCE, P.StudyID AS STUDYID, P.SeriesID AS SERIESID, P.ImageID AS IMAGEID order by RID"
	if info==False:return q
	else: return "Get all the TAU scans with all informations"
	
def query6(info):
	q="match (p:Person)--(P:PET_META_LIST) \n\
	where toInteger(P.PETTYPE)=1 and toInteger(P.RIGHTONE)=1 \n\
	with p, P \n\
	optional match (p)--(av:AV45META{SCANDATE:P.SCANDATE}) \n\
	optional match (p)--(am:AMYMETA{SCANDATE:P.SCANDATE}) \n\
	with p, P, av, am \n\
	return toInteger(p.RID) as RID, P.Subject as ID, \n\
	case when av.VISCODE is not null then av.VISCODE else am.VISCODE end as VISCODE, \n\
	case when av.VISCODE2 is not  null then av.VISCODE2 else am.VISCODE2 end as VISCODE2, \n\
	P.PHASE as PHASE, P.SCANDATE as SCANDATE, P.Sequence as SEQUENCE, P.StudyID as STUDYID, P.SeriesID as SERIESID, P.ImageID as IMAGEID \n\
	order by RID"
	if info==False:return q
	else: return "Get all the Amyloid scans with all informations"
	
def query7(info):
	q="match (p:Person)--(P:PET_META_LIST) \n\
	where toInteger(P.PETTYPE)=0 and toInteger(P.RIGHTONE)=1 \n\
	with p, P \n\
	optional match (p)--(pet:PETMETA) where pet.SCANDATE=P.SCANDATE \n\
	return toInteger(p.RID) as RID, P.Subject as ID, pet.VISCODE as VISCODE, pet.VISCODE2 as VISCODE2, P.PHASE as PHASE, P.SCANDATE as SCANDATE, P.Sequence as SEQUENCE, P.StudyID as STUDYID, P.SeriesID as SERIESID, P.ImageID as IMAGEID order by RID"
	if info==False:return q
	else: return "Get all the FDG scans with all informations"	
	
def query8(info):
	q="match (p:Person)--(m:MRILIST) \n\
	where toInteger(m.MRITYPE)=0 \n\
	with p,m \n\
	match (p)--(M:MRI3META) \n\
	where M.SCANDATE=m.SCANDATE \n\
	with m.SCANDATE as sDate1, collect([m.IMAGEUID, m.T1ACCE]) as l1, max(m.IMAGEUID) as MAX1,min(m.IMAGEUID) as MIN1, m.PHASE as PHASE1, p, M.FIELD_STRENGTH as FIELD_STRENGTH, m.SUBJECT as ID, M.VISCODE as VISCODE, M.VISCODE2 as VISCODE2 \n\
	optional match (p)--(m:MRILIST) \n\
	where toInteger(m.MRITYPE)=1 and m.SCANDATE=sDate1 \n\
	with  p,collect(m.IMAGEUID) as l2, max(m.IMAGEUID) as MAX2, sDate1, l1, MAX1, MIN1, PHASE1, ID, FIELD_STRENGTH, VISCODE, VISCODE2 \n\
	return toInteger(p.RID) as RID, ID, FIELD_STRENGTH, PHASE1 as PHASE, VISCODE, VISCODE2, sDate1 as SCANDATE, \n\
	case when size(filter(x in l1 where x[1]='0' and x[0]<MAX1))>0 then filter(x in l1 where x[1]='0' and x[0]<MAX1)[0][0] \n\
	when size(filter(x in l1 where x[1]='0' and x[0]>MIN1))>0 then filter(x in l1 where x[1]='0' and x[0]>MIN1)[0][0] else filter(x in l1 where x[0]=MAX1)[0][0] end as IMAGUID_T1, \n\
	case when size(filter(x in l1 where x[1]='0' and x[0]<MAX1))>0 then 'N' \n\
	when size(filter(x in l1 where x[1]='0' and x[0]>MIN1))>0 then 'N' when size(filter(x in l1 where x[1]='0' and x[0]=MAX1))>0 then 'N' else 'Y' end as T1ISACCE, \n\
	case when size(filter(x in l2 where x=MAX2))>0 then filter(x in l2 where x=MAX2)[0] else '' end as IMAGUID_T2, \n\
	size(filter(x in l1 where x[1]<>'1')) as NT1NONEACCE, \n\
	case size(filter(x in l1 where x[1]<>'1')) when 1 then filter(x in l1 where x[1]<>'1')[0][0] when 0 then '' else filter(x in l1 where x[1]<>'1') end as IMAGEUID_T1NONEACCE, \n\
	size(filter(x in l1 where x[1]='1')) as NT1ACCE, \n\
	case size(filter(x in l1 where x[1]='1')) when 1 then filter(x in l1 where x[1]='1')[0][0] when 0 then '' else filter(x in l1 where x[1]='1') end as IMAGEUID_T1ACCE, \n\
	size(l2) as NT2, \n\
	case size(l2) when 1 then l2[0] when 0 then '' else l2 end as IMAGEUID_T2ALL \n\
	order by RID, SCANDATE"
	if info==False:return q
	else: return "Get all the MRI scans with all T1 and T2 informations"	
	
def query9(info):
	q="MATCH (p:PTDEMOG)--(n:Person) \n\
	WITH COLLECT([p.PTGENDER, p.PTDOBYY]) AS info, n \n\
	MATCH (n)--(d:DXSUM_PDXCONV_ADNIALL) \n\
	OPTIONAL MATCH (n)--(a:APOE{VISCODE:d.VISCODE}) \n\
	OPTIONAL MATCH (n)--(m:MMSE{VISCODE2:d.VISCODE2}) \n\
	OPTIONAL MATCH (n)--(c:CDR{VISCODE2:d.VISCODE2}) \n\
	RETURN toInteger(n.RID) AS RID, d.VISCODE2 AS VISCODE2,info[0][0] AS PTGENDER, \n\
	CASE WHEN d.SCANDATE<>'' THEN date(d.SCANDATE).year-toInteger(info[0][1]) ELSE '' END AS AGE_AT_VISIT, \n\
	case when d.DXCHANGE<>'' then d.DXCHANGE when d.DIAGNOSIS<>'' then d.DIAGNOSIS else d.DXCURREN end as DXCHANGE, \n\
	a.APVOLUME AS APVOLUME, a.APCOLLECT AS APCOLLECT, \n\
	a.APTIME AS APTIME, a.RNACOLL AS RNACOLL, a.RNADATE AS RNADATE, a.RNATIME AS RNATIME, a.RNAVOL AS RNAVOL, \n\
	m.MMSCORE AS MMSCORE, c.CDSOURCE AS CDSOURCE, c.CDVERSION AS CDVERSION, c.CDMEMORY AS CDMEMORY, c.CDORIENT AS CDORIENT, \n\
	c.CDJUDGE AS CDJUDGE, c.CDCOMMUN AS CDCOMMUN, c.CDHOME AS CDHOME, c.CDCARE AS CDCARE, c.CDGLOBAL AS CDGLOBAL, \n\
	c.CDRSB AS CDRSB, c.CDSOB AS CDSOB order by RID, AGE_AT_VISIT"
	if info==False:return q
	else: return "Age, sex, diagnosis, amyloid level, APOE status, and cognitive scores (MMSE, clinical dementia rating) for each visit (baseline, 3,6 months, and each year) of the ADNI subjects"

def query10(info):
	q="match (p:Person)--(P:PET_META_LIST) \n\
	where toInteger(P.PETTYPE)=2 \n\
	with collect(distinct p.RID) as rids \n\
	unwind rids as R \n\
	MATCH (p:Person{RID:R})--(d:DXSUM_PDXCONV_ADNIALL) \n\
	with max(d.SCANDATE) as maxdate,p \n\
	match (p)--(d:DXSUM_PDXCONV_ADNIALL{SCANDATE:maxdate}) \n\
	return toInteger(p.RID) as RID, \n\
	case when d.DXCHANGE<>'' then d.DXCHANGE else d.DIAGNOSIS end as DXCHANGE order by RID"
	
	if info==False:return q
	else:return "A spreadsheet with all Tau-PET scans and diagnosis information"

def query11(info):
	q="match (P:PET_META_LIST)--(p:Person)--(m:MRILIST) \n\
	where toInteger(m.MRITYPE)=0 and toInteger(P.PETTYPE)=1 and P.SCANDATE=m.SCANDATE \n\
	with collect(distinct p.RID) as rids \n\
	unwind rids as R \n\
	match (p:Person{RID:R})--(d:DXSUM_PDXCONV_ADNIALL) \n\
	with max(d.SCANDATE) as maxdate, p \n\
	match (p)--(d:DXSUM_PDXCONV_ADNIALL{SCANDATE:maxdate}) \n\
	return toInteger(p.RID) as RID, \n\
	case when d.DXCHANGE<>'' then d.DXCHANGE else d.DIAGNOSIS end as DXCHANGE order by RID"
	
	if info==False:return q
	else:return "A spreadsheet with all subjects with a T1 and a amyloid PET scan and diagnosis information"
	
def query12(info):
	q="match (p:Person)--(m:MRILIST) \n\
	where toInteger(m.MRITYPE)=1 \n\
	with collect(distinct p.RID) as rids \n\
	unwind rids as R \n\
	match (p:Person{RID:R})--(d:DXSUM_PDXCONV_ADNIALL) \n\
	with max(d.SCANDATE) as maxdate, p \n\
	match (p)--(d:DXSUM_PDXCONV_ADNIALL{SCANDATE:maxdate}) \n\
	return toInteger(p.RID) as RID, \n\
	case when d.DXCHANGE<>'' then d.DXCHANGE else d.DIAGNOSIS end as DXCHANGE order by RID"
	
	if info==False:return q
	else:return "A spreadsheet with all subjects with the high res T2 scan and diagnosis information"

def query13(info):
	q="MATCH (p:Person)--(t:TAU_fileloc) \n\
	WITH p, t \n\
	OPTIONAL MATCH (p)--(m:MRI3TListWithNIFTIPath) \n\
	WHERE toInteger(m.NT2)<>0 \n\
	WITH COLLECT([m,abs(toInt(substring(m.VISCODE2,1))-toInt(substring(t.VISCODE2,1)))]) AS T2, p, t \n\
	OPTIONAL MATCH (p)--(m:MRI3TListWithNIFTIPath) \n\
	WITH COLLECT([m,abs(toInt(substring(m.VISCODE2,1))-toInt(substring(t.VISCODE2,1)))]) AS T1, T2, p, t \n\
	OPTIONAL MATCH (p)--(a:Amyloid_fileloc) \n\
	WITH p, t, T1, T2, COLLECT([a,abs(toInt(substring(a.VISCODE2,1))-toInt(substring(t.VISCODE2,1))),abs(duration.inDays(date(t.SCANDATE),date(a.SCANDATE)).days)]) AS AMY \n\
	UNWIND extract(x in T2 | x[1]) AS T2diff \n\
	UNWIND extract(x in T1 | x[1]) AS T1diff \n\
	UNWIND extract(x in AMY | x[1]) AS AMYdiff \n\
	WITH p, t, T1, T2, min(T2diff) AS T2Min, min(T1diff) AS T1Min, AMY, min(AMYdiff) AS AMYmin \n\
	WITH p, t, T1, T2, T2Min, T1Min, AMY, AMYmin, \n\
	CASE WHEN (t.VISCODE2='bl' and size(filter(x in T2 WHERE (x[0]).VISCODE2='bl')[0][0])>0) THEN (filter(x in T2 WHERE (x[0]).VISCODE2='bl')[0][0]).SCANDATE \n\
	WHEN t.VISCODE2='bl' THEN (filter(x in T1 WHERE (x[0]).VISCODE2='bl')[0][0]).SCANDATE \n\
	WHEN size(filter(x in T2 WHERE x[1]=T2Min))>1 THEN (filter(x in T2 WHERE x[1]=T2Min)[-1][0]).SCANDATE \n\
	WHEN size(filter(x in T2 WHERE x[1]=T2Min))=1 THEN (filter(x in T2 WHERE x[1]=T2Min)[0][0]).SCANDATE \n\
	ELSE (filter(x in T1 WHERE x[1]=T1Min)[0][0]).SCANDATE END AS MRISCANDATE, \n\
	CASE WHEN t.VISCODE2='bl' THEN (filter(x in AMY WHERE (x[0]).VISCODE2='bl')[0][0]).SCANDATE \n\
	WHEN size(filter(x in AMY WHERE x[1]=AMYmin))>1 THEN (filter(x in AMY WHERE x[1]=AMYmin)[-1][0]).SCANDATE \n\
	when t.VISCODE2='' then case when size(filter(x in AMY WHERE x[2]<63))>0 then (filter(x in AMY WHERE x[2]<63)[0][0]).SCANDATE end \n\
	ELSE (filter(x in AMY WHERE x[1]=AMYmin)[0][0]).SCANDATE END AS AMYSCANDATE \n\
	RETURN toInteger(p.RID) AS RID, t.ID AS ID, t.VISCODE2 AS TAUVISCODE2, t.SCANDATE AS TAUSCANDATE, t.IMAGEID AS TAUIMAGEID, t.FILELOC AS TAUFILELOC, t.TAUNIFTI AS FINALTAUNIFTI, \n\
	MRISCANDATE, \n\
	CASE WHEN MRISCANDATE is not null THEN duration.inDays(date(MRISCANDATE),date(t.SCANDATE)).days ELSE '' END AS DIFFDATETAU, \n\
	CASE WHEN t.VISCODE2='bl' THEN 'bl' \n\
	WHEN size(filter(x in T2 WHERE x[1]=T2Min))>1 THEN (filter(x in T2 WHERE x[1]=T2Min)[-1][0]).VISCODE2 \n\
	WHEN size(filter(x in T2 WHERE x[1]=T2Min))=1 THEN (filter(x in T2 WHERE x[1]=T2Min)[0][0]).VISCODE2 \n\
	ELSE (filter(x in T1 WHERE x[1]=T1Min)[0][0]).VISCODE2 END AS MRIVISCODE2, \n\
	CASE WHEN t.VISCODE2='bl' THEN (filter(x in T2 WHERE (x[0]).VISCODE2='bl')[0][0]).IMAGEUID_T2ALL \n\
	WHEN size(filter(x in T2 WHERE x[1]=T2Min))>1 THEN (filter(x in T2 WHERE x[1]=T2Min)[-1][0]).IMAGEUID_T2ALL \n\
	ELSE (filter(x in T2 WHERE x[1]=T2Min)[0][0]).IMAGEUID_T2ALL END AS T2IMAGEUID, \n\
	CASE WHEN t.VISCODE2='bl' THEN (filter(x in T2 WHERE (x[0]).VISCODE2='bl')[0][0]).FINALT2NIFTI \n\
	WHEN size(filter(x in T2 WHERE x[1]=T2Min))>1 THEN (filter(x in T2 WHERE x[1]=T2Min)[-1][0]).FINALT2NIFTI \n\
	ELSE (filter(x in T2 WHERE x[1]=T2Min)[0][0]).FINALT2NIFTI END AS FINALT2NIFTI, \n\
	CASE WHEN t.VISCODE2='bl' THEN (filter(x in T1 WHERE (x[0]).VISCODE2='bl')[0][0]).IMAGEUID_T1 \n\
	WHEN (size(filter(x in T1 WHERE x[1]=T1Min))>1 and T1Min=T2Min) THEN (filter(x in T1 WHERE x[1]=T1Min)[-1][0]).IMAGEUID_T1 \n\
	WHEN (size(filter(x in T1 WHERE x[1]=T1Min))=1 and T1Min=T2Min) THEN (filter(x in T1 WHERE x[1]=T1Min)[0][0]).IMAGEUID_T1 \n\
	WHEN size(filter(x in T1 WHERE x[1]=T1Min))>1 THEN (filter(x in T1 WHERE x[1]=T1Min)[-1][0]).IMAGEUID_T1 \n\
	ELSE (filter(x in T1 WHERE x[1]=T1Min)[0][0]).IMAGEUID_T1 END AS T1IMAGEUID, \n\
	CASE WHEN t.VISCODE2='bl' THEN (filter(x in T1 WHERE (x[0]).VISCODE2='bl')[0][0]).FINALT1NIFTI \n\
	WHEN (size(filter(x in T1 WHERE x[1]=T1Min))>1 and T1Min=T2Min) THEN (filter(x in T1 WHERE x[1]=T1Min)[-1][0]).FINALT1NIFTI \n\
	WHEN (size(filter(x in T1 WHERE x[1]=T1Min))=1 and T1Min=T2Min) THEN (filter(x in T1 WHERE x[1]=T1Min)[0][0]).FINALT1NIFTI \n\
	WHEN size(filter(x in T1 WHERE x[1]=T1Min))>1 THEN (filter(x in T1 WHERE x[1]=T1Min)[-1][0]).FINALT1NIFTI \n\
	ELSE (filter(x in T1 WHERE x[1]=T1Min)[0][0]).FINALT1NIFTI END AS FINALT1NIFTI, \n\
	CASE WHEN t.VISCODE2='bl' THEN (filter(x in AMY WHERE (x[0]).VISCODE2='bl')[0][0]).VISCODE2 \n\
	WHEN size(filter(x in AMY WHERE x[1]=AMYmin))>1 THEN (filter(x in AMY WHERE x[1]=AMYmin)[-1][0]).VISCODE2 \n\
	when t.VISCODE2='' then case when size(filter(x in AMY WHERE x[2]<63))>0 then (filter(x in AMY WHERE x[2]<63)[0][0]).VISCODE2 end \n\
	ELSE (filter(x in AMY WHERE x[1]=AMYmin)[0][0]).VISCODE2 END AS AMYVISCODE2, \n\
	AMYSCANDATE, \n\
	CASE WHEN MRISCANDATE is not null THEN duration.inDays(date(MRISCANDATE),date(AMYSCANDATE)).days ELSE '' END AS DIFFDATEAMY, \n\
	CASE WHEN t.VISCODE2='bl' THEN (filter(x in AMY WHERE (x[0]).VISCODE2='bl')[0][0]).IMAGEID \n\
	WHEN size(filter(x in AMY WHERE x[1]=AMYmin))>1 THEN (filter(x in AMY WHERE x[1]=AMYmin)[-1][0]).IMAGEID \n\
	when t.VISCODE2='' then case when size(filter(x in AMY WHERE x[2]<63))>0 then (filter(x in AMY WHERE x[2]<63)[0][0]).IMAGEID end \n\
	ELSE (filter(x in AMY WHERE x[1]=AMYmin)[0][0]).IMAGEID END AS AMYIMAGEID, \n\
	CASE WHEN t.VISCODE2='bl' THEN (filter(x in AMY WHERE (x[0]).VISCODE2='bl')[0][0]).FILELOC \n\
	WHEN size(filter(x in AMY WHERE x[1]=AMYmin))>1 THEN (filter(x in AMY WHERE x[1]=AMYmin)[-1][0]).FILELOC \n\
	when t.VISCODE2='' then case when size(filter(x in AMY WHERE x[2]<63))>0 then (filter(x in AMY WHERE x[2]<63)[0][0]).FILELOC end \n\
	ELSE (filter(x in AMY WHERE x[1]=AMYmin)[0][0]).FILELOC END AS AMYFILELOC, \n\
	CASE WHEN t.VISCODE2='bl' THEN (filter(x in AMY WHERE (x[0]).VISCODE2='bl')[0][0]).AMYLOIDNIFTI \n\
	WHEN size(filter(x in AMY WHERE x[1]=AMYmin))>1 THEN (filter(x in AMY WHERE x[1]=AMYmin)[-1][0]).AMYLOIDNIFTI \n\
	when t.VISCODE2='' then case when size(filter(x in AMY WHERE x[2]<63))>0 then (filter(x in AMY WHERE x[2]<63)[0][0]).AMYLOIDNIFTI end \n\
	ELSE (filter(x in AMY WHERE x[1]=AMYmin)[0][0]).AMYLOIDNIFTI END AS FINALAmyNIFTI \n\
	order by RID" 
	if info==False:return q
	else:return "Using every available Tau PET scan available (one scan per subject in one row) as anchor, add a) information about the closest T2-MRI scan if available, b) information about the closest Amyloid PET scan."

def query14(info):
	q="match (p:Person)--(m:MRI3TListWithNIFTIPath) \n\
	where toInteger(m.NT2)<>0 \n\
	with p,m \n\
	optional match (p)--(a:Amyloid_fileloc) \n\
	with p, m, collect([a,abs(toInt(substring(a.VISCODE2,1))-toInt(substring(m.VISCODE2,1)))]) as AMY \n\
	unwind extract(x in AMY | x[1]) as AMYdiff \n\
	with p, m, AMY, min(AMYdiff) as AMYmin \n\
	return toInteger(p.RID) as RID, m.ID as ID, m.FIELD_STRENGTH as FIELD_STRENGTH, m.PHASE as PHASE, m.VISCODE2 as T2VISCODE2, m.SCANDATE as T2SCANDATE, m.IMAGEUID_T2ALL AS T2IMAGEUID, m.FINALT2NIFTI as FINALT2NIFTI, m.VENDOR2 as VENDOR, \n\
	case when m.VENDOR2<>m.VENDOR3 then toString(m.VENDOR2 + ' to '+ m.VENDOR3) else '' end as VENDORCHANGED, \n\
	m.MODEL2 as SCANMODEL, \n\
	case when m.VENDOR2=m.VENDOR3 and m.MODEL2<>m.MODEL3 then toString(m.MODEL2 + ' to '+ m.MODEL3) else '' end as MODELCHANGED, \n\
	case when m.VISCODE2='bl' then (filter(x in AMY where (x[0]).VISCODE2='bl')[0][0]).VISCODE2 \n\
	when size(filter(x in AMY where x[1]=AMYmin))>1 then (filter(x in AMY where x[1]=AMYmin)[-1][0]).VISCODE2 \n\
	else (filter(x in AMY where x[1]=AMYmin)[0][0]).VISCODE2 end as AMYVISCODE2, \n\
	case when m.VISCODE2='bl' then (filter(x in AMY where (x[0]).VISCODE2='bl')[0][0]).SCANDATE \n\
	when size(filter(x in AMY where x[1]=AMYmin))>1 then (filter(x in AMY where x[1]=AMYmin)[-1][0]).SCANDATE \n\
	else (filter(x in AMY where x[1]=AMYmin)[0][0]).SCANDATE end as AMYSCANDATE, \n\
	case when m.VISCODE2='bl' then (filter(x in AMY where (x[0]).VISCODE2='bl')[0][0]).IMAGEID \n\
	when size(filter(x in AMY where x[1]=AMYmin))>1 then (filter(x in AMY where x[1]=AMYmin)[-1][0]).IMAGEID \n\
	else (filter(x in AMY where x[1]=AMYmin)[0][0]).IMAGEID end as AMYIMAGEID, \n\
	case when m.VISCODE2='bl' then (filter(x in AMY where (x[0]).VISCODE2='bl')[0][0]).FILELOC \n\
	when size(filter(x in AMY where x[1]=AMYmin))>1 then (filter(x in AMY where x[1]=AMYmin)[-1][0]).FILELOC \n\
	else (filter(x in AMY where x[1]=AMYmin)[0][0]).FILELOC end as AMYFILELOC \n\
	order by RID, T2SCANDATE"
	if info==False:return q
	else:return "A spreadsheet of every T2-MRI scan available for every subject, adding the following columns: a) Scanner vendor, b) ADNI stage, c) Scanner vendor change (e.g. Siemens to GE), d) Scanner model change but same manufacturer, e) Scanner model. Also add information about the closest Amyloid PET scan."
	
def query15(info):
	q="MATCH (n:Person)--(p:PTDEMOG) \n\
	where n.RID in ['21', '59', '89', '150', '156', '301', '303', '377', '416', '454', '467', '501', '555', '566', '668', '677', '722', '746', '767', '800', '972', '1052', '1195', '1414', '1418', '2002', '2036', '2037', '2045', '2055', '2060', '2061', '2072', '2074', '2079', '2083', '2093', '2109', '2116', '2119', '2121', '2123', '2130', '2148', '2164', '2167', '2220', '2225', '2247', '2264', '2301', '2304', '2308', '2333', '2363', '2378', '2379', '2380', '2392', '4004', '4014', '4015', '4020', '4028', '4030', '4035', '4036', '4037', '4043', '4051', '4060', '4063', '4071', '4072', '4077', '4082', '4084', '4092', '4100', '4105', '4114', '4115', '4120', '4138', '4143', '4146', '4151', '4158', '4159', '4164', '4167', '4169', '4170', '4173', '4175', '4176', '4177', '4179', '4184', '4187', '4199', '4200', '4206', '4212', '4214', '4216', '4222', '4226', '4235', '4243', '4271', '4277', '4278', '4281', '4292', '4299', '4302', '4308', '4309', '4312', '4320', '4331', '4351', '4356', '4360', '4365', '4372', '4376', '4381', '4383', '4386', '4389', '4390', '4391', '4392', '4393', '4394', '4401', '4404', '4406', '4410', '4414', '4427', '4429', '4430', '4444', '4445', '4446', '4448', '4453', '4462', '4464', '4465', '4466', '4482', '4483', '4489', '4491', '4502', '4505', '4510', '4513', '4520', '4522', '4526', '4536', '4538', '4539', '4547', '4552', '4553', '4559', '4562', '4566', '4571', '4576', '4582', '4586', '4587', '4596', '4598', '4599', '4607', '4613', '4614', '4621', '4623', '4631', '4632', '4635', '4636', '4653', '4657', '4672', '4674', '4676', '4678', '4689', '4706', '4714', '4715', '4720', '4722', '4723', '4732', '4736', '4739', '4742', '4750', '4762', '4764', '4767', '4769', '4777', '4780', '4782', '4783', '4784', '4785', '4795', '4796', '4805', '4806', '4815', '4816', '4820', '4825', '4832', '4838', '4842', '4855', '4856', '4862', '4863', '4869', '4871', '4874', '4876', '4877', '4878', '4893', '4894', '4898', '4899', '4904', '4905', '4920', '4929', '4941', '4954', '4974', '4980', '4989', '5004', '5013', '5014', '5015', '5017', '5023', '5029', '5040', '5047', '5054', '5063', '5066', '5078', '5082', '5087', '5097', '5100', '5112', '5113', '5123', '5124', '5126', '5131', '5140', '5141', '5159', '5160', '5162', '5167', '5193', '5198', '5203', '5205', '5207', '5210', '5222', '5227', '5234', '5235', '5244', '5253', '5259', '5261', '5263', '5269', '5271', '5273', '5278', '5283', '5285', '5289', '5290', '5294'] \n\
	WITH COLLECT([p.PTGENDER, p.PTDOBYY, p.PTEDUCAT]) AS info, n \n\
	MATCH (n)--(d:DXSUM_PDXCONV_ADNIALL) \n\
	with max(d.SCANDATE) as maxDate, info, n \n\
	MATCH (n)--(d:DXSUM_PDXCONV_ADNIALL{SCANDATE:maxDate}) \n\
	with info, n, d \n\
	MATCH (n)--(m:MMSE{VISCODE2:d.VISCODE2}) \n\
	RETURN toInteger(n.RID) AS RID,info[0][0] AS PTGENDER, \n\
	CASE WHEN d.SCANDATE<>'' THEN date(d.SCANDATE).year-toInteger(info[0][1]) ELSE '' END AS PTAGE, \n\
	info[0][2] as PTEDUACTION, m.MMSCORE AS MMSCORE, \n\
	case when d.DXCHANGE<>'' then d.DXCHANGE else d.DIAGNOSIS end as DXCHANGE order by RID" 
	
	if info==False:return q
	else: return "Mengjin s query"
	
def query16(info):
	q="MATCH (n:Person)--(s:stats_lr_cleanup) \n\
	WITH s, n \n\
	OPTIONAL MATCH (n)--(p:PTDEMOG) \n\
	WITH COLLECT([p.PTGENDER,date({year:toInteger(p.PTDOBYY), month:toInteger(p.PTDOBMM)}), p.PTEDUCAT]) AS demoginfo, n, s \n\
	OPTIONAL MATCH (n)--(d:DXSUM_PDXCONV_ADNIALL) \n\
	WHERE s.TAUVISCODE2=d.VISCODE2 \n\
	WITH n,s,demoginfo,COLLECT([d.DIAGNOSIS,d.DXCHANGE,d.Phase,d.VISCODE,d.VISCODE2,d.SCANDATE]) AS dxinfo \n\
	OPTIONAL MATCH (n)--(f:UCBERKELEYFDG) \n\
	WHERE s.TAUVISCODE2=f.VISCODE2 \n\
	WITH n,s,demoginfo,dxinfo,f \n\
	OPTIONAL MATCH (n)--(a:APOERES) \n\
	WITH n,s,demoginfo,dxinfo,f,a \n\
	OPTIONAL MATCH (n)--(w2:UCD_ADNI2_WMH) \n\
	WITH n,s,demoginfo,dxinfo,f,a,COLLECT([w2,abs(toInt(substring(w2.VISCODE2,1))-toInt(substring(s.TAUVISCODE2,1))),w2.VISCODE2]) as wmh2 \n\
	OPTIONAL MATCH (n)--(w1:UCD_ADNI1_WMH) \n\
	WITH n,s,demoginfo,dxinfo,f,a,wmh2+COLLECT([w1,abs(toInt(substring(w1.VISCODE,1))-toInt(substring(s.TAUVISCODE2,1))),w1.VISCODE]) as WMH \n\
	UNWIND extract(x in WMH | x[1]) AS WMHdiff \n\
	WITH n,s,demoginfo,dxinfo,f,a,WMH,min(WMHdiff) as WMHmin \n\
	OPTIONAL MATCH (n)--(b:UCBERKELEYAV45) \n\
	WHERE s.TAUVISCODE2=b.VISCODE2 \n\
	WITH n,s,demoginfo,dxinfo,f,a,WMH,b,WMHmin \n\
	RETURN dxinfo[-1][2] as PHASE, dxinfo[-1][3] as VISCODE, dxinfo[-1][4] as VISCODE2, toInteger(s.RID) AS RID, s.ID as ID"
	q+=return_all_properties("s","stats_lr_cleanup_blanks")
	q+=", dxinfo[-1][5] as EXAMDATE, CASE WHEN demoginfo[0][0]='' THEN demoginfo[1][0] ELSE demoginfo[0][0] END AS PTGENDER, \n\
	CASE WHEN s.TAUSCANDATE<>'' THEN \n\
	CASE WHEN demoginfo[0][0]='' THEN duration.inMonths(demoginfo[1][1],date(s.TAUSCANDATE)).months/12.0 ELSE duration.inMonths(demoginfo[0][1],date(s.TAUSCANDATE)).months/12.0 END \n\
	ELSE '' END AS PTAGE, \n\
	CASE WHEN demoginfo[0][2]='' THEN demoginfo[1][2] ELSE demoginfo[0][2] END AS PTEDUCAT, \n\
	CASE when dxinfo[-1][1]<>'' then dxinfo[-1][1] else dxinfo[-1][0] end as DXCHANGE, f.LEFTANGULAR AS LEFTANGULAR, f.RIGHTANGULAR AS RIGHTANGULAR, \n\
	f.CINGULUMPOSTBILATERAL AS CINGULUMPOSTBILATERAL, f.LEFTTEMPORAL AS LEFTTEMPORAL, f.RIGHTTEMPORAL AS RIGHTTEMPORAL, \n\
	f.ADSIGNATURE AS ADSIGNATURE, a.APGEN1 AS APGEN1, a.APGEN2 AS APGEN2, a.APOE AS APOE, \n\
	CASE WHEN s.TAUSCANDATE<>'' THEN \n\
	CASE WHEN WMHmin is not null THEN (filter(x in WMH where x[1]=WMHmin)[0][0]).WHITMATHYP ELSE (filter(x in WMH where x[2]='bl')[0][0]).WHITMATHYP END \n\
	ELSE '' end as WHITMATHYP, \n\
	CASE WHEN s.TAUSCANDATE<>'' THEN \n\
	CASE WHEN WMHmin is not null THEN abs(duration.inDays(date(s.TAUSCANDATE),date((filter(x in WMH where x[1]=WMHmin)[0][0]).SCANDATE)).days) \n\
	WHEN size(filter(x in WMH where x[2]='bl'))>0 then abs(duration.inDays(date(s.TAUSCANDATE),date((filter(x in WMH where x[2]='bl')[0][0]).SCANDATE)).days) END \n\
	ELSE '' end as DIFFDATEWMH, \n\
	b.SUMMARYSUVR_WHOLECEREBNORM AS SUMMARYSUVR_WHOLECEREBNORM, b.SUMMARYSUVR_WHOLECEREBNORM_1_11CUTOFF AS SUMMARYSUVR_WHOLECEREBNORM_1_11CUTOFF \n\
	order by RID"
	if info==False:return q
	else: return "Test"
	
def query17(info):
	q="MATCH (n:Person)--(s:stats_lr_cleanup) \n\
	where s.MRISCANDATE<>'' \n\
	WITH s, n \n\
	OPTIONAL MATCH (n)--(p:PTDEMOG) \n\
	WITH COLLECT([p.PTGENDER,date({year:toInteger(p.PTDOBYY), month:toInteger(p.PTDOBMM)}), p.PTEDUCAT]) AS demoginfo, n, s \n\
	OPTIONAL MATCH (n)--(d:DXSUM_PDXCONV_ADNIALL) \n\
	WHERE s.TAUVISCODE2=d.VISCODE2 \n\
	WITH n,s,demoginfo,COLLECT([d.DIAGNOSIS,d.DXCHANGE]) AS dxinfo \n\
	OPTIONAL MATCH (n)--(f:UCBERKELEYFDG) \n\
	WHERE s.TAUVISCODE2=f.VISCODE2 \n\
	WITH n,s,demoginfo,dxinfo,f \n\
	OPTIONAL MATCH (n)--(a:APOERES) \n\
	WITH n,s,demoginfo,dxinfo,f,a \n\
	OPTIONAL MATCH (n)--(w2:UCD_ADNI2_WMH) \n\
	WITH n,s,demoginfo,dxinfo,f,a,COLLECT([w2,abs(toInt(substring(w2.VISCODE2,1))-toInt(substring(s.TAUVISCODE2,1))),w2.VISCODE2]) AS wmh2 \n\
	OPTIONAL MATCH (n)--(w1:UCD_ADNI1_WMH) \n\
	WITH n,s,demoginfo,dxinfo,f,a,wmh2+COLLECT([w1,abs(toInt(substring(w1.VISCODE,1))-toInt(substring(s.TAUVISCODE2,1))),w1.VISCODE]) AS WMH \n\
	UNWIND extract(x in WMH | x[1]) AS WMHdiff \n\
	WITH n,s,demoginfo,dxinfo,f,a,WMH,min(WMHdiff) AS WMHmin \n\
	OPTIONAL MATCH (n)--(b:UCBERKELEYAV45) \n\
	WHERE s.TAUVISCODE2=b.VISCODE2 \n\
	WITH n,s,demoginfo,dxinfo,f,a,WMH,b,WMHmin \n\
	optional match (p)--(v:allvols) \n\
	where date(v.bldate)=date(s.MRISCANDATE) \n\
	WITH n,s,demoginfo,dxinfo,f,a,WMH,b,WMHmin, v \n\
	RETURN toInteger(s.RID) AS RID, s.ID as ID"
	q+=return_all_properties("s","stats_lr_cleanup_blanks")
	q+=", CASE WHEN demoginfo[0][0]='' THEN demoginfo[1][0] ELSE demoginfo[0][0] END AS PTGENDER, \n\
	CASE WHEN s.TAUSCANDATE<>'' THEN \n\
	CASE WHEN demoginfo[0][0]='' THEN duration.inMonths(demoginfo[1][1],date(s.TAUSCANDATE)).months/12.0 ELSE duration.inMonths(demoginfo[0][1],date(s.TAUSCANDATE)).months/12.0 END \n\
	ELSE '' END AS PTAGE, \n\
	CASE WHEN demoginfo[0][2]='' THEN demoginfo[1][2] ELSE demoginfo[0][2] END AS PTEDUCAT, \n\
	CASE WHEN dxinfo[-1][1]<>'' THEN dxinfo[-1][1] ELSE dxinfo[-1][0] END AS DXCHANGE, f.LEFTANGULAR AS LEFTANGULAR, f.RIGHTANGULAR AS RIGHTANGULAR, \n\
	f.CINGULUMPOSTBILATERAL AS CINGULUMPOSTBILATERAL, f.LEFTTEMPORAL AS LEFTTEMPORAL, f.RIGHTTEMPORAL AS RIGHTTEMPORAL, \n\
	f.ADSIGNATURE AS ADSIGNATURE, a.APGEN1 AS APGEN1, a.APGEN2 AS APGEN2, a.APOE AS APOE, \n\
	CASE WHEN s.TAUSCANDATE<>'' THEN \n\
	CASE WHEN WMHmin is not null THEN (filter(x in WMH WHERE x[1]=WMHmin)[0][0]).WHITMATHYP ELSE (filter(x in WMH WHERE x[2]='bl')[0][0]).WHITMATHYP END \n\
	ELSE '' END AS WHITMATHYP, \n\
	CASE WHEN s.TAUSCANDATE<>'' THEN \n\
	CASE WHEN WMHmin is not null THEN abs(duration.inDays(date(s.TAUSCANDATE),date((filter(x in WMH WHERE x[1]=WMHmin)[0][0]).SCANDATE)).days) \n\
	WHEN size(filter(x in WMH WHERE x[2]='bl'))>0 THEN abs(duration.inDays(date(s.TAUSCANDATE),date((filter(x in WMH WHERE x[2]='bl')[0][0]).SCANDATE)).days) END \n\
	ELSE '' END AS DIFFDATEWMH, \n\
	b.SUMMARYSUVR_WHOLECEREBNORM AS SUMMARYSUVR_WHOLECEREBNORM, b.SUMMARYSUVR_WHOLECEREBNORM_1_11CUTOFF AS SUMMARYSUVR_WHOLECEREBNORM_1_11CUTOFF"
	q+=return_all_properties("v","allvols2")
	q+="order by RID"
	if info==False: return q
	else: return "Test 2: allvols+stats"

def query18(info):
	q="match (p:Person)--(q:Mengjin_query) \n\
	with p,q \n\
	match (p)--(P:PTDEMOG) \n\
	where P.VISCODE2='bl' \n\
	with COLLECT([date({year:toInteger(P.PTDOBYY), month:toInteger(P.PTDOBMM)}),date(P.USERDATE),P.PTEDUCAT,P.PTGENDER]) as demoginfo, p, q \n\
	optional match (p)--(d:DXSUM_PDXCONV_ADNIALL) \n\
	with p,q,demoginfo,COLLECT([abs(duration.inDays(date(q.SCANDATE),date(d.SCANDATE)).days),d.DIAGNOSIS,d.DXCHANGE,d.DXCURREN]) AS dxinfo \n\
	optional match (p)--(m:MMSE) \n\
	with p,q,demoginfo,dxinfo,COLLECT([abs(duration.inDays(date(q.SCANDATE),date(m.USERDATE)).days),m.MMSCORE]) AS mmseinfo \n\
	unwind extract(x in dxinfo | x[0]) as dxdiff \n\
	unwind extract(x in mmseinfo | x[0]) as mmsediff \n\
	with p,q,demoginfo,dxinfo,mmseinfo,min(dxdiff) as dxDate,min(mmsediff) as mmseDate \n\
	return toInteger(p.RID) as RID, q.ID as ID, q.SCANDATE as SCANDATE, demoginfo[0][-1] as PTGENDER, demoginfo[0][-2] as PTEDUCAT, \n\
	duration.inMonths(demoginfo[0][0],demoginfo[0][1]).months/12 as Age_at_bl, \n\
	case when filter(x in dxinfo where x[0]=dxDate)[0][2]<>'' then filter(x in dxinfo where x[0]=dxDate)[0][2]  \n\
	when filter(x in dxinfo where x[0]=dxDate)[0][1]<>'' then filter(x in dxinfo where x[0]=dxDate)[0][1] \n\
	else filter(x in dxinfo where x[0]=dxDate)[0][3] end as DXCHANGE, \n\
	filter(x in mmseinfo where x[0]=mmseDate)[0][-1] as MMSCORE \n\
	order by RID"
	if info==False: return q
	else: return "Mengjin s query 2"

def query19(info):
	q="match (n:Person)--(m:MRI3TListWithNIFTIPath) \n\
	with n,m \n\
	optional match (n)--(p:PTDEMOG)\n\
	WITH COLLECT([p.PTGENDER,date({year:toInteger(p.PTDOBYY), month:toInteger(p.PTDOBMM)}), p.PTEDUCAT]) AS demoginfo, n, m \n\
	OPTIONAL MATCH (n)--(d:DXSUM_PDXCONV_ADNIALL) \n\
	WHERE m.VISCODE2=d.VISCODE2 \n\
	WITH n,m,demoginfo,COLLECT([d.DIAGNOSIS,d.DXCHANGE,d.DXCURREN]) AS dxinfo \n\
	optional match (n)--(M:MMSE) \n\
	where m.VISCODE2=M.VISCODE2 \n\
	with n,m,demoginfo,dxinfo,M \n\
	return toInteger(n.RID) as RID"
	q+=return_all_properties("m","MRI3TListWithNIFTIPath")
	q+=", CASE WHEN demoginfo[0][0]='' THEN demoginfo[1][0] ELSE demoginfo[0][0] END AS PTGENDER, \n\
	CASE WHEN m.SCANDATE<>'' THEN \n\
	CASE WHEN demoginfo[0][0]='' THEN duration.inMonths(demoginfo[1][1],date(m.SCANDATE)).months/12.0 ELSE duration.inMonths(demoginfo[0][1],date(m.SCANDATE)).months/12.0 END \n\
	ELSE '' END AS PTAGE, \n\
	CASE WHEN demoginfo[0][2]='' THEN demoginfo[1][2] ELSE demoginfo[0][2] END AS PTEDUCAT, \n\
	CASE WHEN dxinfo[-1][1]<>'' THEN dxinfo[-1][1] WHEN dxinfo[-1][0]<>'' then dxinfo[-1][0] else dxinfo[-1][2] END AS DXCHANGE, \n\
	M.MMSCORE order by RID"
	if info==False: return q
	else: return "text"
	
def query20(info):
	q="MATCH (n:Person)--(s:stats_lr_cleanup) \n\
	WHERE s.MRISCANDATE<>'' and s.left_CA1_vol<>' ' \n\
	WITH COLLECT(s) as S, n \n\
	unwind extract(x in S | x.MRISCANDATE) as mridate \n\
	with S, n, mridate \n\
	MATCH (n)--(q:ToMergeWithQA_RI_updated) \n\
	WHERE q.T2_QC_R<>'missing' \n\
	with n, mridate, COLLECT([date(q.MRISCANDATE), q.PHASE, q.VISCODE, q.VISCODE2, q.T2_QC_R, q.T2_QC_L]) as Qdata, filter(x in S where x.MRISCANDATE=mridate)[0] as s \n\
	RETURN filter(x in Qdata where x[0]=date(mridate))[0][1] AS PHASE, toInteger(n.RID) AS RID, \n\
	filter(x in Qdata where x[0]=date(mridate))[0][2] AS VISCODE, filter(x in Qdata where x[0]=date(mridate))[0][3] AS VISCODE2, \n\
	s.ID AS ID, s.ICV AS ICV, s.Slice_Thickness AS SLICE_THICKNESS, s.MRISCANDATE AS MRIDATE, s.left_CA1_vol AS left_CA1_vol, s.left_CA1_ns AS left_CA1_ns, \n\
	CASE WHEN s.left_CA2_vol=' ' THEN 0 ELSE s.left_CA2_vol END AS left_CA2_vol, \n\
	CASE WHEN s.left_CA2_ns=' ' THEN 0 ELSE s.left_CA2_ns END AS left_CA2_ns, \n\
	s.left_CA3_vol AS left_CA3_vol, s.left_CA3_ns AS left_CA3_ns, s.left_DG_vol AS left_DG_vol, \n\
	s.left_DG_ns AS left_DG_ns, s.left_MISC_vol AS left_MISC_vol, s.left_MISC_ns AS left_MISC_ns, s.left_SUB_vol AS left_SUB_vol, s.left_SUB_ns AS left_SUB_ns, \n\
	s.left_ERC_vol AS left_ERC_vol, s.left_ERC_ns AS left_ERC_ns, s.left_BA35_vol AS left_BA35_vol, s.left_BA35_ns AS left_BA35_ns, s.left_BA36_vol AS left_BA36_vol, \n\
	s.left_BA36_ns AS left_BA36_ns, s.left_PHC_vol AS left_PHC_vol, s.left_PHC_ns AS left_PHC_ns, s.left_sulcus_vol AS left_sulcus_vol, s.left_sulcus_ns AS left_sulcus_ns, \n\
	s.left_CA_vol AS left_CA_vol, s.left_CA_ns AS left_CA_ns, \n\
	s.right_CA1_vol AS right_CA1_vol, s.right_CA1_ns AS right_CA1_ns, \n\
	CASE WHEN s.right_CA2_vol=' ' THEN 0 ELSE s.right_CA2_vol END AS right_CA2_vol, \n\
	CASE WHEN s.right_CA2_ns=' ' THEN 0 ELSE s.right_CA2_ns END AS right_CA2_ns, \n\
	s.right_CA3_vol AS right_CA3_vol, s.right_CA3_ns AS right_CA3_ns, s.right_DG_vol AS right_DG_vol, s.right_DG_ns AS right_DG_ns, \n\
	s.right_MISC_vol AS right_MISC_vol, s.right_MISC_ns AS right_MISC_ns, s.right_SUB_vol AS right_SUB_vol, s.right_SUB_ns AS right_SUB_ns, \n\
	s.right_ERC_vol AS right_ERC_vol, s.right_ERC_ns AS right_ERC_ns, s.right_BA35_vol AS right_BA35_vol, s.right_BA35_ns AS right_BA35_ns, \n\
	s.right_BA36_vol AS right_BA36_vol, s.right_BA36_ns AS right_BA36_ns, s.right_PHC_vol AS right_PHC_vol, s.right_PHC_ns AS right_PHC_ns, \n\
	s.right_sulcus_vol AS right_sulcus_vol, s.right_sulcus_ns AS right_sulcus_ns, s.right_CA_vol AS right_CA_vol, s.right_CA_ns AS right_CA_ns, \n\
	filter(x in Qdata where x[0]=date(mridate))[0][4] AS T2_QC_R, filter(x in Qdata where x[0]=date(mridate))[0][5] AS T2_QC_L \n\
	order by RID, MRIDATE"
	if info==False: return q
	else: return "ADNI PICSLASHS spreadsheet"
	
def query21(info):
	q="MATCH (n:Person)--(s:stats_lr_cleanup) \n\
	WITH s, n \n\
	MATCH (n)--(p:PTDEMOG) \n\
	WITH COLLECT([p.PTGENDER,date({year:toInteger(p.PTDOBYY), month:toInteger(p.PTDOBMM)}), p.PTEDUCAT]) AS demoginfo, n, s \n\
	MATCH (n)--(d:DXSUM_PDXCONV_ADNIALL) \n\
	WHERE s.TAUVISCODE2=d.VISCODE2 \n\
	WITH n,s,demoginfo,COLLECT([d.DIAGNOSIS,d.DXCHANGE,d.Phase,d.VISCODE,d.VISCODE2,d.SCANDATE]) AS dxinfo \n\
	optional match (n)--(m:MRI_cog_data) \n\
	where s.MRISCANDATE = m.MRIDATE_formatted \n\
	with n,s,demoginfo,dxinfo,m \n\
	RETURN dxinfo[-1][2] AS PHASE, dxinfo[-1][3] AS VISCODE, dxinfo[-1][4] AS VISCODE2, dxinfo[-1][5] AS EXAMDATE, toInteger(s.RID) AS RID, s.ID AS ID, \n\
	s.TAUVISCODE2 AS TAUVISCODE2, s.TAUSCANDATE AS TAUSCANDATE, s.TAUIMAGEID AS TAUIMAGEID, s.TAUFILELOC AS TAUFILELOC, s.FINALTAUNIFTI AS FINALTAUNIFTI, \n\
	s.MRISCANDATE AS MRISCANDATE, s.DIFFDATETAU AS DIFFDATETAU, s.MRIVISCODE2 AS MRIVISCODE2, s.T2IMAGEUID AS T2IMAGEUID, s.FINALT2NIFTI AS FINALT2NIFTI, \n\
	s.T1IMAGEUID AS T1IMAGEUID, s.FINALT1NIFTI AS FINALT1NIFTI, s.AMYVISCODE2 AS AMYVISCODE2, s.AMYSCANDATE AS AMYSCANDATE, s.DIFFDATEAMY AS DIFFDATEAMY, \n\
	s.AMYIMAGEID AS AMYIMAGEID, s.AMYFILELOC AS AMYFILELOC, s.FINALAmyNIFTI AS FINALAmyNIFTI, \n\
	CASE WHEN demoginfo[0][0]='' THEN demoginfo[1][0] ELSE demoginfo[0][0] END AS PTGENDER, \n\
	CASE WHEN s.TAUSCANDATE<>'' THEN \n\
	CASE WHEN demoginfo[0][0]='' THEN duration.inMonths(demoginfo[1][1],date(s.TAUSCANDATE)).months/12.0 ELSE duration.inMonths(demoginfo[0][1],date(s.TAUSCANDATE)).months/12.0 END \n\
	ELSE '' END AS PTAGE, \n\
	CASE WHEN demoginfo[0][2]='' THEN demoginfo[1][2] ELSE demoginfo[0][2] END AS PTEDUCAT, \n\
	CASE WHEN dxinfo[-1][1]<>'' THEN dxinfo[-1][1] ELSE dxinfo[-1][0] END AS DXCHANGE, \n\
	m.T2_QC_R as T2_QC_R, m.T2_QC_L as T2_QC_L \n\
	order by RID"
	if info==False: return q
	else: return "Spreasheet to merge with QA"
	
def query22(info):
	q="match (p:Person)--(n:no_stat_temp) \n\
	with p,n \n\
	optional match (p)--(P:PTDEMOG) \n\
	where P.VISCODE2='bl' \n\
	with COLLECT([date({year:toInteger(P.PTDOBYY), month:toInteger(P.PTDOBMM)}),date(P.USERDATE),P.PTEDUCAT,P.PTGENDER]) AS demoginfo, p, n \n\
	optional match (p)--(d:DXSUM_PDXCONV_ADNIALL) \n\
	where d.VISCODE2='bl' \n\
	with p,n,demoginfo,COLLECT([d.DIAGNOSIS,d.DXCHANGE,d.DXCURREN]) AS dxinfo \n\
	OPTIONAL MATCH (p)--(m:MMSE) \n\
	where m.VISCODE2='bl' \n\
	WITH p,n,demoginfo,dxinfo,m \n\
	RETURN toInteger(p.RID) AS RID, n.ID AS ID, demoginfo[0][-1] AS PTGENDER, demoginfo[0][-2] AS PTEDUCAT, \n\
	duration.inMonths(demoginfo[0][0],demoginfo[0][1]).months/12.0 AS Age_at_bl, \n\
	CASE WHEN dxinfo[0][2]<>'' THEN dxinfo[0][2] WHEN dxinfo[0][0]<>'' THEN dxinfo[0][0] ELSE dxinfo[0][1] END AS DXCHANGE, \n\
	m.MMSCORE AS MMSCORE \n\
	order by RID"
	if info==False: return q
	else: return "Mengjin query 3"
	
def query23(info):
	q="MATCH (p:Person)--(t:T2Tau) \n\
	WITH p,t \n\
	match (p)--(d:DXSUM_PDXCONV_ADNIALL) \n\
	with p, t, COLLECT([abs(duration.inDays(date(d.SCANDATE),date(t.MRIDATE)).days), d.VISCODE2]) AS list2 \n\
	UNWIND extract(x in list2 | x[0]) AS datediff \n\
	WITH p, t, list2, min(datediff) AS min \n\
	OPTIONAL MATCH (p)--(n:NEUROBAT) \n\
	WITH p, t, list2, min, COLLECT([n.VISCODE2,  n.AVDEL30MIN, n.AVTOT1, n.AVTOT6, n.AVDELTOT, n.AVDELERR2]) AS list, filter(x in list2 where x[0]=min)[0][1] as VISCODE2_DX \n\
	RETURN toInteger(p.RID) AS RID"
	q+=return_all_properties("t","T2Tau")
	q+=", case when size(filter(x in list where x[0]=VISCODE2_DX and x[4]<>''))>0 then filter(x in list where x[0]=VISCODE2_DX and x[4]<>'')[0][0] \n\
	else filter(x in list where x[4]<>'')[-1][0]  end  AS VISCODE2_NEURO, \n\
	case when size(filter(x in list where x[0]=VISCODE2_DX and x[4]<>''))>0 then min \n\
	else filter(x in list2 where x[1]=filter(x in list where x[4]<>'')[-1][0])[0][0]  end  AS DATE_DIFF_DX, \n\
	case when size(filter(x in list where x[0]=VISCODE2_DX and x[4]<>''))>0 then filter(x in list where x[0]=VISCODE2_DX and x[4]<>'')[0][1] \n\
	else filter(x in list where x[4]<>'')[-1][1]  end  AS AVDEL30MIN_new, \n\
	case when size(filter(x in list where x[0]=VISCODE2_DX and x[4]<>''))>0 then filter(x in list where x[0]=VISCODE2_DX and x[4]<>'')[0][2] \n\
	else filter(x in list where x[4]<>'')[-1][2]  end as AVTOT1_new, \n\
	case when size(filter(x in list where x[0]=VISCODE2_DX and x[4]<>''))>0 then filter(x in list where x[0]=VISCODE2_DX and x[4]<>'')[0][3] \n\
	else filter(x in list where x[4]<>'')[-1][3]  end as AVTOT6_new, \n\
	case when size(filter(x in list where x[0]=VISCODE2_DX and x[4]<>''))>0 then filter(x in list where x[0]=VISCODE2_DX and x[4]<>'')[0][4] \n\
	else filter(x in list where x[4]<>'')[-1][4]  end as AVDELTOT_new, \n\
	case when size(filter(x in list where x[0]=VISCODE2_DX and x[4]<>''))>0 then filter(x in list where x[0]=VISCODE2_DX and x[4]<>'')[0][5] \n\
	else filter(x in list where x[4]<>'')[-1][5]  end as AVDELERR2_new \n\
	order by RID"
	if info==False: return q
	else: return "Add AVDEL30MIN to T2Tau spreadsheet"

def query24(info):
	q="MATCH (n:Person)--(s:stats_lr_cleanup) \n\
	WITH s, n \n\
	MATCH (n)--(p:PTDEMOG) \n\
	WITH COLLECT([p.PTGENDER,date({year:toInteger(p.PTDOBYY), month:toInteger(p.PTDOBMM)}), p.PTEDUCAT]) AS demoginfo, n, s \n\
	MATCH (n)--(d:DXSUM_PDXCONV_ADNIALL) \n\
	WHERE s.TAUVISCODE2=d.VISCODE2 \n\
	WITH n,s,demoginfo,COLLECT([d.DIAGNOSIS,d.DXCHANGE,d.Phase,d.VISCODE,d.VISCODE2,d.SCANDATE]) AS dxinfo \n\
	OPTIONAL MATCH (n)--(m:MRI_cog_data) \n\
	WHERE s.MRISCANDATE = m.MRIDATE_formatted \n\
	WITH n,s,demoginfo,dxinfo,m \n\
	optional match (n)--(a:ADNI_scanner_summary) \n\
	where date(a.seriesdate)=date(s.MRISCANDATE) \n\
	with n,s,demoginfo,dxinfo,m,a \n\
	RETURN dxinfo[-1][2] AS PHASE, dxinfo[-1][3] AS VISCODE, dxinfo[-1][4] AS VISCODE2, dxinfo[-1][5] AS EXAMDATE, toInteger(s.RID) AS RID, s.ID AS ID, \n\
	s.TAUVISCODE2 AS TAUVISCODE2, s.TAUSCANDATE AS TAUSCANDATE, s.TAUIMAGEID AS TAUIMAGEID, s.TAUFILELOC AS TAUFILELOC, s.FINALTAUNIFTI AS FINALTAUNIFTI, \n\
	s.MRISCANDATE AS MRISCANDATE, s.DIFFDATETAU AS DIFFDATETAU, s.MRIVISCODE2 AS MRIVISCODE2, s.T2IMAGEUID AS T2IMAGEUID, s.FINALT2NIFTI AS FINALT2NIFTI, \n\
	s.T1IMAGEUID AS T1IMAGEUID, s.FINALT1NIFTI AS FINALT1NIFTI, s.AMYVISCODE2 AS AMYVISCODE2, s.AMYSCANDATE AS AMYSCANDATE, s.DIFFDATEAMY AS DIFFDATEAMY, \n\
	s.AMYIMAGEID AS AMYIMAGEID, s.AMYFILELOC AS AMYFILELOC, s.FINALAmyNIFTI AS FINALAmyNIFTI, \n\
	CASE WHEN demoginfo[0][0]='' THEN demoginfo[1][0] ELSE demoginfo[0][0] END AS PTGENDER, \n\
	CASE WHEN s.TAUSCANDATE<>'' THEN \n\
	CASE WHEN demoginfo[0][0]='' THEN duration.inMonths(demoginfo[1][1],date(s.TAUSCANDATE)).months/12.0 ELSE duration.inMonths(demoginfo[0][1],date(s.TAUSCANDATE)).months/12.0 END \n\
	ELSE '' END AS PTAGE, \n\
	CASE WHEN demoginfo[0][2]='' THEN demoginfo[1][2] ELSE demoginfo[0][2] END AS PTEDUCAT, \n\
	CASE WHEN dxinfo[-1][1]<>'' THEN dxinfo[-1][1] ELSE dxinfo[-1][0] END AS DXCHANGE, \n\
	m.T2_QC_R AS T2_QC_R, m.T2_QC_L AS T2_QC_L, a.Manufacterer as Manufacturer, a.model as model, a.software_version as software_version, a.HeadCoil as HeadCoil \n\
	order by RID"
	if info==False: return q
	else: return "Spreasheet merged with QA and provenance information"

def query25(info):
	q="match (n:Person)--(s:ToMergeWithQA_RI_updated) \n\
	with n, s \n\
	optional match (n)--(a:ADNI_scanner_summary) \n\
	where date(a.seriesdate)=date(s.MRISCANDATE) \n\
	return s.PHASE AS PHASE, s.VISCODE AS VISCODE, s.VISCODE2 AS VISCODE2, s.SCANDATE AS EXAMDATE, toInteger(s.RID) AS RID, s.ID AS ID, \n\
	s.TAUVISCODE2 AS TAUVISCODE2, s.TAUSCANDATE AS TAUSCANDATE, s.TAUIMAGEID AS TAUIMAGEID, s.TAUFILELOC AS TAUFILELOC, s.FINALTAUNIFTI AS FINALTAUNIFTI, \n\
	s.MRISCANDATE AS MRISCANDATE, s.DIFFDATETAU AS DIFFDATETAU, s.MRIVISCODE2 AS MRIVISCODE2, s.T2IMAGEUID AS T2IMAGEUID, s.FINALT2NIFTI AS FINALT2NIFTI, \n\
	s.T1IMAGEUID AS T1IMAGEUID, s.FINALT1NIFTI AS FINALT1NIFTI, s.AMYVISCODE2 AS AMYVISCODE2, s.AMYSCANDATE AS AMYSCANDATE, s.DIFFDATEAMY AS DIFFDATEAMY, \n\
	s.AMYIMAGEID AS AMYIMAGEID, s.AMYFILELOC AS AMYFILELOC, s.FINALAmyNIFTI AS FINALAmyNIFTI, s.PTGENDER as PTGENDER, s.PTAGE as PTAGE, s.PTEDUCAT as PTEDUCAT, \n\
	s.DIAGNOSIS as DXCHANGE, s.T2_QC_R AS T2_QC_R, s.T2_QC_L AS T2_QC_L, a.Manufacterer as Manufacturer, a.model as model, a.software_version as software_version, \n\
	a.HeadCoil as HeadCoil order by RID"
	if info==False: return q
	else: return "QA spreadsheet with all QC information"
	
def query26(info):
	q="MATCH (n:Person)--(s:stats_lr_cleanup) \n\
	WITH s, n \n\
	MATCH (n)--(p:PTDEMOG) \n\
	WITH COLLECT([p.PTGENDER,date({year:toInteger(p.PTDOBYY), month:toInteger(p.PTDOBMM)}), p.PTEDUCAT]) AS demoginfo, n, s \n\
	MATCH (n)--(d:DXSUM_PDXCONV_ADNIALL) \n\
	WHERE s.TAUVISCODE2=d.VISCODE2 \n\
	WITH n,s,demoginfo,COLLECT([d.DIAGNOSIS,d.DXCHANGE,d.Phase,d.VISCODE,d.VISCODE2,d.SCANDATE]) AS dxinfo \n\
	MATCH (n)--(q:ToMergeWithQA_RI_updated) \n\
	WHERE date(s.MRISCANDATE) = date(q.MRISCANDATE) \n\
	WITH n,s,demoginfo,dxinfo,COLLECT([q.T2_QC_R, q.T2_QC_L]) as qcinfo \n\
	MATCH (n)--(a:ADNI_scanner_summary) \n\
	WHERE date(a.seriesdate)=date(s.MRISCANDATE) \n\
	WITH n,s,demoginfo,dxinfo,qcinfo,a \n\
	optional match (n)--(b:NEUROBAT) \n\
	where b.VISCODE2=s.TAUVISCODE2 and b.AVDEL30MIN<>'' \n\
	with n,s,demoginfo,dxinfo,qcinfo,a,b \n\
	RETURN dxinfo[-1][2] AS PHASE, dxinfo[-1][3] AS VISCODE, dxinfo[-1][4] AS VISCODE2, dxinfo[-1][5] AS EXAMDATE, toInteger(s.RID) AS RID"  
	q+=return_all_properties("s","stats_lr_cleanup_blanks")
	q+=", CASE WHEN demoginfo[0][0]='' THEN demoginfo[1][0] ELSE demoginfo[0][0] END AS PTGENDER, \n\
	CASE WHEN s.TAUSCANDATE<>'' THEN \n\
	CASE WHEN demoginfo[0][0]='' THEN duration.inMonths(demoginfo[1][1],date(s.TAUSCANDATE)).months/12.0 ELSE duration.inMonths(demoginfo[0][1],date(s.TAUSCANDATE)).months/12.0 END \n\
	ELSE '' END AS PTAGE, \n\
	CASE WHEN demoginfo[0][2]='' THEN demoginfo[1][2] ELSE demoginfo[0][2] END AS PTEDUCAT, \n\
	CASE WHEN dxinfo[-1][1]<>'' THEN dxinfo[-1][1] ELSE dxinfo[-1][0] END AS DXCHANGE, \n\
	qcinfo[0][0] AS T2_QC_R, qcinfo[0][1] AS T2_QC_L, \n\
	a.Manufacterer AS Manufacturer, a.model AS model, a.software_version AS software_version, a.HeadCoil AS HeadCoil, \n\
	b.AVDEL30MIN as AVDEL30MIN, b.AVTOT1 as AVTOT1, b.AVTOT6 as AVTOT6, b.AVDELTOT as AVDELTOT, b.AVDELERR2 as AVDELERR2 \n\
	order by RID"
	if info==False: return q
	else: return "QA spreadsheet with all QC information, all analysis information and cognitive information"

def query27(info):
	q="MATCH (n:Person)--(v:allvols) \n\
	WHERE v.bldate<>'' \n\
	WITH n, v \n\
	MATCH (n)--(p:PTDEMOG) \n\
	WITH COLLECT([p.PTGENDER,date({year:toInteger(p.PTDOBYY), month:toInteger(p.PTDOBMM)}), p.PTEDUCAT]) AS demoginfo, n, v \n\
	OPTIONAL MATCH (n)--(d:DXSUM_PDXCONV_ADNIALL) \n\
	WHERE d.SCANDATE<>'' \n\
	WITH n, v, demoginfo, COLLECT([abs(duration.inDays(date(v.bldate),date(d.SCANDATE)).days), d.DXCHANGE, d.DIAGNOSIS, d.DXCURREN, abs(duration.inDays(date(v.fudate),date(d.SCANDATE)).days), d.VISCODE2, d.Phase]) AS dxinfo \n\
	UNWIND extract(x in dxinfo | x[0]) AS bldxdiff \n\
	UNWIND extract(x in dxinfo | x[4]) AS fudxdiff \n\
	WITH n, v, demoginfo, dxinfo, min(bldxdiff) AS minbldx, min(fudxdiff) AS minfudx \n\
	OPTIONAL MATCH (n)--(a:ADNI_scanner_summary) \n\
	WITH n, v, demoginfo, dxinfo,  minbldx, minfudx, COLLECT([abs(duration.inDays(date(v.bldate),date(a.seriesdate)).days), abs(duration.inDays(date(v.fudate),date(a.seriesdate)).days), a]) AS prinfo, \n\
	filter(x in dxinfo WHERE x[0]=minbldx)[0][5] AS VISCODE2_bl, filter(x in dxinfo WHERE x[4]=minfudx)[0][5] AS VISCODE2_fu \n\
	UNWIND extract(x in prinfo | x[0]) AS blprdiff \n\
	UNWIND extract(x in prinfo | x[1]) AS fuprdiff \n\
	WITH n, v, demoginfo, dxinfo,  minbldx, minfudx, prinfo, VISCODE2_bl, VISCODE2_fu, min(blprdiff) AS minblpr, min(fuprdiff) AS minfupr \n\
	MATCH (n)--(c:NEUROBAT) \n\
	WHERE c.AVDEL30MIN<>'' \n\
	WITH n, v, demoginfo, dxinfo,  minbldx, minfudx, prinfo, VISCODE2_bl, VISCODE2_fu, minblpr, minfupr, COLLECT([c.VISCODE2, c.AVDEL30MIN, c.AVTOT1, c.AVTOT6, c.AVDELTOT, c.AVDELERR2]) AS coginfo \n\
	RETURN toInteger(n.RID) AS RID, \n\
	CASE WHEN demoginfo[0][0]='' THEN demoginfo[1][0] ELSE demoginfo[0][0] END AS PTGENDER, \n\
	CASE WHEN v.bldate<>'' THEN \n\
	CASE WHEN demoginfo[0][0]='' THEN duration.inMonths(demoginfo[1][1],date(v.bldate)).months/12.0 ELSE duration.inMonths(demoginfo[0][1],date(v.bldate)).months/12.0 END \n\
	ELSE '' END AS PTAGE, \n\
	CASE WHEN demoginfo[0][2]='' THEN demoginfo[1][2] ELSE demoginfo[0][2] END AS PTEDUCAT" 
	q+=return_all_properties('v','allvols')
	q+=", CASE WHEN filter(x in dxinfo WHERE x[0]=minbldx)[0][2]<>'' THEN filter(x in dxinfo WHERE x[0]=minbldx)[0][2] \n\
	WHEN filter(x in dxinfo WHERE x[0]=minbldx)[0][1]<>'' THEN filter(x in dxinfo WHERE x[0]=minbldx)[0][1] \n\
	ELSE filter(x in dxinfo WHERE x[0]=minbldx)[0][3] END AS DXCHANGE, \n\
	filter(x in dxinfo WHERE x[0]=minbldx)[0][6] AS PHASE_bl, \n\
	filter(x in dxinfo WHERE x[4]=minfudx)[0][6] AS PHASE_fu, \n\
	CASE WHEN filter(x in dxinfo WHERE x[0]=minbldx)[0][6]<>filter(x in dxinfo WHERE x[4]=minfudx)[0][6] THEN 'changed' ELSE 'same' END AS PHASE_change, \n\
	(filter(x in prinfo WHERE x[0]=minblpr)[0][2]).Manufacterer AS Manufacturer_bl, \n\
	(filter(x in prinfo WHERE x[0]=minblpr)[0][2]).model AS model_bl, \n\
	(filter(x in prinfo WHERE x[0]=minblpr)[0][2]).software_version AS software_version_bl, \n\
	(filter(x in prinfo WHERE x[0]=minblpr)[0][2]).HeadCoil AS HeadCoil_bl, \n\
	(filter(x in prinfo WHERE x[1]=minfupr)[0][2]).Manufacterer AS Manufacturer_fu, \n\
	(filter(x in prinfo WHERE x[1]=minfupr)[0][2]).model AS model_fu, \n\
	(filter(x in prinfo WHERE x[1]=minfupr)[0][2]).software_version AS software_version_fu, \n\
	(filter(x in prinfo WHERE x[1]=minfupr)[0][2]).HeadCoil AS HeadCoil_fu, \n\
	CASE WHEN (filter(x in prinfo WHERE x[0]=minblpr)[0][2]).Manufacterer<>(filter(x in prinfo WHERE x[1]=minfupr)[0][2]).Manufacterer THEN 'changed' ELSE 'same' END AS Manufacturer_change, \n\
	CASE WHEN (filter(x in prinfo WHERE x[0]=minblpr)[0][2]).model<>(filter(x in prinfo WHERE x[1]=minfupr)[0][2]).model THEN 'changed' ELSE 'same' END AS model_change, \n\
	CASE WHEN (filter(x in prinfo WHERE x[0]=minblpr)[0][2]).software_version<>(filter(x in prinfo WHERE x[1]=minfupr)[0][2]).software_version THEN 'changed' ELSE 'same' END AS software_version_change, \n\
	CASE WHEN (filter(x in prinfo WHERE x[0]=minblpr)[0][2]).HeadCoil<>(filter(x in prinfo WHERE x[1]=minfupr)[0][2]).HeadCoil THEN 'changed' ELSE 'same' END AS HeadCoil_change, \n\
	filter(x in coginfo WHERE x[0]=VISCODE2_bl)[0][1] AS AVDEL30MIN_bl, \n\
	filter(x in coginfo WHERE x[0]=VISCODE2_bl)[0][2] AS AVTOT1_bl, \n\
	filter(x in coginfo WHERE x[0]=VISCODE2_bl)[0][3] AS AVTOT6_bl, \n\
	filter(x in coginfo WHERE x[0]=VISCODE2_bl)[0][4] AS AVDELTOT_bl, \n\
	filter(x in coginfo WHERE x[0]=VISCODE2_bl)[0][5] AS AVDELERR2_bl, \n\
	CASE WHEN filter(x in coginfo WHERE x[0]=VISCODE2_fu)[0][1] is null THEN 'NA' ELSE filter(x in coginfo WHERE x[0]=VISCODE2_fu)[0][1] END AS AVDEL30MIN_fu, \n\
	CASE WHEN filter(x in coginfo WHERE x[0]=VISCODE2_fu)[0][2] is null THEN 'NA' ELSE filter(x in coginfo WHERE x[0]=VISCODE2_fu)[0][2] END AS AVTOT1_fu, \n\
	CASE WHEN filter(x in coginfo WHERE x[0]=VISCODE2_fu)[0][3] is null THEN 'NA' ELSE filter(x in coginfo WHERE x[0]=VISCODE2_fu)[0][3] END AS AVTOT6_fu, \n\
	CASE WHEN filter(x in coginfo WHERE x[0]=VISCODE2_fu)[0][4] is null THEN 'NA' ELSE filter(x in coginfo WHERE x[0]=VISCODE2_fu)[0][4] END AS AVDELTOT_fu, \n\
	CASE WHEN filter(x in coginfo WHERE x[0]=VISCODE2_fu)[0][5] is null THEN 'NA' ELSE filter(x in coginfo WHERE x[0]=VISCODE2_fu)[0][5] END AS AVDELERR2_fu, \n\
	CASE WHEN filter(x in coginfo WHERE x[0]=VISCODE2_bl)[0][1]<>filter(x in coginfo WHERE x[0]=VISCODE2_fu)[0][1] THEN 'changed' ELSE 'same' END AS AVDEL30MIN_change, \n\
	CASE WHEN filter(x in coginfo WHERE x[0]=VISCODE2_bl)[0][2]<>filter(x in coginfo WHERE x[0]=VISCODE2_fu)[0][2] THEN 'changed' ELSE 'same' END AS AVTOT1_change, \n\
	CASE WHEN filter(x in coginfo WHERE x[0]=VISCODE2_bl)[0][3]<>filter(x in coginfo WHERE x[0]=VISCODE2_fu)[0][3] THEN 'changed' ELSE 'same' END AS AVTOT6_change, \n\
	CASE WHEN filter(x in coginfo WHERE x[0]=VISCODE2_bl)[0][4]<>filter(x in coginfo WHERE x[0]=VISCODE2_fu)[0][4] THEN 'changed' ELSE 'same' END AS AVDELTOT_change, \n\
	CASE WHEN filter(x in coginfo WHERE x[0]=VISCODE2_bl)[0][5]<>filter(x in coginfo WHERE x[0]=VISCODE2_fu)[0][5] THEN 'changed' ELSE 'same' END AS AVDELERR2_change \n\
	order By RID"
	if info==False: return q
	else: return "allvols + bl dx + bl/fu/change provenance + bl/fu/change phase, + bl/fu/change cog data"
	
def get_query_list(full_list):
	ql1=['Query 1','Query 2','Query 3','Query 4','Query 5','Query 6','Query 7','Query 8','Query 9',
		'Query 10','Query 11','Query 12','Query 13','Query 14','Query 15','Query 16','Query 17','Query 18',
		'Query 19', 'Query 20', 'Query 21', 'Query 22', 'Query 23', 'Query 24', 'Query 25', 'Query 26', 'Query 27']
	ql2=[query1(True),query2(True),query3(True),query4(True),query5(True),query6(True),query7(True),query8(True),query9(True),
		query10(True),query11(True),query12(True),query13(True),query14(True),query15(True),query16(True),query17(True),query18(True),
		query19(True), query20(True), query21(True), query22(True), query23(True), query24(True), query25(True), query26(True), query27(True)]
	if full_list==True: return ql2
	else: return ql1
	
def query(num_query):
	if num_query==1:return query1(False),["DXSUM","PDXCONV"]
	elif num_query==2:return query2(False),["DXSUM","PDXCONV"]
	elif num_query==3:return query3(False),["DXSUM","PDXCONV","NEUROBAT","MMSE"]
	elif num_query==4: return query4(False),["MRI3META","MRIMETA"]
	elif num_query==5: return query5(False),[]
	elif num_query==6: return query6(False),[]
	elif num_query==7: return query7(False),[]
	elif num_query==8: return query8(False),[]
	elif num_query==9: return query9(False),["DXSUM","PDXCONV","MMSE","CDR","APOE","PTDEMOG"]
	elif num_query==10: return query10(False),["DXSUM","PDXCONV"]
	elif num_query==11: return query11(False),["DXSUM","PDXCONV"]
	elif num_query==12: return query12(False),["DXSUM","PDXCONV"]
	elif num_query==13: return query13(False),[]
	elif num_query==14: return query14(False),[]
	elif num_query==15: return query15(False),["DXSUM","PDXCONV","MMSE","PTDEMOG"]
	elif num_query==16: return query16(False),["DXSUM","PDXCONV","PTDEMOG","UCBERKELEYAV45"]
	elif num_query==17: return query17(False),["DXSUM","PDXCONV","PTDEMOG","UCBERKELEYAV45"]
	elif num_query==18: return query18(False),["DXSUM","PDXCONV","PTDEMOG","MMSE"]
	elif num_query==19: return query19(False),["DXSUM","PDXCONV","PTDEMOG","MMSE"]
	elif num_query==20: return query20(False),["DXSUM","PDXCONV"]
	elif num_query==21: return query21(False),["DXSUM","PDXCONV","PTDEMOG"]
	elif num_query==22: return query22(False),["DXSUM","PDXCONV","PTDEMOG","MMSE"]
	elif num_query==23: return query23(False),["NEUROBAT"]
	elif num_query==24: return query24(False),["DXSUM","PDXCONV","PTDEMOG"]
	elif num_query==25: return query25(False),["DXSUM","PDXCONV","PTDEMOG"]
	elif num_query==26: return query26(False),["DXSUM","PDXCONV","PTDEMOG"]
	elif num_query==27: return query27(False),["DXSUM","PDXCONV","NEUROBAT","PTDEMOG"]
