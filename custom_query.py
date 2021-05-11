from query_sampler import return_all_properties

def query_builder(qMajor, qOptional, qMerge, stdinfo):
	maj = list(qMajor.keys())[0]
	optional = list(qOptional.keys())
	tbl = [maj] + optional

	print('qMajor', qMajor)

	q = "match (p:Person)--(n:{})\n".format(maj)
	withStr = "with p, n\n"
	if qMerge[maj]['date'] != "":	q += "where n.{} <> \"\"\n".format(qMerge[maj]['date'])
	q += withStr 
	
	if 'demog' in stdinfo:
		q += "optional match (p)--(P:PTDEMOG)\n"
		q += withStr[:-1] + ", collect([P.PTGENDER, date({year:toInteger(P.PTDOBYY), month:toInteger(P.PTDOBMM)}), P.PTEDUCAT, P.PTRACCAT]) as demoginfo\n"
		withStr = withStr[:-1] + ", demoginfo\n"
		tbl.append("PTDEMOG")
	
	if 'dx' in stdinfo:
		q += "optional match (p)--(d:DXSUM_PDXCONV_ADNIALL)\nwhere d.SMARTDATE<>\"\"\n"
		q += withStr[:-1] + ", collect([abs(duration.inDays(date(n.{}),date(d.SMARTDATE)).days),d.SMARTDIAG,d.SMARTDATE]) AS dxinfo\n".format(qMerge[maj]['date'])
		q += "unwind extract(x in dxinfo | x[0]) as diffdx\n"
		q += withStr[:-1] + ", dxinfo, min(diffdx) as mindx\n"
		withStr = withStr[:-1] + ", dxinfo, mindx\n"
		tbl += ["PDXCONV", "DXSUM"]

	# For each optional data, we need a map from ID to index
	opt_index_map={}

	for i, opt in enumerate(optional):
		# Type of merge
		matchstr = 'optional match' if qMerge[opt]['optional'] is True else 'match'

		q += "{} (p)--(n{}:{})\n".format(matchstr, i, opt)
		mergetemp = list(qMerge[opt].keys())[0]

		opt_index_map[opt] = {}
		for k, field in enumerate(list(qOptional[opt])):
			opt_index_map[opt][field] = k
		
		if mergetemp == "date" and qMerge[opt][mergetemp][1] == "closest":
			q += "where n{num}.{0} <> \"\"\n".format(qMerge[opt][mergetemp][0], num = i)
			listemp = ""
			for data in list(qOptional[opt]):
				listemp += "n{num}.{data}, ".format(num = i, data = data)
			q += withStr[:-1] + ", collect([abs(duration.inDays(date(n.{0}), date(n{num}.{1})).days), {list}]) as n{num}cond\n".format(qMerge[maj][mergetemp], qMerge[opt][mergetemp][0], list = listemp[:-2], num = i)
			q += "unwind extract (x in filter(y in n{num}cond where y[0] > {fro} and y[0] < {to}) | x[0]) as n{num}diff\n".format(
				num = i, fro = qMerge[opt][mergetemp][2], to = qMerge[opt][mergetemp][3])
			q += withStr[:-1] + ", n{num}cond, min(n{num}diff) as minN{num}\n".format(num = i)
			withStr = withStr[:-1] + ", n{num}cond, minN{num}\n".format(num = i)
		
		elif mergetemp == "date" and qMerge[opt][mergetemp][1] == "before":
			q += "where n{num}.{0} <> \"\"\n".format(qMerge[opt][mergetemp][0], num = i)
			listemp = ""
			for data in list(qOptional[opt]):
				listemp += "n{num}.{data}, ".format(num = i, data = data)
			q += withStr[:-1] + ", collect([(duration.inDays(date(n.{0}), date(n{num}.{1})).days), {list}]) as n{num}cond\n".format(qMerge[maj][mergetemp], qMerge[opt][mergetemp][0], list = listemp[:-2], num = i)
			q += "unwind extract (x in filter(y in n{num}cond where y[0]<0) | x[0]) as n{num}diff\n".format(num = i)
			q += withStr[:-1] + ", n{num}cond, max(n{num}diff) as minN{num}\n".format(num = i)
			withStr = withStr[:-1] + ", n{num}cond, minN{num}\n".format(num = i)

		elif mergetemp == "date" and qMerge[opt][mergetemp][1] == "after":
			q += "where n{num}.{0} <> \"\"\n".format(qMerge[opt][mergetemp][0], num = i)
			listemp = ""
			for data in list(qOptional[opt]):
				listemp += "n{num}.{data}, ".format(num = i, data = data)
			q += withStr[:-1] + ", collect([(duration.inDays(date(n.{0}), date(n{num}.{1})).days), {list}]) as n{num}cond\n".format(qMerge[maj][mergetemp], qMerge[opt][mergetemp][0], list = listemp[:-2], num = i)
			q += "unwind extract (x in filter(y in n{num}cond where y[0]>=0) | x[0]) as n{num}diff\n".format(num = i)
			q += withStr[:-1] + ", n{num}cond, min(n{num}diff) as minN{num}\n".format(num = i)
			withStr = withStr[:-1] + ", n{num}cond, minN{num}\n".format(num = i)
		
		elif mergetemp == "default":
			withStr = withStr[:-1] + ", n{}\n".format(i)
			q += withStr
		
		elif mergetemp == "date" and qMerge[opt][mergetemp][1] == "equal":
			q += "where n.{} = n{num}.{}\n".format(qMerge[maj][mergetemp], qMerge[opt][mergetemp][0], num = i)
			withStr = withStr[:-1] + ", n{}\n".format(i)
			q += withStr
			
		else:
			q += "where n.{} = n{num}.{}\n".format(qMerge[maj][mergetemp], qMerge[opt][mergetemp], num = i)
			withStr = withStr[:-1] + ", n{}\n".format(i)
			q += withStr
		
	q += "return toInteger(p.RID) as RID, "
	
	if 'demog' in stdinfo:
		q += "case when demoginfo[0][0]=\"\" then demoginfo[1][0] else demoginfo[0][0] end as PTGENDER,\n"
		q += "case when n.{d}<>\"\" then\ncase when demoginfo[0][0]=\"\" then duration.inMonths(demoginfo[1][1],date(n.{d})).months/12.0\n".format(d = qMerge[maj]['date'])
		q += "else duration.inMonths(demoginfo[0][1],date(n.{d})).months/12.0 end\n".format(d = qMerge[maj]['date'])
		q += "else \"\" end as PTAGE,\n".format(d = qMerge[maj]['date'])
		q += "case when demoginfo[0][2]=\"\" then demoginfo[1][2] else demoginfo[0][2] end as PTEDUCAT,\n"
		q += "case when demoginfo[0][3]=\"\" then demoginfo[1][3] else demoginfo[0][3] end as PTRACCAT,\n"

	if 'dx' in stdinfo:
		q += "filter(x in dxinfo where x[0]=mindx)[-1][1] as SMARTDIAG,\n"
		q += "filter(x in dxinfo where x[0]=mindx)[-1][2] as SMARTDATE_DIAG,\n"

	# Go through the major coulns
	for majdata in list(qMajor[maj]):

		# Check if the field is unique
		unique = True
		for i, opt in enumerate(optional):
			if majdata in list(qOptional[opt]):
				unique = False

		# If unique field, then just add to query and that's it
		if unique:
			q += "n.{data} as {data}, ".format(data=majdata)
		else:
			# Add the major table name to the column name
			suffix = 'TMP' if maj.startswith('tmp_') else maj
			q += "n.{} as {}_{}, ".format(majdata, majdata, suffix)

			# Add the same column in merge tables
			for i, opt in enumerate(optional):
				if majdata in list(qOptional[opt]):
					mergetemp = list(qMerge[opt].keys())[0]
					if mergetemp == "date" and qMerge[opt][mergetemp][1] in ["closest", "after", "before"]:
						#q += "filter(x in n{num}cond where x[0] = minN{num})[0][{j}] as {data}_{opt},\n".format(
						#	num=i, j=j + 1, data=majdata, opt=opt)
						q += "filter(x in n{num}cond where x[0] = minN{num})[0][{index}] as {data}_{opt},\n".format(
							num=i, data=majdata, opt=opt, index=opt_index_map[opt][majdata]+1)
					else:
						q += "n{num}.{data} as {data}_{opt}, ".format(num=i, data=majdata, opt=opt)

	for i, opt in enumerate(optional):
		mergetemp = list(qMerge[opt].keys())[0]
		if mergetemp == "date" and qMerge[opt][mergetemp][1] in ["closest","after","before"]:
			for j, data in enumerate(list(qOptional[opt])):
				if data not in list(qMajor[maj]):
					q += "filter(x in n{num}cond where x[0] = minN{num})[0][{index}] as {data},\n".format(
						num = i, j = j + 1, data = data, index = opt_index_map[opt][data]+1)

		else:
			for data in list(qOptional[opt]):
				if data not in list(qMajor[maj]):
					q += "n{num}.{data} as {data}, ".format(num = i, data = data)
	
	q = q[:-2] +  " order by RID"
	
	return q, tbl
	
