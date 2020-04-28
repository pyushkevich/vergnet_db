import csv, re
import os

# TODO: there needs to be a consistent way to define instance path
dir_path = os.path.join(os.environ['ADNIDB_ROOT'], 'instance')

meta_file="DATADIC.csv"
data_file="result.csv"

    ##Create a dictionary of all the meta data (specified by Phase and Table) from a csv file
    #meta_file : name of the meta .csv file
    #phase : name of the ADNI Phase
    #table : name of the table you need
def create_meta_dict(meta_file,table):
    meta_dic=dict()
    for k,row in enumerate(meta_file):
        if k==0:
            header=row
            field_ind=header.index('FLDNAME')
            code_ind=header.index('CODE')
            tblname_ind=header.index('TBLNAME')
            #phase_ind=header.index('Phase') #useless ?
        else:
            for i,col in enumerate(row):
                #if (row[phase_ind]==phase and row[tblname_ind]==table): 
                if row[tblname_ind] in table:
                    if i==field_ind: 
                        field_temp=col
                    if i==code_ind:
                        l=re.split(';|=',col)
                        if len(l)%2!=0 and l[-1]=='':l.pop()
                        for n,c in enumerate(l): l[n]=c.strip()
                        if len(l)>1:
                            d_temp=dict(l[j:j+2] for j in range(0, len(l), 2))
                        else:
                            d_temp=dict()
                        meta_dic[field_temp]=d_temp
    return meta_dic

    ##Translate the data from data_file with the meta dictionary
    #data_file : name of the .csv file you wamt to translate
    #rownum : number of row in the data_file
    #meta_dic : meta dictionary
def translate_data(data_file,rownum,meta_dic):
    header_data=next(data_file)
    new_result=[[0 for i in range(len(header_data))] for j in range(rownum)]
    new_result[0]=header_data
    pattern=re.compile('\d|\d,')
    for k,row in enumerate(data_file):
        for i,col in enumerate(row):
            header_woutus=header_data[i].split('_')[0]
            if header_data[i] in meta_dic.keys(): 
                pos_temp=meta_dic[header_data[i]]
            elif header_woutus in meta_dic.keys(): 
                pos_temp=meta_dic[header_woutus]
            else: 
                pos_temp={}
                
            if (pos_temp!={} and col in pos_temp.keys()): 
                val_temp=pos_temp[col]
            elif (pos_temp!={} and pattern.match(col)): 
                l_temp=re.split('[|]',col)
                val_temp=''
                for j,val in enumerate(l_temp): 
                    if val not in pos_temp: 
                        val_temp+=val
                    else: val_temp+=pos_temp[val]+'{}'.format(' | ' if j!=len(l_temp)-1 else '')
            else: 
                val_temp=col
            new_result[k+1][i]=val_temp
    return new_result

    ##Create a new .csv file (named final_result.csv) where the data has been translated
    #meta_file : name of the meta .csv file 
    #data_file : name of the .csv file you want to translate
def result(meta_file,data_file,table):
    input = open(data_file,newline='')
    f=csv.reader(input)
    rownum=sum(1 for row in f)
    meta_dict=create_meta_dict(csv.reader(open(meta_file,newline='')),table)
    output=open(dir_path+"/savefile/result/"+'final_result_temp.csv','w',newline='')
    writer=csv.writer(output)
    writer.writerows(translate_data(csv.reader(open(data_file,newline='')),rownum,meta_dict))
    input.close()
    output.close()
    diag_postprocess()
    csv2tsv()
    print('Data translated')
    return

    #Process the diagnosis variable to create an unique one
def diag_postprocess():
    input=open(dir_path+'/savefile/result/final_result_temp.csv','r',newline='')
    output=open(dir_path+'/savefile/result/final_result.csv','w',newline='')
    reader=csv.reader(input)
    writer=csv.writer(output)
    header=next(reader)
    diag_inds = [i for i, x in enumerate(header) if 'DXCHANGE' in x]
    if len(diag_inds)>0:
        #diag_ind=header.index('DXCHANGE')
        header_temp=header
        for diag_ind in diag_inds:
            header_temp[diag_ind]=header[diag_ind].replace('DXCHANGE','DIAGNOSIS')
        writer.writerow(header_temp)
        for row in reader:
            row_temp=row
            for diag_ind in diag_inds:
                diag_temp=row[diag_ind].split(": ")[-1].split(' to ')
                row_temp[diag_ind]=diag_temp[-1]
            writer.writerow(row_temp)
    else:
        writer.writerow(header)
        for row in reader:
            writer.writerow(row)
    input.close()
    output.close()
        
    #create a tsv file from a csv
def csv2tsv():
    with open(dir_path+'/savefile/result/final_result.csv','r',newline='') as input, open(dir_path+'/savefile/result/final_result.tsv','w',newline='') as output:
        csvin = csv.reader(input)
        tsvout = csv.writer(output, delimiter='\t')
        
        for row in csvin:
            tsvout.writerow(row)
