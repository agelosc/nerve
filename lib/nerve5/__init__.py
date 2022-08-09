import os
import glob
import json

import re
import math

def error(msg):
    raise Exception(msg)

def uncamelCase(str, char=' '):
    result = re.sub('([A-Z]{1})', r'%s\1'%char, str)
    return result.title()

def pprint(data):
    import pprint
    pp = pprint.PrettyPrinter()
    pp.pprint(data)

def illegalChars(str, extraChars=None):

    chars = '^<>/{}[]~`'
    if extraChars is not None:
        chars+=extraChars
    for c in chars:
        if c in str:
            return True
    return False


def floatToStr(num, pad=3):
    n = str( round(num, pad) )
    n = n.split('.')[0] + '.' + n.split('.')[1].ljust(pad, '0')
    return n


class matrix():
    def __init__(self, *args):
        self.data = [[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]]
        if len(args) == 0:
            # Identity
            self.data = [[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]]
        else:
            if type(args[0]) is list or type(args[0]) is tuple:
                self.data[0] = [ args[0][0], args[0][1], args[0][2], args[0][3] ]
                self.data[1] = [ args[0][4], args[0][5], args[0][6], args[0][7] ]
                self.data[2] = [ args[0][8], args[0][9], args[0][10], args[0][11] ]
                self.data[3] = [ args[0][12], args[0][13], args[0][14], args[0][15]]
            else:
                self.data[0] = [ args[0], args[1], args[2], args[3] ]
                self.data[1] = [ args[4], args[5], args[6], args[7] ]
                self.data[2] = [ args[8], args[9], args[10], args[11] ]
                self.data[3] = [ args[12], args[13], args[14], args[15]]


    def __str__(self):

        txt = '\n'
        txt+= '|\n'.join( [ ''.join(['{:10}'.format( floatToStr(item) ) for item in row]) for row in self.data] )
        txt+='|'
        return txt

    def asFloat(self):
        out = []
        for i in range(4):
            for j in range(4):
                out.append( self.data[i][j] )
        return out

    @staticmethod
    def transposeMatrix(m):
        return map(list,zip(*m))

    @staticmethod
    def getMatrixMinor(m,i,j):
        return [row[:j] + row[j+1:] for row in (m[:i]+m[i+1:])]

    @staticmethod
    def getMatrixDeternminant(m):
        #base case for 2x2 matrix
        if len(m) == 2:
            return m[0][0]*m[1][1]-m[0][1]*m[1][0]

        determinant = 0
        for c in range(len(m)):
            determinant += ((-1)**c)*m[0][c]*matrix.getMatrixDeternminant(matrix.getMatrixMinor(m,0,c))
        return determinant

    @staticmethod
    def getMatrixInverse(m):
        determinant = matrix.getMatrixDeternminant(m)
        #special case for 2x2 matrix:
        if len(m) == 2:
            return [[m[1][1]/determinant, -1*m[0][1]/determinant],
                    [-1*m[1][0]/determinant, m[0][0]/determinant]]

        #find matrix of cofactors
        cofactors = []
        for r in range(len(m)):
            cofactorRow = []
            for c in range(len(m)):
                minor = matrix.getMatrixMinor(m,r,c)
                cofactorRow.append(((-1)**(r+c)) * matrix.getMatrixDeternminant(minor))
            cofactors.append(cofactorRow)
        cofactors = matrix.transposeMatrix(cofactors)
        for r in range(len(cofactors)):
            for c in range(len(cofactors)):
                cofactors[r][c] = cofactors[r][c]/determinant
        return cofactors

    def inverse(self):
        out = matrix(  )
        out.data = self.getMatrixInverse(self.data)
        return out

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __mul__(self, m):
        s = self.data
        o = matrix()
        if type(m) is float or type(m) is int:
            for i in range(4):
                for j in range(4):
                    o.data[i][j]  = self.data[i][j] * float(m)
            return o
        elif type(m) is type(self):
            o[0][0] = s[0][0]*m[0][0] + s[0][1]*m[1][0] + s[0][2]*m[2][0] + s[0][3]*m[3][0]
            o[0][1] = s[0][0]*m[0][1] + s[0][1]*m[1][1] + s[0][2]*m[2][1] + s[0][3]*m[3][1]
            o[0][2] = s[0][0]*m[0][2] + s[0][1]*m[1][2] + s[0][2]*m[2][2] + s[0][3]*m[3][2]
            o[0][3] = s[0][0]*m[0][3] + s[0][1]*m[1][3] + s[0][2]*m[2][3] + s[0][3]*m[3][3]

            o[1][0] = s[1][0]*m[0][0] + s[1][1]*m[1][0] + s[1][2]*m[2][0] + s[1][3]*m[3][0]
            o[1][1] = s[1][0]*m[0][1] + s[1][1]*m[1][1] + s[1][2]*m[2][1] + s[1][3]*m[3][1]
            o[1][2] = s[1][0]*m[0][2] + s[1][1]*m[1][2] + s[1][2]*m[2][2] + s[1][3]*m[3][2]
            o[1][3] = s[1][0]*m[0][3] + s[1][1]*m[1][3] + s[1][2]*m[2][3] + s[1][3]*m[3][3]

            o[2][0] = s[2][0]*m[0][0] + s[2][1]*m[1][0] + s[2][2]*m[2][0] + s[2][3]*m[3][0]
            o[2][1] = s[2][0]*m[0][1] + s[2][1]*m[1][1] + s[2][2]*m[2][1] + s[2][3]*m[3][1]
            o[2][2] = s[2][0]*m[0][2] + s[2][1]*m[1][2] + s[2][2]*m[2][2] + s[2][3]*m[3][2]
            o[2][3] = s[2][0]*m[0][3] + s[2][1]*m[1][3] + s[2][2]*m[2][3] + s[2][3]*m[3][3]

            o[3][0] = s[3][0]*m[0][0] + s[3][1]*m[1][0] + s[3][2]*m[2][0] + s[3][3]*m[3][0]
            o[3][1] = s[3][0]*m[0][1] + s[3][1]*m[1][1] + s[3][2]*m[2][1] + s[3][3]*m[3][1]
            o[3][2] = s[3][0]*m[0][2] + s[3][1]*m[1][2] + s[3][2]*m[2][2] + s[3][3]*m[3][2]
            o[3][3] = s[3][0]*m[0][3] + s[3][1]*m[1][3] + s[3][2]*m[2][3] + s[3][3]*m[3][3]

            return o
        elif type(m) is type(vector()):
            o = vector()
            o.setX( o[0][0]*v.x + o[0][1]*v.y  + o[0][2]*v.z + o[0][3]*1)
            o.setY( o[1][0]*v.x + o[1][1]*v.y  + o[1][2]*v.z + o[1][3]*1)
            o.setZ( o[2][0]*v.x + o[2][1]*v.y  + o[2][2]*v.z + o[2][3]*1)
            return o
        else:
            raise Exception("Type Error")