def info_builder(qMajor, qOptional, qMerge, stdinfo):
	maj = list(qMajor.keys())[0]

	info = "Find all subjects who have {} and add:".format(maj)
	if maj.startswith('tmp_'):
		info = "List all subjects in uploaded spreadsheet and add: "

	returninfo = " Return"
	infosup = " Merged"

	for i, prop in enumerate(qMajor[maj]):
		returninfo += " {}{}".format(prop, "," if i<len(qMajor[maj])-1 else ";")
		
	for i, optional in enumerate(list(qOptional.keys())):
		mergeType = list(qMerge[optional].keys())[0]
		if mergeType == 'date': strMerge = " merged with {} {}".format(qMerge[optional][mergeType][1], mergeType)
		elif mergeType == 'viscode': strMerge = " merged with {}".format(mergeType)
		else: strMerge = " merged with RID/nothing"
	
		info += " {}{} and".format(optional, strMerge if i<len(list(qOptional.keys())) else "")
		for j, prop in enumerate(qOptional[optional]): 
			returninfo += " {}{}".format(prop, "," if j<len(qOptional[optional])-1 else ";") 

	if 'dx' in stdinfo: infosup += " with diagnosis information and" 
	if 'demog' in stdinfo: infosup += " with demographic information and"
	
	if len(infosup) < 10: 
		result = info[:-4] + "." + returninfo[:-1] + "."
	else:
		result = info[:-4] + "." + returninfo[:-1] + "." + infosup[:-4] + "."
	return result
	
