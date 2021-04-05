import csv
import re
import os
import time
import pandas as pd

# Merging sc and bl visits for ADNI3 scans. Copy logical memory scores to bl visit and remove sc visit
def mergeLMrows(infile, outfile):
   df = pd.read_csv( infile )

   for index, row in df.iterrows():
      VISCODE2=row['VISCODE2']
      Phase=row['Phase']
      RID=row['RID']
      if Phase == 'ADNI3' and VISCODE2 == 'bl' :
        scrow = df.loc[(df['RID'] == RID) & (df['VISCODE2'] == 'sc') & (df['Phase'] == 'ADNI3') ]
        if scrow.empty == False :
           df.at[index, 'LMSTORY'] = scrow['LMSTORY']
           df.at[index, 'LIMMTOTAL'] = scrow['LIMMTOTAL']
           df.at[index, 'LIMMEND'] = scrow['LIMMEND']
           df.at[index, 'LDELBEGIN'] = scrow['LDELBEGIN']
           df.at[index, 'LDELTOTAL'] = scrow['LDELTOTAL']
           df.at[index, 'LDELCUE'] = scrow['LDELCUE']
           df.drop( scrow.index, inplace = True )
   df.to_csv( outfile, index=False)


#preprocess csv files
def preprocess(csvfilename,dirs):
	mi_pet="Coreg, Avg, Std Img and Vox Siz, Uniform Resolution" 
	for dir in dirs:
		f=open(dir +'/'+csvfilename,newline='', encoding='utf-8-sig')
		pattern=re.compile('\d{3}_S_0*')
		print('Writing CSV to %s', (open(dir +'/'+csvfilename.replace('.csv','_temp.csv'),'w'),))
		with open(dir +'/'+csvfilename.replace('.csv','_temp.csv'),'w') as temp:
			for i,line in enumerate(f):
				mritype=-4
				if i==0:				
					if "PET_META_LIST" in csvfilename:
						header = line.replace("\n", ',\"RID\",\"PHASE\",\"PETTYPE\",\"RIGHTONE\"\n').replace("Scan Date","SCANDATE")
					elif "MRILIST" in csvfilename:
						header = line.replace("\n", ',\"RID\",\"PHASE\",\"MRITYPE\",\"T1ACCE\"\n')	
					elif 'APOERES' in csvfilename:		
						header = line.replace("\n", ',\"APOE\"\n')
					elif 'allvols' in csvfilename:
						header = line.replace('\n', ',\"RID"\n')
					elif 'ADNI_scanner' in csvfilename:
						header = line.replace('\n', ',\"RID"\n')
					else:header = line
					temp.write(
						#header.upper()
						header.replace(" ","")
						.replace("VISIT","VISCODE2")
						.replace("Visit","VISCODE2")
						.replace("/","_")
						.replace(".","_")
						.replace("EXAMDATE", "SCANDATE")
					)	
				else:
					
					##Preprocess the phase
					if "ADNIGO" in line or "ADNI1/GO" in line:phase="ADNIGO"
					elif "ADNI2" in line:phase="ADNI2"
					elif "ADNI3" in line:phase="ADNI3"
					else: phase="ADNI1"
					
					if "PET_META_LIST" in csvfilename:
					
						##Preprocess the rid
						rid = pattern.sub('',re.search('\d{3}_S_\d{4}',line).group())
						if int(rid)>5999:phase="ADNI3"
					
						##Preprocess the PET we want
						if mi_pet in line:ro=1
						else:ro=0
						
						##Preprocess PET scan type (TAU=1/Amyloid=2/other=0)
						if ("FBB" in line or "AV45" in line):pettype=1
						elif "AV1451" in line:pettype=2
						else:pettype=0
								
						line_temp = line.replace('\n', ',\"'+rid+'\",\"'+phase+'\",\"'+str(pettype)+'\",\"'+str(ro)+'\"\n')
						
					elif "MRILIST" in csvfilename:
						
						##Preprocess the rid
						rid = pattern.sub('',re.search('\d{3}_S_\d{4}',line).group())
						if int(rid)>5999:phase="ADNI3"
						
						line=line.upper()
						##Preprocess the MRI type (T1/T2)
						if ("MPRAGE" in line or "MP-RAGE" in line or "SPGR" in line):
							mritype=0
						elif "HIPP" in line:
							mritype=1
						
						##Preprocess Acce T1
						if ("ACCE" in line or "GRAPPA" in line or "SENSE" in line or "_P2_" in line):
							acce=1
						else:
							acce=0
						
						line_temp = line.replace('\n', ',\"'+rid+'\",\"'+phase+'\",\"'+str(mritype)+'\",\"'+str(acce)+'\"\n')
					
					elif 'APOERES' in csvfilename:
						l=line.replace('"',"").split(',')
						if int(l[8])==4 or int(l[9])==4 :
							line_temp = line.replace('\n', ',\"carrier\"\n')
						else:	
							line_temp = line.replace('\n', ',\"non-carrier\"\n')
						
					elif 'allvols' in csvfilename:
						##Preprocess the rid
						rid = pattern.sub('',re.search('\d{3}_S_\d{4}',line).group())
						line_temp = line.replace('\n', ',\"'+rid+'\"\n')
					
					elif 'ADNI_scanner' in csvfilename:
						pattern2 = re.compile('\d{8}')
						date = re.search('\d{8}', line).group()
						dateTemp = date[0:4]+'-'+date[4:6]+'-'+date[6:8]
						rid = pattern.sub('',re.search('\d{3}_S_\d{4}',line).group())
						line_temp = line.replace('\n', ',\"'+rid+'\"\n').replace(date,dateTemp)
					
					else:
						line_temp = line.replace('scmri','bl').replace('blmri','bl').replace('sc','bl')

					line_temp=dateFormat(line_temp)
					temp.write(line_temp)
		f.close()
		os.remove(dir +'/'+csvfilename)

