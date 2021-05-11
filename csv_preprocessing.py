import csv
import re
import os
import time
import pandas as pd


# Merging sc and bl visits for ADNI3 scans. Copy logical memory scores to bl visit and remove sc visit
def mergeLMrows(infile, outfile):
    df = pd.read_csv(infile)

    for index, row in df.iterrows():
        VISCODE2 = row['VISCODE2']
        Phase = row['Phase']
        RID = row['RID']
        if Phase == 'ADNI3' and VISCODE2 == 'bl':
            scrow = df.loc[(df['RID'] == RID) & (df['VISCODE2'] == 'sc') & (df['Phase'] == 'ADNI3')]
            if scrow.empty == False:
                df.at[index, 'LMSTORY'] = scrow['LMSTORY']
                df.at[index, 'LIMMTOTAL'] = scrow['LIMMTOTAL']
                df.at[index, 'LIMMEND'] = scrow['LIMMEND']
                df.at[index, 'LDELBEGIN'] = scrow['LDELBEGIN']
                df.at[index, 'LDELTOTAL'] = scrow['LDELTOTAL']
                df.at[index, 'LDELCUE'] = scrow['LDELCUE']
                df.drop(scrow.index, inplace=True)
    df.to_csv(outfile, index=False)


# Helper function to set RID, phase for MRI/PET tables
def set_rid_and_phase(df, i, row):
    # Assign the phase
    visit = row['VISIT']
    df.at[i, 'PHASE'] = \
        "ADNIGO" if "ADNIGO" in visit or "ADNI1/GO" in visit else (
            "ADNI2" if "ADNI2" in visit else (
                "ADNI3" if "ADNI3" in visit else "ADNI1"))

    # Assign the RID
    df.at[i, 'RID'] = int(row['SUBJECT'].split('_')[2])
    if df.at[i, 'RID'] > 5999:
        df.at[i, 'PHASE'] = "ADNI3"


# Helper function to set rid, viscode, phase in MRI/PET tables
def fixup_imaging_csv(df):
    # Replacement of strings with VISCODE
    repdic = {
        "ADNI Baseline": "bl",
        "ADNI Screening": "sc",
        "ADNI1/GO Month 12": "m12",
        "ADNI1/GO Month 18": "m18",
        "ADNI1/GO Month 24": "m24",
        "ADNI1/GO Month 36": "m36",
        "ADNI1/GO Month 48": "m48",
        "ADNI1/GO Month 54": "m54",
        "ADNI1/GO Month 6": "m06",
        "ADNI2 Baseline-New Pt": "v03",
        "ADNI2 Initial Visit-Cont Pt": "v06",
        "ADNI2 Month 3 MRI-New Pt": "v04",
        "ADNI2 Month 6-New Pt": "v05",
        "ADNI2 Screening MRI-New Pt": "v02",
        "ADNI2 Screening-New Pt": "v01",
        "ADNI2 Tau-only visit": "tau",
        "ADNI2 Year 1 Visit": "v11",
        "ADNI2 Year 2 Visit": "v21",
        "ADNI2 Year 3 Visit": "v31",
        "ADNI2 Year 4 Visit": "v41",
        "ADNI2 Year 5 Visit": "v51",
        "ADNI3 Initial Visit-Cont Pt": "init",
        "ADNI3 Year 1 Visit": "y1",
        "ADNI3 Year 2 Visit": "y2",
        "ADNI3 Year 3 Visit": "y3",
        "ADNI3 Year 4 Visit": "y4",
        "ADNI3 Year 5 Visit": "y5",
        "ADNI3 Year 6 Visit": "y6",
        "ADNIGO Month 3 MRI": "m03",
        "ADNIGO Month 60": "m60",
        "ADNIGO Month 66": "m66",
        "ADNIGO Month 72": "m72",
        "ADNIGO Month 78": "m78",
        "ADNIGO Screening MRI": "scmri",
        "No Visit Defined": "nv",
        "Unscheduled": "uns1"
    }

    # Assign the RID and PHASE using current strings
    for i, row in df.iterrows():
        # Set the RID and phase
        set_rid_and_phase(df, i, row)

    # Assign the viscode
    df['VISCODE'] = df['VISIT'].replace(repdic)

    return df


