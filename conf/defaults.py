import os, sys
import json, pathlib

sys.path.append( str(pathlib.Path.cwd().parent / 'lib') )
import nerve

conf = {}
conf['JOB'] = '$TEMP/nerve'
conf['DIR'] = 'stage'

with open('00-defaults.json', 'w') as outfile:
    json.dump(conf, outfile, indent=4)