class vector():
    def __init__(self, *args):
        self.data = []
        if len(args) == 0:
            for i in range(3):
                self.data.append(0)
        else:
            if type(args[0]) is list or type(args[0]) is tuple:
                self.data.append(args[0][0])
                self.data.append(args[0][1])
                self.data.append(args[0][2])
            else:
                self.data.append(args[0])
                self.data.append(args[1])
                self.data.append(args[2])

    def set(self, value):
        if type(value) is list or type(value) is typle:
            self.data[0] = value[0]
            self.data[1] = value[1]
            self.data[2] = value[2]
        else:
            raise Exception("Type Error")

    def setX(self, value):
        self.data[0] = value
    def setY(self, value):
        self.data[1] = value
    def setZ(self, value):
        self.data[2] = value


    def get(self):
        return self.data

    def getX(self):
        return self.data[0]
    def getY(self):
        return self.data[1]
    def getZ(self):
        return self.data[2]

    def __add__(self, other):
        c = vector()
        for i in range(3):
            if type(other) is type(vector()):
                c.data[i] = self.data[i] + other.data[i]
            elif type(other) is float or type(other) is int:
                c.data[i] = self.data[i] + float(other)
            else:
                raise Exception('Type Error')
        return c

    def __sub__(self, other):
        c = vector()
        for i in range(3):
            if type(other) is type(vector()):
                c.data[i] = self.data[i] - other.data[i]
            elif type(other) is float or type(other) is int:
                c.data[i] = self.data[i] - float(other)
            else:
                raise Exception('Type Error')
        return c

    def __mul__(self, other):
        c = vector()
        for i in range(3):
            if type(other) is type(vector()):
                c.data[i] = self.data[i] * other.data[i]
            elif type(other) is float or type(other) is int:
                c.data[i] = self.data[i] * float(other)
            else:
                raise Exception('Type Error')
        return c

    def __div__(self, other):
        c = vector()
        for i in range(3):
            if type(other) is type(vector()):
                c.data[i] = self.data[i] / other.data[i]
            elif type(other) is float or type(other) is int:
                if float(other) == 0:
                    raise Exception('Cannot divide by zero')
                c.data[i] = self.data[i] / float(other)
            else:
                raise Exception('Type Error')
        return c

    def __iter__(self):
        for i in range(3):
            yield self.data[i]

    def __coerce__(self, other):
        return (self, other)

    def __getattr__(self, name):
        if name == 'x':
            return self.data[0]
        elif name == 'y':
            return self.data[1]
        elif name == 'z':
            return self.data[2]


    def __str__(self):
        return '{ %f, %f, %f }'%( self.data[0], self.data[1], self.data[2] )

    def unit(self):
        c = vector()
        mag = self.mag()
        for i in range(3):
            c.data[i] = self.data[i] / mag
        return c

    def mag(self):
        return self.magnitude()

    def magnitude(self):
        mag = 0
        for i in range(3):
            mag+= math.pow(self.data[i],2)

        return math.sqrt(mag)