# New preprocessing code using Pandas - old code was full of holes I believe!
def preprocess_new(csvfilename, dirs, registry=None):
    # If registry passed in, encapsulate its data in a dictionary
    reg_vc_vc2_dict = {}
    reg_vc2_date_dict = {}
    if registry is not None:
        for i, row in registry.dropna(subset=('RID', 'VISCODE', 'VISCODE2', 'EXAMDATE')).iterrows():
            rid, vc, vc2, edate = str(row['RID']), str(row['VISCODE']), str(row['VISCODE2']), pd.to_datetime(
                row['EXAMDATE'])
            if rid not in reg_vc_vc2_dict:
                reg_vc_vc2_dict[rid] = {}
            if rid not in reg_vc2_date_dict:
                reg_vc2_date_dict[rid] = {}
            reg_vc_vc2_dict[rid][vc] = vc2
            reg_vc2_date_dict[rid][vc2] = edate

    for dir in dirs:

        # Read the CSV file into a PANDAS dataframe
        df = pd.read_csv(os.path.join(dir, csvfilename))

        # Rename lowercase columns, examdate
        df = df.rename(columns={
            "Scan Date": "SCANDATE",
            "Visit": "VISIT",
            "Subject": "SUBJECT"})

        # Replace illegal characters in column names
        df.columns = df.columns.str.replace('/', '_')
        df.columns = df.columns.str.replace('.', '_')
        df.columns = df.columns.str.replace(' ', '')

        # Per-table special processing
        if csvfilename.startswith('PET_META_LIST'):
            # Rename the columns
            df.rename(columns={"Scan Date": "SCANDATE"})
            for col in ('RID', 'PHASE', 'PETTYPE', 'RIGHTONE'):
                df[col] = None

            # Generate a VISCODE column
            df = fixup_imaging_csv(df)

            for i, row in df.iterrows():

                # Preprocess the PET we want
                mi_pet = "Coreg, Avg, Std Img and Vox Siz, Uniform Resolution"
                df.at[i, 'RIGHTONE'] = 1 if mi_pet in row['Sequence'] else 0

                # Preprocess PET scan type (TAU=1/Amyloid=2/other=0)
                if "FBB" in row['Sequence'] or "AV45" in row['Sequence']:
                    df.at[i, 'PETTYPE'] = 1
                elif "AV1451" in row['Sequence']:
                    df.at[i, 'PETTYPE'] = 2
                else:
                    df.at[i, 'PETTYPE'] = 0

        elif csvfilename.startswith('MRILIST'):
            for col in ('RID', 'PHASE', 'MRITYPE', 'T1ACCE'):
                df[col] = None

            # Uppercase the sequence name
            df['SEQUENCE'] = df['SEQUENCE'].str.upper()

            # Generate a VISCODE column
            df = fixup_imaging_csv(df)

            for i, row in df.iterrows():

                # Preprocess the MRI type (T1/T2)
                seq = row['SEQUENCE']
                if "MPRAGE" in seq or "MP-RAGE" in seq or "SPGR" in seq:
                    df.at[i, 'MRITYPE'] = 0
                elif "HIPP" in seq:
                    df.at[i, 'MRITYPE'] = 1

                # Preprocess Acce T1
                if "ACCE" in seq or "GRAPPA" in seq or "SENSE" in seq or "_P2_" in seq:
                    df.at[i, 'T1ACCE'] = 1
                else:
                    df.at[i, 'T1ACCE'] = 0

        elif csvfilename.startswith('APOERES'):
            df['APOE'] = None
            for i, row in df.iterrows():
                df.at[i, 'APOE'] = 'carrier' if row['APGEN1'] == 4 or row['APGEN2'] == 4 else 'non-carrier'

        elif csvfilename.startswith('allvols'):
            df['RID'] = None
            for i, row in df.iterrows():
                df.at[i, 'RID'] = int(row['ID'].split('_')[2])

        elif csvfilename.startswith('ADNI_scanner'):
            df['RID'] = None
            for i, row in df.iterrows():
                df.at[i, 'RID'] = int(row['subject_id'].split('_')[2])

        elif csvfilename.startswith('DXSUM_PDXCONV_ADNIALL'):
            df['SMARTDIAG'] = None

            # ADNI1 stores current diagnosis in DXCURREN
            idx_a1 = (df.Phase == 'ADNI1') & (pd.notna(df.DXCURREN))
            df.at[idx_a1, 'SMARTDIAG'] = df.loc[idx_a1].DXCURREN.apply(int).replace({1: 'NL', 2: 'MCI', 3: 'AD'})

            # ADNI2 stores current diagnosis and conversion status in DXCHANGE
            idx_a2go = df.Phase.isin(('ADNIGO', 'ADNI2')) & (pd.notna(df.DXCHANGE))
            df.at[idx_a2go, 'SMARTDIAG'] = df.loc[idx_a2go].DXCHANGE.replace({1: 'NL', 2: 'MCI', 3: 'AD',
                                                                              4: 'MCI', 5: 'AD', 6: 'AD',
                                                                              7: 'NC', 8: 'MCI', 9: 'NC'})

            # ADNI3 uses DIAGNOSIS varaible
            idx_a3 = (df.Phase == 'ADNI3') & (pd.notna(df.DIAGNOSIS))
            df.at[idx_a3, 'SMARTDIAG'] = df.loc[idx_a3].DIAGNOSIS.apply(int).replace({1: 'NL', 2: 'MCI', 3: 'AD'})





        # In the case of the FDG summary measurement table, we perform pivoting and compute the AD signature
        # value as the sum of the ROIs
        elif csvfilename.startswith('UCBERKELEYFDG'):

            # Merge the ROI and laterality columns
            df['ROI'] = df['ROILAT'].astype(str) + '_' + df['ROINAME']

            # Pivot (create columns for ROIs, values are means)
            df = df.pivot(index=['RID', 'UID', 'VISCODE', 'VISCODE2', 'EXAMDATE'], columns='ROI', values='MEAN')
            df = df.reset_index()

            # Add signature value
            df['ADSIGNATURE'] = df.loc[:, 'Bilateral_CingulumPost':].mean(axis=1)

        # Replace screening viscodes with BL
        for col in 'VISCODE', 'VISCODE2':
            if col in df.columns:
                df[col] = df[col].str.replace('scmri', 'bl').replace('blmri', 'bl').replace('sc', 'bl')

        # Format date fields
        for col in df.columns:
            if 'DATE' in col:
                df[col] = pd.to_datetime(df[col], errors='ignore')

        # Create a SMARTDATE field that captures best available date
        df['SMARTDATE'] = None
        df['SMARTDATESRC'] = None

        # If table has EXAMDATE or SCANDATE, etc., assign that to SMARTDATE
        for key in 'EXAMDATE', 'SCANDATE', 'MRI.DATE1':
            if key in df.columns:
                df['SMARTDATE'] = df[key]
                df['SMARTDATESRC'] = key
                break

        # If VISCODE2 is missing and VISCODE is present, assign VISCODE2 columnt
        if 'RID' in df.columns and 'VISCODE' in df.columns and 'VISCODE2' not in df.columns:
            df['VISCODE2'] = None
            for i, row in df.iterrows():
                rid, vc = str(row['RID']), str(row['VISCODE'])
                print('Trying: ', rid, vc, reg_vc_vc2_dict.get(rid, {}).get(vc))
                if rid in reg_vc_vc2_dict and vc in reg_vc_vc2_dict[rid]:
                    df.at[i, 'VISCODE2'] = reg_vc_vc2_dict[rid][vc]

        # For empty rows, try to assign from VISCODE2
        if 'RID' in df.columns and 'VISCODE2' in df.columns:
            for i, row in df.iterrows():
                rid, vc2, smartdate = str(row['RID']), str(row['VISCODE2']), row['SMARTDATE']
                if pd.isna(smartdate):
                    if rid in reg_vc2_date_dict and vc2 in reg_vc2_date_dict[rid]:
                        df.at[i, 'SMARTDATE'] = pd.to_datetime(reg_vc2_date_dict[rid][vc2])
                        df.at[i, 'SMARTDATESRC'] = 'VISCODE2'

        # Make sure smartdate is in date format
        df['SMARTDATE'] = pd.to_datetime(df['SMARTDATE'])

        # Write to the temp file
        df.to_csv(os.path.join(dir, csvfilename.replace('.csv', '_temp.csv')),
                  index=False, quoting=csv.QUOTE_ALL,
                  date_format='%Y-%m-%d')
        os.remove(os.path.join(dir, csvfilename))


