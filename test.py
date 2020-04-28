import csv 
import re

def FDG_preprocess(FDGcsvname):
	with open(FDGcsvname + '.csv', 'r', newline='') as infile, open('UCBERKELEYFDG.csv', 'w', newline='') as outfile:
		reader = csv.reader(infile)
		hr = next(reader)
		hw = hr[:5]+['Left Angular','Right Angular','CingulumPost Bilateral', 'Right Temporal', 'Left Temporal']
		writer = csv.DictWriter(outfile, fieldnames=hw)
		writer.writeheader()
		dict_temp={hw[0]:'', hw[1]:'', hw[2]:'', hw[3]:'', hw[4]:'', hw[5]:'', hw[6]:'', hw[7]:'', hw[8]:'', hw[9]:''}
		for i,row in enumerate(reader):
			if i%5==0:
				dict_temp[hw[0]]=row[0]
				dict_temp[hw[1]]=row[1]
				dict_temp[hw[2]]=row[2]
				dict_temp[hw[3]]=row[3]
				dict_temp[hw[4]]=row[4]
				dict_temp[hw[5]]=row[7]
			elif i%5==1: dict_temp[hw[6]]=row[7]
			elif i%5==2: dict_temp[hw[7]]=row[7]
			elif i%5==3: dict_temp[hw[8]]=row[7]		
			else: 
				dict_temp[hw[9]]=row[7]
				writer.writerow(dict_temp)
	
	
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
	


# pattern=re.compile('\d{3}_S_0*')	
# input = open("Subject_and_scan_stat_uniq.csv",'r',newline='')
# output = open("Subject_and_scan_stat_uniq_temp.csv",'w',newline='')
# reader = csv.reader(input) 
# writer = csv.writer(output)

# header = next(reader)
# header+=append('RID')
# writer.writerow(header)

# for line in reader:
	# rid = pattern.sub('',re.search('\d{3}_S_\d{4}',line[0]).group())
	# line_temp.append(str(rid))
	# writer.writerow(line_temp)
# input.close()
# output.close()

input=open("Subject_and_scan_stat_uniq_temp.csv",'r',newline='')
reader = csv.reader(input) 

next(reader)
l=[]
for row in reader:
	l.append(row[-1])
	
input.close()
print(l)