#normalize date format from different csv files
def dateFormat(line):
	pattern1=re.compile('\d{1,2}/\d{1,2}/\d{4}')
	pattern2=re.compile('\d{1,2}/\d{1,2}/\d{2}')
	datelist1=re.findall('\d{1,2}\/\d{1,2}\/\d{4}',line)
	datelist2=re.findall('\d{1,2}\/\d{1,2}\/\d{2}',line)
	if datelist1!=[]:
		line_temp=line
		for date in datelist1:
			datetemp=date.split('/')
			datefinal=datetemp[2]+"-"+datetemp[0]+"-"+datetemp[1]
			line_temp=line_temp.replace(date,datefinal)
		return line_temp
	elif datelist2!=[]:
		line_temp=line
		for date in datelist2:
			datetemp=date.split('/')
			datefinal="20"+datetemp[2]+"-"+datetemp[0]+"-"+datetemp[1]
			line_temp=line_temp.replace(date,datefinal)
		return line_temp
	else:
		return line

#convert tsv files to csv files for upload or download
def tsv2csv(tsvfilename,tsvfilepath):
	outpath = tsvfilepath.replace(tsvfilename,'')+tsvfilename.replace('tsv','csv')
	numline = sum(1 for row in open(tsvfilepath, 'r'))
	with open(tsvfilepath, 'r') as tsvfile, open(outpath, 'w') as csvfile:
		for i,line in enumerate(tsvfile):
			line=line.replace('\"','')
			fileContent = "\"" + re.sub("\t", "\",\"", line) 
			fileContent = fileContent.replace('\n','\"\n')
			if i==numline-1 and "\n" not in fileContent: 
				fileContent+="\"\n"
			csvfile.write(fileContent)
	return outpath