# preprocess csv files
def preprocess(csvfilename, dirs, registry=None):
    mi_pet = "Coreg, Avg, Std Img and Vox Siz, Uniform Resolution"
    for dir in dirs:
        f = open(dir + '/' + csvfilename, newline='', encoding='utf-8-sig')
        pattern = re.compile('\d{3}_S_0*')
        print('Writing CSV to %s', (open(dir + '/' + csvfilename.replace('.csv', '_temp.csv'), 'w'),))
        with open(dir + '/' + csvfilename.replace('.csv', '_temp.csv'), 'w') as temp:
            for i, line in enumerate(f):
                mritype = -4
                if i == 0:
                    if "PET_META_LIST" in csvfilename:
                        header = line.replace("\n", ',\"RID\",\"PHASE\",\"PETTYPE\",\"RIGHTONE\"\n').replace(
                            "Scan Date", "SCANDATE")
                    elif "MRILIST" in csvfilename:
                        header = line.replace("\n", ',\"RID\",\"PHASE\",\"MRITYPE\",\"T1ACCE\"\n')
                    elif 'APOERES' in csvfilename:
                        header = line.replace("\n", ',\"APOE\"\n')
                    elif 'allvols' in csvfilename:
                        header = line.replace('\n', ',\"RID"\n')
                    elif 'ADNI_scanner' in csvfilename:
                        header = line.replace('\n', ',\"RID"\n')
                    else:
                        header = line
                    temp.write(
                        # header.upper()
                        header.replace(" ", "")
                            .replace("VISIT", "VISCODE2")
                            .replace("Visit", "VISCODE2")
                            .replace("/", "_")
                            .replace(".", "_")
                            .replace("EXAMDATE", "SCANDATE")
                    )
                else:

                    ##Preprocess the phase
                    if "ADNIGO" in line or "ADNI1/GO" in line:
                        phase = "ADNIGO"
                    elif "ADNI2" in line:
                        phase = "ADNI2"
                    elif "ADNI3" in line:
                        phase = "ADNI3"
                    else:
                        phase = "ADNI1"

                    if "PET_META_LIST" in csvfilename:

                        ##Preprocess the rid
                        rid = pattern.sub('', re.search('\d{3}_S_\d{4}', line).group())
                        if int(rid) > 5999: phase = "ADNI3"

                        ##Preprocess the PET we want
                        if mi_pet in line:
                            ro = 1
                        else:
                            ro = 0

                        ##Preprocess PET scan type (TAU=1/Amyloid=2/other=0)
                        if ("FBB" in line or "AV45" in line):
                            pettype = 1
                        elif "AV1451" in line:
                            pettype = 2
                        else:
                            pettype = 0

                        line_temp = line.replace('\n',
                                                 ',\"' + rid + '\",\"' + phase + '\",\"' + str(pettype) + '\",\"' + str(
                                                     ro) + '\"\n')

                    elif "MRILIST" in csvfilename:

                        ##Preprocess the rid
                        rid = pattern.sub('', re.search('\d{3}_S_\d{4}', line).group())
                        if int(rid) > 5999: phase = "ADNI3"

                        line = line.upper()
                        ##Preprocess the MRI type (T1/T2)
                        if ("MPRAGE" in line or "MP-RAGE" in line or "SPGR" in line):
                            mritype = 0
                        elif "HIPP" in line:
                            mritype = 1

                        ##Preprocess Acce T1
                        if ("ACCE" in line or "GRAPPA" in line or "SENSE" in line or "_P2_" in line):
                            acce = 1
                        else:
                            acce = 0

                        line_temp = line.replace('\n',
                                                 ',\"' + rid + '\",\"' + phase + '\",\"' + str(mritype) + '\",\"' + str(
                                                     acce) + '\"\n')

                    elif 'APOERES' in csvfilename:
                        l = line.replace('"', "").split(',')
                        if int(l[8]) == 4 or int(l[9]) == 4:
                            line_temp = line.replace('\n', ',\"carrier\"\n')
                        else:
                            line_temp = line.replace('\n', ',\"non-carrier\"\n')

                    elif 'allvols' in csvfilename:
                        ##Preprocess the rid
                        rid = pattern.sub('', re.search('\d{3}_S_\d{4}', line).group())
                        line_temp = line.replace('\n', ',\"' + rid + '\"\n')

                    elif 'ADNI_scanner' in csvfilename:
                        pattern2 = re.compile('\d{8}')
                        date = re.search('\d{8}', line).group()
                        dateTemp = date[0:4] + '-' + date[4:6] + '-' + date[6:8]
                        rid = pattern.sub('', re.search('\d{3}_S_\d{4}', line).group())
                        line_temp = line.replace('\n', ',\"' + rid + '\"\n').replace(date, dateTemp)

                    else:
                        line_temp = line.replace('scmri', 'bl').replace('blmri', 'bl').replace('sc', 'bl')

                    line_temp = dateFormat(line_temp)
                    temp.write(line_temp)
        f.close()
        os.remove(dir + '/' + csvfilename)


