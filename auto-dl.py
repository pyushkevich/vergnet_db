from subprocess import run
from api import upload_file
import os
import sys
from csv_preprocessing import preprocess_new
from csv_preprocessing import mergeLMrows
from csv_preprocessing import quoteCSV
from database_v2 import update_database,dx_haschanged
import pandas
import argparse
import re

# Create an argument parser
parse = argparse.ArgumentParser(
    description="ADNI CSV downloader and database importer script")

# Add the arguments
parse.add_argument('--cached-csv', dest='use_cached_csv', action='store_true', default=False, help='Skip CSV downloading')
parse.add_argument('--cached-pre', dest='use_cached_pre', action='store_true', default=False, help='Skip CSV downloading and preprocessing ')
parse.add_argument('--no-import', dest='no_import', action='store_true', default=False, help='Skip import into the database')
parse.add_argument('-f', dest='filter', default=None, help='Filter - only import specific CSV')
parse.add_argument('--skip-to-filter', dest='skip_to_filter', default=None, help='Filter - only import after specific CSV')
args = parse.parse_args()

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

if not args.use_cached_csv and not args.use_cached_pre:
    run([rootdir+'/auto-dl/dl'],shell=True)
    print('Done downloading files')

dir_csv=rootdir + "/instance/ADNI"

csvfiles = [f for f in os.listdir(dir_csv) if os.path.isfile(os.path.join(dir_csv, f))]
filedir = [config['ADNIDB_IMPORT_SAVEDIR'], config['ADNIDB_NEO4J_IMPORT']]

# Read the registry CSV. This can be used to link visit codes to dates, facilitating
# time-based merges. We will use pandas to read the registry
df_reg = pandas.read_csv(os.path.join(dir_csv, 'REGISTRY.csv'))

# Do we skip up to a filter
filter_found = False
for csv in csvfiles:

    # Skip registry and skip everything if the filter not fond
    if csv.endswith('REGISTRY.csv'):
        continue

    # Check filters
    if args.filter is not None:
        if re.compile(args.filter).search(csv) is None:
            continue

    # Check skip to filter
    if filter_found is False and args.skip_to_filter is not None:
        if re.compile(args.skip_to_filter).search(csv) is not None:
            filter_found = True
        continue

    # For NEUROBAT, we merge the bl and sc data as logical memory scores are coming from the sc visit but they should
    # really belong to bl, and the available data from those two visits are mutually exclusive. So merge them. Throw
    # away USERDATE and USERDATE2 data from sc visit.
    if "NEUROBAT" in csv:
        mergeLMrows( dir_csv + '/' + csv , dir_csv + '/' + csv )
        quoteCSV( csv, [ dir_csv ] ) # Add quotes, else will get SemanticError

    filename=upload_file(dir_csv+'/'+csv,filedir)
    print('FN:', filename, 'D:', filedir)

    if not args.use_cached_pre:
        # Perform main preprocessing
        print('Preprocessing %s in directories ' % filename, filedir)
        preprocess_new(filename, filedir, registry=df_reg)

    if not args.no_import:
        # Update the database
        filename=filename.replace('.csv','_temp.csv')
        info = update_database([filename])
        if "TAUMETA" in filename: dx_haschanged(info)
        print(info)
