from subprocess import run
from api import upload_file
import os
from csv_preprocessing import preprocess
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

#run([rootdir+'/auto-dl/dl'],shell=True)
print('Done')

dir_csv=rootdir + "/instance/ADNI"

csvfiles = [f for f in os.listdir(dir_csv) if os.path.isfile(os.path.join(dir_csv, f))]
filedir = [config['ADNIDB_IMPORT_SAVEDIR'], config['ADNIDB_NEO4J_IMPORT']]
print(filedir)

for csv in csvfiles:
    filename=upload_file(dir_csv+'/'+csv,filedir)

    preprocess(filename,filedir)
    filename=filename.replace('.csv','_temp.csv')
    info = update_database([filename])
    if "TAUMETA" in filename: dx_haschanged(info)
	
    print(info)