# normalize date format from different csv files
def dateFormat(line):
    pattern1 = re.compile('\d{1,2}/\d{1,2}/\d{4}')
    pattern2 = re.compile('\d{1,2}/\d{1,2}/\d{2}')
    datelist1 = re.findall('\d{1,2}\/\d{1,2}\/\d{4}', line)
    datelist2 = re.findall('\d{1,2}\/\d{1,2}\/\d{2}', line)
    if datelist1 != []:
        line_temp = line
        for date in datelist1:
            datetemp = date.split('/')
            datefinal = datetemp[2] + "-" + datetemp[0] + "-" + datetemp[1]
            line_temp = line_temp.replace(date, datefinal)
        return line_temp
    elif datelist2 != []:
        line_temp = line
        for date in datelist2:
            datetemp = date.split('/')
            datefinal = "20" + datetemp[2] + "-" + datetemp[0] + "-" + datetemp[1]
            line_temp = line_temp.replace(date, datefinal)
        return line_temp
    else:
        return line


# convert tsv files to csv files for upload or download
def tsv2csv(tsvfilename, tsvfilepath):
    outpath = tsvfilepath.replace(tsvfilename, '') + tsvfilename.replace('tsv', 'csv')
    numline = sum(1 for row in open(tsvfilepath, 'r'))
    with open(tsvfilepath, 'r') as tsvfile, open(outpath, 'w') as csvfile:
        for i, line in enumerate(tsvfile):
            line = line.replace('\"', '')
            fileContent = "\"" + re.sub("\t", "\",\"", line)
            fileContent = fileContent.replace('\n', '\"\n')
            if i == numline - 1 and "\n" not in fileContent:
                fileContent += "\"\n"
            csvfile.write(fileContent)
    return outpath


