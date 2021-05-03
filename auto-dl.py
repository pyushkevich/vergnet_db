from subprocess import run
from api import upload_file
import os
import sys
from csv_preprocessing import preprocess
from csv_preprocessing import mergeLMrows
from csv_preprocessing import quoteCSV
from database_v2 import update_database,dx_haschanged


# Get the root directory
rootdir=os.environ.get('ADNIDB_ROOT', None)
if rootdir is None:
    print('Environment variable ADNIDB_ROOT is not set')
    sys.exit(-1)

# Global configuration entries
config = {
    'ADNIDB_IMPORT_SAVEDIR' : os.environ.get('ADNIDB_IMPORT_SAVEDIR', os.path.join(rootdir, 'instance/savefile')),
    'ADNIDB_NEO4J_IMPORT' :   os.environ.get('ADNIDB_NEO4J_IMPORT',   os.path.join(rootdir, 'instance/db/import'))
}

run([rootdir+'/auto-dl/dl'],shell=True)
print('Done')

dir_csv=rootdir + "/instance/ADNI"

csvfiles = [f for f in os.listdir(dir_csv) if os.path.isfile(os.path.join(dir_csv, f))]
filedir = [config['ADNIDB_IMPORT_SAVEDIR'], config['ADNIDB_NEO4J_IMPORT']]

for csv in csvfiles:
    # For NEUROBAT, we merge the bl and sc data as logical memory scores are coming from the sc visit but they should really belong to bl, and the available data from those two visits are mutually exclusive. So merge them. Throw away USERDATE and USERDATE2 data from sc visit.
    if "NEUROBAT" in csv:
        mergeLMrows( dir_csv + '/' + csv , dir_csv + '/' + csv )
        quoteCSV( csv, [ dir_csv ] ) # Add quotes, else will get SemanticError
    filename=upload_file(dir_csv+'/'+csv,filedir)
    print('FN:', filename, 'D:', filedir)

    preprocess(filename,filedir)
    filename=filename.replace('.csv','_temp.csv')
    info = update_database([filename])
    if "TAUMETA" in filename: dx_haschanged(info)
	
    print(info)