def merge(input, mergewith, dates=['SMARTDATE']):
	tbl=[]
	collect = "COLLECT(["
	unwind = ""
	w = "WITH dxinfo, n, i{}, "
	rdxtest = ""
	
	mdemog="optional match (n)--(p:PTDEMOG) \
		WITH COLLECT([p.PTGENDER,date({{year:toInteger(p.PTDOBYY), month:toInteger(p.PTDOBMM)}}), p.PTEDUCAT]) AS demoginfo, n, i{}"
	
	for j, date in enumerate(dates):
		collect += "abs(duration.inDays(date(i.{}),date(d.SMARTDATE)).days),".format(date)
		unwind += "UNWIND extract(x in dxinfo | x[{}]) as diff{}\n".format(j, date)
		w += "min(diff{d}) as min{d}, ".format(d = date)
		rdxtest += ",CASE WHEN filter(x in dxinfo where x[{num}]=min{d})[-1][-3]<>\"\" THEN filter(x in dxinfo where x[{num}]=min{d})[-1][-3] \
		WHEN filter(x in dxinfo where x[{num}]=min{d})[-1][-4]<>\"\" then filter(x in dxinfo where x[{num}]=min{d})[-1][-4] \
		else filter(x in dxinfo where x[{num}]=min{d})[-1][-2] END AS DXCHANGE_{d}".format(num = j, d = date)
	
	unwind = unwind[:-1]
	w = w[:-2]	
		
	mdxtest="OPTIONAL MATCH (n)--(d:DXSUM_PDXCONV_ADNIALL) \
		WHERE d.SMARTDATE<>\"\" \
		WITH " + collect + "d.DIAGNOSIS,d.DXCHANGE,d.DXCURREN,d.VISCODE2]) AS dxinfo, n, i{}\n" + unwind + "\n" + w	+ "\n"
	
	mmmse="optional match (n)--(m:MMSE) \
		where m.VISCODE2=filter(x in dxinfo where x[0]=min{})[-1][-1] \
		with m, n, i{}"

	rdemog=",CASE WHEN demoginfo[0][0]=\"\" THEN demoginfo[1][0] ELSE demoginfo[0][0] END AS PTGENDER, \
		CASE WHEN i.{d}<>\"\" THEN \
		CASE WHEN demoginfo[0][0]=\"\" THEN duration.inMonths(demoginfo[1][1],date(i.{d})).months/12.0 ELSE duration.inMonths(demoginfo[0][1],date(i.{d})).months/12.0 END \
		ELSE \"\" END AS PTAGE"

	rdx=",CASE WHEN filter(x in dxinfo where x[0]=mindx)[-1][2]<>\"\" THEN filter(x in dxinfo where x[0]=mindx)[-1][2] \
		WHEN filter(x in dxinfo where x[0]=mindx)[-1][1]<>\"\" then filter(x in dxinfo where x[0]=mindx)[-1][1] \
		else filter(x in dxinfo where x[0]=mindx)[-1][3] END AS DXCHANGE"	
		
	rmmse=",m.MMSCORE as MMSCORE"
		
	q="match (n:Person)--(i:{}) \
		where i.{}<>\"\" \
		with n, i ".format(input, dates[0])
	result="return toInteger(n.RID) as RID"+return_all_properties("i",input)
	add=""
	info="{} merged with {}"
	mergeinfo=""
	if 'demog' in mergewith:
		q+=mdemog.format(" ")
		result+=rdemog.format(d = dates[0])
		tbl.append('PTDEMOG')
		add+=", demoginfo"
		mergeinfo+="demographic information; "
	if 'dx' in mergewith:
		q+=mdxtest.format(add+" ", add+" ")
		result+=rdxtest
		tbl.append('PDXCONV')
		tbl.append('DXSUM')
		add+=", dxinfo"
		for date in dates:
			add+=", min{}".format(date)
		mergeinfo+="diagnosis information; "

		q+=mmmse.format(dates[0], add+" ")
		result+=rmmse
		tbl.append('MMSE')
		add+=", m"
		mergeinfo+="MMSE information; "
		
	return q + result + " order by RID", tbl, info.format(input,mergeinfo)