# create a new spreadsheet for FDG data
def FDG_preprocess(FDGcsvname):
    newfilename = 'UCBERKELEYFDG.csv'
    with open(FDGcsvname, 'r', newline='') as infile, open(newfilename, 'w', newline='') as outfile:
        reader = csv.reader(infile)
        hr = next(reader)
        hw = hr[:5] + ['Left Angular', 'Right Angular', 'CingulumPost Bilateral', 'Right Temporal', 'Left Temporal',
                       'ADSIGNATURE']
        writer = csv.DictWriter(outfile, fieldnames=hw)
        writer.writeheader()
        dict_temp = {hw[0]: '', hw[1]: '', hw[2]: '', hw[3]: '', hw[4]: '', hw[5]: '', hw[6]: '', hw[7]: '', hw[8]: '',
                     hw[9]: '', hw[10]: ''}
        for i, row in enumerate(reader):
            if i % 5 == 0:
                dict_temp[hw[0]] = row[0]
                dict_temp[hw[1]] = (row[1] if row[1] != '' else 'bl')
                dict_temp[hw[2]] = (row[2] if row[2] != '' else 'bl')
                dict_temp[hw[3]] = row[3]
                dict_temp[hw[4]] = row[4]
                dict_temp[hw[5]] = row[7]
                mean = float(row[7])
            elif i % 5 == 1:
                dict_temp[hw[6]] = row[7]
                mean += float(row[7])
            elif i % 5 == 2:
                dict_temp[hw[7]] = row[7]
                mean += float(row[7])
            elif i % 5 == 3:
                dict_temp[hw[8]] = row[7]
                mean += float(row[7])
            else:
                dict_temp[hw[9]] = row[7]
                mean += float(row[7])
                dict_temp[hw[10]] = mean / 5.0

                writer.writerow(dict_temp)
    return newfilename