#create a new spreadsheet for FDG data
def FDG_preprocess(FDGcsvname):
	newfilename = 'UCBERKELEYFDG.csv'
	with open(FDGcsvname, 'r', newline='') as infile, open(newfilename, 'w', newline='') as outfile:
		reader = csv.reader(infile)
		hr = next(reader)
		hw = hr[:5]+['Left Angular','Right Angular','CingulumPost Bilateral', 'Right Temporal', 'Left Temporal', 'ADSIGNATURE']
		writer = csv.DictWriter(outfile, fieldnames=hw)
		writer.writeheader()
		dict_temp={hw[0]:'', hw[1]:'', hw[2]:'', hw[3]:'', hw[4]:'', hw[5]:'', hw[6]:'', hw[7]:'', hw[8]:'', hw[9]:'', hw[10]:''}
		for i,row in enumerate(reader):
			if i%5==0:
				dict_temp[hw[0]]=row[0]
				dict_temp[hw[1]]=(row[1] if row[1]!='' else 'bl')
				dict_temp[hw[2]]=(row[2] if row[2]!='' else 'bl')
				dict_temp[hw[3]]=row[3]
				dict_temp[hw[4]]=row[4]
				dict_temp[hw[5]]=row[7]
				mean = float(row[7])
			elif i%5==1: 
				dict_temp[hw[6]]=row[7]
				mean += float(row[7])
			elif i%5==2: 
				dict_temp[hw[7]]=row[7]
				mean += float(row[7])
			elif i%5==3: 
				dict_temp[hw[8]]=row[7]		
				mean += float(row[7])
			else: 
				dict_temp[hw[9]]=row[7]
				mean += float(row[7])
				dict_temp[hw[10]]= mean/5.0
				
				writer.writerow(dict_temp)	
	return newfilename
	
#create a new spreadsheet for provenance data
def summary_preprocess(filename):
	outputtemp = 'tempsummary.csv'
	with open(filename, 'r', newline='') as infile, open(outputtemp, 'w', newline='') as outfile:
		reader = csv.reader(infile)
		h = next(reader)
		writer = csv.DictWriter(outfile, fieldnames=h)
		writer.writeheader()
		dict_temp = {h[0]:'', h[1]:'', h[2]:'', h[3]:'', h[4]:'', h[5]:''}
		for row in reader:
			dict_temp[h[0]] = row[0]
			dict_temp[h[1]] = row[1]
			dict_temp[h[3]] = row[3]
			dict_temp[h[4]] = row[4]
			dict_temp[h[5]] = row[5]
			if (row[3]=='DISCOVERY MR750' or row[3]=='DISCOVERY MR750w' or row[3]=='SIGNA HDx' 
				or row[3]=='Signa HDxt' or row[3]=='SIGNA Premier'):
				dict_temp[h[2]] = 'GE MEDICAL SYSTEMS'
				
			elif (row[3]=='Achieva dStream' or row[3]=='Ingenia Elition X' or row[3]=='Ingenia' or row[3]=='Achieva' 
				or row[3]=='Achieva dStream' or row[3]=='GEMINI' or row[3]=='Ingenuity' or row[3]=='Intera'):
				dict_temp[h[2]] = 'Philips Medical Systems'
				
			else:
				dict_temp[h[2]] = 'SIEMENS'
				
			writer.writerow(dict_temp)
			
	with open(filename, 'w', newline='') as outfile, open(outputtemp, 'r', newline='') as infile:
		for row in infile:
				outfile.write(row)
	
	os.remove(outputtemp)
	return filename
	
#add quotation marks t ocsv files before uploading them into the db
def quoteCSV(csvin,dirs):
	for dir in dirs:
		with open(dir+'/'+csvin,'r',newline='') as input, open(dir+'/temp.csv','w',newline='') as output:
			for row in input:
				test=row.split('"')
				if len(test)>1:
					temp=''
					for i in range(0, len(test), 2):
						test[i]=test[i].replace(',','","')
					for part in test:
						temp+=part
					row_temp = '"{}"\r\n'.format(temp.replace('\r\n','').replace('\n',''))
				else:
					row_temp = '"{}"\r\n'.format(row.replace(',','","').replace('\r\n','').replace('\n',''))
				#print(row_temp)
				output.write(row_temp)
		with open(dir+'/temp.csv','r',newline='') as input, open(dir+'/'+csvin,'w',newline='') as output:
			for row in input:
				output.write(row)
				
		os.remove(dir +'/temp.csv')	
