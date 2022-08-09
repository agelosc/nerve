import sys, os
sys.path.append( os.environ['NERVE_LOCAL_PATH'] + '/lib' )

import nerve

def imageConvert():
    if len(sys.argv) == 1:
        print('No image file specified. Quiting...')
        return False
    source = sys.argv[1]


if __name__ == "__main__":
   imageConvert()