# create a new spreadsheet for provenance data
def summary_preprocess(filename):
    outputtemp = 'tempsummary.csv'
    with open(filename, 'r', newline='') as infile, open(outputtemp, 'w', newline='') as outfile:
        reader = csv.reader(infile)
        h = next(reader)
        writer = csv.DictWriter(outfile, fieldnames=h)
        writer.writeheader()
        dict_temp = {h[0]: '', h[1]: '', h[2]: '', h[3]: '', h[4]: '', h[5]: ''}
        for row in reader:
            dict_temp[h[0]] = row[0]
            dict_temp[h[1]] = row[1]
            dict_temp[h[3]] = row[3]
            dict_temp[h[4]] = row[4]
            dict_temp[h[5]] = row[5]
            if (row[3] == 'DISCOVERY MR750' or row[3] == 'DISCOVERY MR750w' or row[3] == 'SIGNA HDx'
                    or row[3] == 'Signa HDxt' or row[3] == 'SIGNA Premier'):
                dict_temp[h[2]] = 'GE MEDICAL SYSTEMS'

            elif (row[3] == 'Achieva dStream' or row[3] == 'Ingenia Elition X' or row[3] == 'Ingenia' or row[
                3] == 'Achieva'
                  or row[3] == 'Achieva dStream' or row[3] == 'GEMINI' or row[3] == 'Ingenuity' or row[3] == 'Intera'):
                dict_temp[h[2]] = 'Philips Medical Systems'

            else:
                dict_temp[h[2]] = 'SIEMENS'

            writer.writerow(dict_temp)

    with open(filename, 'w', newline='') as outfile, open(outputtemp, 'r', newline='') as infile:
        for row in infile:
            outfile.write(row)

    os.remove(outputtemp)
    return filename


# add quotation marks t ocsv files before uploading them into the db
def quoteCSV(csvin, dirs):
    for dir in dirs:
        with open(dir + '/' + csvin, 'r', newline='') as input, open(dir + '/temp.csv', 'w', newline='') as output:
            for row in input:
                test = row.split('"')
                if len(test) > 1:
                    temp = ''
                    for i in range(0, len(test), 2):
                        test[i] = test[i].replace(',', '","')
                    for part in test:
                        temp += part
                    row_temp = '"{}"\r\n'.format(temp.replace('\r\n', '').replace('\n', ''))
                else:
                    row_temp = '"{}"\r\n'.format(row.replace(',', '","').replace('\r\n', '').replace('\n', ''))
                # print(row_temp)
                output.write(row_temp)
        with open(dir + '/temp.csv', 'r', newline='') as input, open(dir + '/' + csvin, 'w', newline='') as output:
            for row in input:
                output.write(row)

        os.remove(dir + '/temp.csv')