class cfg:
    def __init__(self):
        pass

    @staticmethod
    def path(sel):
        if sel == 'job':
            # JOB PATH
            jobpath = 'R:/jobs'
            if jobpath[-1] != '/':
                jobpath += '/'
            return jobpath

        elif sel == 'studiolibrary':
            return "R:/software/tools/studiolibrary/lib/"
        elif sel == 'assets':
            return 'assets'

class DataObject:
    def __init__(self):
        self.path = None
        self.data = {}

    def keys(self):
        return self.data.keys()

    def setPath(self, path):
        self.path = path

    def __getitem__(self, key):
        if key in self.data.keys():
            return self.data[key]
        else:
            error(key + ' key not found in sequence')

    def __setitem__(self, key, value):
        self.data[key] = value

    def __str__(self):
        return str(self.data)

    def pprint(self):
        pprint(self.data)

    def _load(self):
        if not os.path.exists( self.path ):
            error( 'Data file not found: ' + self.path)

        self.data.update(json.load( open( self.path) ))

    def _save(self):
        with open( self.path, 'w' ) as datafile:
            json.dump( self.data, datafile)

    def update(self, data):
        for key in data.keys():
            if key in self.keys():
                # if list
                if isinstance(self.data[key], list):
                    # check if element exists
                    for e in data[key]:
                        if e not in self.data[key]:
                            self.data[key].append( e )
                # if dict
                elif isinstance(self.data[key], dict):
                    self.data[key].update( data[key] )
                # else
                else:
                    self.data[key] = data[key]

class assetBase(DataObject):
    def __init__(self):
        DataObject.__init__(self)

    def default(self, key, value):
        if key in self.keys():
            return False

        self.data[key] = value

    def datapath(self):
        path = self.jobpath()
        path+= 'assets/'
        path+= self['type'] + '/'

        return path

    def datafile(self):
        datafile = self["name"]
        datafile+= self.versionStr()
        datafile+= '.json'

        return datafile

    def versionStr(self):
        if self.has('version'):
            if self['version'] == 0:
                return ''
            else:
                return '_v' + str( str(self['version']).zfill(3) )
        else:
            latest = self.latestVersion()
            if latest is None:
                return ''
            else:
                return '_v' + str( str(latest).zfill(3) )

    def exportData(self):
        self.path = self.datapath() + self.datafile()

        # Update
        if os.path.exists(self.path):
            data = self.data.copy()
            self.importData()
            self.update(data)

        if not os.path.exists(self.datapath()):
            os.makedirs( self.datapath() )

        self._save()

    def importData(self):
        self.path = self.datapath() + self.datafile()
        if os.path.exists(self.path):
            self._load()



    def jobpath(self):
        path = cfg.path('job')
        path+= self['job'] + '/'
        path+= self['seq'] + '/'
        path+= self['shot'] + '/'

        return path

    def has(self, key):
        if key in self.data.keys() and self.data[key] is not None and self.data[key] != []:
            return True

        return False

    def versions(self):
        versions = []

        if os.path.isfile( self.datapath() + self['name'] + '.json' ):
            return None

        wc  = self.datapath() + self["name"] + '_v*.json'
        files = glob.glob( wc )
        if files is not []:
            for file in files:
                version = int( file.split('_v')[-1].replace('.json', '') )
                versions.append( version )

        versions = sorted(versions)
        return versions

    def latestVersion(self):
        versions = self.versions()

        if versions is None:
            return None

        if len(versions):
            return versions[-1]
        else:
            return 0

    def nextVersion(self):
        latestVersion = self.latestVersion()
        if latestVersion is None:
            return None

        return latestVersion + 1

class assetBaseOLD:
    def __init__(self, args):
        self.args = args

        self.ui = {}
        self.opt = {}

        # job path
        self.args["jobpath"] = cfg.path('job') + self.args["job"] + '/' + self.args["seq"] + '/' + self.args["shot"]
        if not os.path.exists(self.args["jobpath"]):
            error("Job path does not exist: " + self.args["jobpath"])

        # asset path
        self.args["assetpath"] = self.args["jobpath"] + '/' + cfg.path("assets") + '/' + self.args["type"]
        if not os.path.exists(self.args["assetpath"]):
            os.makedirs(self.args["assetpath"])

        # basename
        self.args["basename"] = self.args["job"] + '_' + self.args["seq"] + '_' + self.args["shot"] + '_' + self.args["type"] + '_' + self.args["name"]

    def versions(self):
        if 'basename' not in self.args.keys():
            error('Versions cannot be resolved, "basename" not set.')

        versions = []
        wildcard = self.args["assetpath"] + '/' + self.args["basename"] + '_v*.json'
        cassets = glob.glob( wildcard )
        if cassets is not []:
            for c in cassets:
                version = int(c.split('_')[-1][1:4])
                versions.append( version )
        versions = sorted(versions)

        return versions

    def nextVersion(self):
        return self.latestVersion() + 1

    def latestVersion(self):
        versions = self.versions()
        if len(versions):
            return versions[-1]
        else:
            return 0

    def filename(self):
        if 'basename' not in self.args.keys():
            error('Filename cannot be resolved, "basename" not set.')
        if 'version' not in self.args.keys():
            error('Filename cannot be resolved, "version" not set.')
        if 'extension' not in self.args.keys():
            error('Filename cannot be resolved, "extension" not set.')

        return self.args["basename"] + '_v' + str(self.args["version"]).zfill(3) + '.' + self.args["extension"]

    def datafilename(self):
        if 'basename' not in self.args.keys():
            error('Data Filename cannot be resolved, "basename" not set.')
        if 'version' not in self.args.keys():
            error('Data Filename cannot be resolved, "version" not set.')

        return self.args["basename"] + '_v' + str(self.args["version"]).zfill(3) + '.json'

    def filepath(self):
        return self.args["assetpath"] + '/' + self.filename()

    def datafilepath(self):
        return self.args["assetpath"] + '/' + self.datafilename()

    def exportData(self):
        with open(self.datafilepath(), 'w') as datafile:
            json.dump(self.args, datafile)

    def importData(self):
        # Validate
        if not os.path.exists( self.datafilepath() ):
            nerve.error('Asset not found: "'+self.datafilename().replace('.json', ''))

        data = json.load( open( self.datafilepath()) )
        for key in data.keys():
            self.args[key] = data[key]

    def setDefaultOptions(self):
        for key in self.opt.keys():
            if key not in self.args.keys():
                self.args[key] = self.opt[key][0]



class sequence(DataObject):
    def __init__(self, path=None):
        DataObject.__init__(self)

        if path is not None:
            self.name = self.basename(path)
            self.path = path

    def save(self):
        if 'shots' not in self.data.keys():
            self.data['shots'] = []

        self._save()

    def shotName(self, shot):
        return 'S%s: [%s - %s]'%(str(shot["order"]).zfill(2), str(str(shot["startFrame"])).zfill(4), str(shot["endFrame"]).zfill(4))

    def getShotByName(self, name):
        for shot in self["shots"]:
            if self.shotName(shot) == name:
                return shot

    def load(self):
        self._load()
        self.sort()

    def sort(self):
        self.data["shots"] = sorted( self.data["shots"], key=lambda k: k["order"] )

    def sortOLD(self):
        order = {}
        for shot in self.data["shots"]:
            order[ int( shot["order"] )] = shot

        l = []
        for key in order.keys():
            l.append(key)

        l = sorted(l)
        orderedShots = []
        for i in l:
            orderedShots.append(order[i])

        self.shots = orderedShots

    @staticmethod
    def basename( path ):
        return os.path.basename( path ).replace('seq_', '').replace( '.json', '' )

    @staticmethod
    def list(path):
        files = []
        for f in glob.glob(path + '/seq_*.json'):
            files.append( f )
        return files
