# -*- coding: utf-8 -*-
import os, sys, errno

def pprint(data):
    import pprint
    pp = pprint.PrettyPrinter()
    pp.pprint(data)

def uncamelCase(str, char=' '):
    ''' Converts "JeremySpokeInClassToday" to "Jeremy Spoke In Class Today" '''
    import re
    result = re.sub('([A-Z]{1})', r'%s\1'%char, str)
    return result.title()

def illegalCharacters(str, characters='&<>{}[]~`'):
    for char in characters:
        if char in str:
            return True

def isEnglish(s):
    try:
        s.encode(encoding='utf=8').decode('ascii')
    except:
        return False
    else:
        return True

def GetFormats(invert=False):
    data = {}
    data['usda'] = 'USDAscii'
    data['usd'] = 'USD'
    data['abc'] = 'Alembic'
    data['mb'] = 'MayaBinary'
    data['ma'] = 'MayaAscii'
    data['fbx'] = 'FBX'
    data['obj'] = 'OBJ'
    data['rs'] = 'RedshiftProxy'

    if invert:
        return dict( (v,k) for k,v in data.items() )

    return data

def Config():
    import json
    conf = {}

    # Current Directorys
    cwd = Path(__file__)

    # Nerve Root Directory
    nrvpath = cwd.GetParent(3)
    # Load Config Files
    files = Path.Glob(nrvpath+'conf/*.json')
    for file in files:
        with open(str(file)) as json_file:
            data = json.load(json_file)
        conf.update( data )

    conf['path'] = nrvpath
    return conf

def versionAsString(version):
    return 'v{}'.format( str(version).zfill(3) )

def versionAsInt(version):
    if version == '<next>':
        return 0
    return int(version[1:])

class Path:
    def __init__(self, path, separator='/'):
        self.separator = separator
        self.segments = []
        self.content = None
        self.isDir = True

        if isinstance(path, Path):
            path = path.AsString(separator)

        # Clean common path inaccuracies
        if path[:1] == '\\':
            path = Path._resolveMapped(path)

        path = path.replace('\\', '/')
        for i in range(10):
            path = path.replace('//', '/')

        # Set Separator
        path = path.replace('/', self.separator)

        # Set Object Data
        self.segments = path.rstrip(self.separator).split(self.separator)
        filename, extension = os.path.splitext(self.segments[-1])
        self.isDir = not extension

        # Expand Environmental Variables
        segments = []
        for i in range(len(self.segments)):
            segments.append( self.segments[i])
            if self.segments[i].startswith('$'):
                if self.segments[i][1:] in os.environ.keys():
                    segments.pop()
                    segments.extend( Path(os.environ[ self.segments[i][1:]]  ).segments )
        self.segments = segments

    @staticmethod
    def _resolveMapped(path):
        import pathlib
        path = pathlib.Path(path).resolve()

        mapped_paths = []
        for drive in 'ZYXWVUTSRQPONMLKJIHGFEDCBA':
            root = pathlib.Path('{}:/'.format(drive))
            try:
                mapped_paths.append( root / path.relative_to(root.resolve())  )
            except (ValueError, OSError):
                pass

        return str(min(mapped_paths, key=lambda x: len(str(x)), default=path))

    def AsString(self, separator=None):
        separator = separator if separator else self.separator
        return separator.join(self.segments)

    def __repr__(self):
        return self.AsString()

    def __add__(self, other):
        if not isinstance(other, Path):
            other = Path(other)
        if other.IsAbsolute():
            other = other.GetRelative(1)
        other.segments = self.segments+other.segments
        return other

    def __eq__(self, other):
        if not isinstance(other, Path):
            other = Path(other)
        return self.segments == other.segments

    def __ne__(self, other):
        if not isinstance(other, Path):
            other = Path(other)
        return self.segments != other.segments

    def IsAbsolute(self):
        if not len(self.segments):
            return False
        return os.path.isabs(self.AsString())

        #if self.segments[0][1] == ':':
            #return True
        #return not self.segments[0]

    @staticmethod
    def GetDrives():
        ''' https://stackoverflow.com/questions/4188326/in-python-how-do-i-check-if-a-drive-exists-w-o-throwing-an-error-for-removable '''
        import ctypes, itertools, string, platform

        if 'Windows' not in platform.system():
            return []
        drive_bitmask = ctypes.cdll.kernel32.GetLogicalDrives()
        return list(itertools.compress(string.ascii_uppercase, map(lambda x:ord(x) - ord('0'), bin(drive_bitmask)[:1:-1])))

    def GetParent(self, offset=1):
        return Path(self.separator.join( self.segments[:-offset] ))

    def HasParent(self):
        if len(self.segments) == 2 and self.IsAbsolute():
            return False
        return len(self.segments)>1

    def GetRelative(self, offset):
        if offset==0:
            return self
        if offset > 0:
            if self.IsAbsolute():
                self.segments.pop(0)
            return Path(self.separator.join( self.segments[:offset] ))
        if offset < 0:
            return Path(self.separator.join( self.segments[offset:] ))

    def GetRelativeTo(self, path):
        path = Path(path)
        relpath = os.path.relpath(self.AsString(), path.AsString())
        return Path(relpath)

    def GetHead(self):
        return self.segments[-1]

    def GetName(self):
        name = self.GetFileName()
        if self.HasVersion():
            name = name.replace('_'+self.GetStringVersion(), '')
        return name

    def GetFileName(self):
        name, ext = os.path.splitext( self.GetHead() )
        if self.HasFrame():
            return name.replace('.'+self.GetFrameAsString(), '')
        return name

    def GetExtension(self):
        name,ext = os.path.splitext( self.GetHead() )
        return ext[1:]

    @staticmethod
    def GetThisFile():
        return Path( __file__ )

    def IsDir(self):
        return self.isDir

    def IsFile(self):
        return not self.isDir

    def IsValid(self):
        import errno

        segments = self.segments
        if not len(segments):
            return False
        if not self.IsAbsolute():
            return False
        if segments[0][1] != ':':
            return False
        if segments[0][0] not in Path.GetDrives():
            return False

        drivepath = segments[0]
        drivename = segments[0][1]
        segments.pop(0)

        try:
            for seg in segments:
                if not seg.isalnum():
                    return False
                if illegalCharacters(seg):
                    return False
                if not isEnglish(seg):
                    return False
                try:
                    os.lstat(os.path.join('C:', seg))
                except OSError as exc:
                    if hasattr(exc, 'winerror'):
                        if exc.winerror == 123:
                            return False
                        elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                            return False
        except TypeError as exc:
            return False
        else:
            return True

    def Exists(self):
        return os.path.exists(self.AsString())

    def SetContent(self, content):
        self.content = content

    def GetContent(self):
        if not self.content:
            return ''
        if isinstance(self.content, Path):
            return self.content.Read()
        return self.content

    def Create(self):
        if self.IsFile():
            self.GetParent().Create()
            with open(self.AsString(), 'w') as writer:
                writer.write(self.GetContent())
        else:
            if not self.Exists():
                os.makedirs(self.AsString())

    def Remove(self, recursive=False):
        if self.IsFile():
            os.remove(self.AsString())
        else:
            if recursive:
                import shutil
                shutil.rmtree( self.AsString(), ignore_errors=True )
            else:
                os.rmdir(self.AsString())

    def Read(self):
        with open(self.AsString(), 'r') as reader:
            return reader.read()

    def HasVersion(self):
        name, ext = os.path.splitext( self.GetHead() )
        import re
        match = re.search('(_v)([0-9]+)$', name)
        if match:
            return True
        return False

    def HasFrame(self):
        name, ext = os.path.splitext( self.GetHead() )
        import re
        match = re.search('\.([0-9]+)$', name)
        if match:
            return True
        return False

    def GetFrame(self):
        return int(self.GetFrameAsString())

    def GetFrameAsString(self):
        name, ext = os.path.splitext( self.GetHead() )
        import re
        match = re.search('\.([0-9]+)$', name)
        if match:
            return match.group(1)
        return None

    def GetVersion(self):
        import re
        name, ext = os.path.splitext( self.GetHead() )
        match = re.search('(_v)([0-9]+)$',name)
        if match:
            return int(match.group(2))
        return None

    def GetStringVersion(self):
        name, ext = os.path.splitext( self.GetHead() )
        import re
        match = re.search('(_)(v[0-9]+)$', name)
        if match:
            return match.group(2)
        return None

    def Copy(self, dest):
        from shutil import copyfile

        dest = Path(dest)
        if dest.HasParent() and not dest.GetParent().Exists():
            os.makedirs( dest.GetParent().AsString() )
        return copyfile(self.AsString(), dest.AsString())

    def Move(self, dest):
        dest = Path(dest)
        if dest.HasParent() and not dest.GetParent().Exists():
            os.makedirs( dest.GetParent().AsString() )

        return os.replace( self.AsString(), dest.AsString() )

    @staticmethod
    def Glob(pattern):
        from glob import glob
        if not isinstance(pattern, Path):
            pattern = Path(pattern)
        return [Path(item) for item in sorted(glob(pattern.AsString()))]
conf = Config()
def GetUserData():
    import json

    datafile = Path('$APPDATA') + 'nerve' + 'userData.json'
    if datafile.Exists():
        with open(datafile.AsString()) as json_file:
            data = json.load(json_file)
        return data
    else:
        return {}
userdata = GetUserData()
def SetUserData(indata=None):
    import json
    if indata:
        userdata.update(indata)

    datafile = Path('$APPDATA') + 'nerve' + 'userData.json'
    if not datafile.Exists():
        datafile.SetContent('{}')
        datafile.Create()
    with open(datafile.AsString(), 'w') as outfile:
        json.dump(userdata, outfile)

class USD:
    @classmethod
    def CreateOrOpen(cls, path):
        from pxr import Usd, Sdf, Kind, UsdGeom, UsdShade

        if not isinstance(path, Path):
            path = Path(path)
        if not path.GetParent().Exists():
            path.GetParent().Create()

        layer = Sdf.Layer.FindOrOpen(path.AsString())
        if not layer:
            layer = Sdf.Layer.CreateNew(path.AsString())

        return layer

    @classmethod
    def FindOrOpen(cls, path):
        from pxr import Usd, Sdf, Kind, UsdGeom, UsdShade

        if not isinstance(path, Path):
            path = Path(path)
        if not path.GetParent().Exists():
            path.GetParent().Create()

        layer = Sdf.Layer.FindOrOpen(path.AsString())
        if not layer:
            raise Exception('Layer does not exist')

        return layer

    @classmethod
    def OpenAsAnonymous(cls, path, metadataOnly=True):
        from pxr import Usd, Sdf, Kind, UsdGeom, UsdShade

        if not isinstance(path, Path):
            path = Path(path)
        return Sdf.Layer.OpenAsAnonymous(path.AsString(), metadataOnly)

    @classmethod
    def StitchClips(cls, path, clips, clipPath, frameRange, interpolate=False):
        from pxr import Sdf, Usd, UsdUtils

        layer = USD.CreateOrOpen(path)
        UsdUtils.StitchClips( layer, clips, Sdf.Path(clipPath), frameRange[0], frameRange[1], interpolateMissingClipValues=interpolate )
        stage = Usd.Stage.Open(layer)
        prim = stage.GetPrimAtPath(clipPath)
        stage.SetDefaultPrim(prim)
        layer.Save()

class Job:
    def __init__(self, path=None, **kwargs):
        self.layerpath = Path(conf['DIR']) + 'job.usda'
        self.cover = Path(conf['DIR']) + 'job.png'

        self.data = {}
        # Defaults
        defaults = {}
        defaults['path'] = Path(path) if path is not None else Path(conf['JOB'])
        defaults['fps'] = 25
        for key,val in defaults.items():
            self.data[key] = kwargs[key] if key in kwargs.keys() else val


    def GetCoverPath(self):
        return Path(self.data['path']) + Path(self.cover)

    def Create(self):
        from pxr import Usd, UsdGeom
        path = self.data['path'] + conf['DIR'] + 'job.usda'
        path.GetParent().Create()
        layer = USD.CreateOrOpen( path )
        layer.Clear()
        stage = Usd.Stage.Open(layer)

        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
        layer.Save()

    @staticmethod
    def AddToRecent(path):
        key = 'recentJobs'
        if key in userdata.keys() and path not in userdata[key]:
            userdata[key].append( path )
        else:
            userdata[key] = [ path ]
        SetUserData()

    @staticmethod
    def GetRecent():
        key = 'recentJobs'
        if key in userdata.keys():
            recents = []
            update = False
            for rec in userdata[key]:
                if not Job(rec).Exists():
                    userdata[key].remove(rec)
                    update = True
            if update:
                SetUserData()
            return userdata[key]
        else:
            return []

    def Exists(self):
        return (self.data['path'] + self.layerpath).Exists()

class App:
    def __init__(self):
        pass

    @staticmethod
    def explore():
        pass

class Base:
    def __init__(self, **kwargs):
        for attr in ['data', 'paths', 'patterns']:
            if not hasattr(self, attr):
                setattr(self, attr, {})

        defaults = {}
        defaults['job'] = os.environ['JOB'] if 'JOB' in os.environ.keys() else Path(conf['JOB'])
        defaults['description'] = ''
        self.SetDefaults(defaults, **kwargs)

    def SetDefaults(self, defaults, **kwargs):
        for key,val in defaults.items():
            self.data[key] = kwargs[key] if key in kwargs.keys() else val

    def GetFilePath(self, key='main'):
        if key not in self.paths.keys():
            raise Exception('Invalid path request: '+key)
        return Path(self.paths[key])

    def GetFilePattern(self, key):
        if key not in self.patterns.keys():
            raise Exception('Invalid pattern request: '+key)
        return Path(self.patterns[key])

    def GetPath(self):
        return Path(self.data['path'])

    def GetName(self):
        return self.GetPath().GetHead()

    def GetJobPath(self):
        return Path(self.data['job']) + Path( conf['DIR'] )

    def SetJobPath(self, path):
        self.data['job'] = Path(path)
        self.SetPaths()

    def HasChildren(self):
        return len(self.GetChildren())

    def SetCustomLayerData(self, layer=None):
        if layer is None:
            layer = USD.FindOrOpen(self.GetFilePath())
        data = {}
        for key,val in self.data.items():
            if key == 'version':
                continue
            if isinstance(val, (str, int, float, bool, dict)):
                data[key] = val
            layer.customLayerData = data
        layer.Save()

    def GetCustomLayerData(self, layer=None):
        if layer is None:
            layer = USD.OpenAsAnonymous(self.GetFilePath())
        return layer.customLayerData

class Layer(Base):
    def __init__(self, path='', **kwargs):
        Base.__init__(self, **kwargs)

        defaults = {}
        defaults['path'] = str(path)
        defaults['description'] = None
        defaults['frameRange'] = None
        defaults['fps'] = None
        self.SetDefaults(defaults, **kwargs)
        self.SetPaths()

    def SetPaths(self):
        self.paths['main'] = '{0}/{1}.usda'.format( self.GetRootPath(), self.GetName() )
        self.patterns['children'] = '{0}/{1}/*.usd*'.format( self.GetRootPath(), self.GetName() )
        self.patterns['sublayers'] = '{0}/*.usd*'.format(self.GetRootPath())
        self.paths['thumb'] = '{0}/{1}.jpg'.format(self.GetRootPath(), self.GetName())

    def Create(self):
        layer = USD.CreateOrOpen( self.GetFilePath() )
        #layer.SetPermissionToEdit(True)

        self.SetCustomLayerData(layer)

        # Metadata
        if self.data['fps']:
            layer.framesPerSecond = self.data['fps']
        if self.data['frameRange']:
            layer.startTimeCode = self.data['frameRange'][0]
            layer.endTimeCode = self.data['frameRange'][1]

        # Inherit Parent Layer
        if self.GetPath() != '':
            relpath = '../{}.usda'.format( self.GetParentLayer().GetName() )
            if relpath not in layer.subLayerPaths:
                layer.subLayerPaths.insert(0, relpath)

        layer.Save()

    def GetRootPath(self):
        jobpath = self.GetJobPath()
        if self.GetPath() == '':
            return jobpath
        return jobpath + 'job' + self.GetPath().GetParent()

    def GetName(self):
        if self.GetPath() == '':
            return Path('job')
        return self.GetPath().GetHead()

    def HasParentLayer(self):
        return self.GetPath() != ''

    def GetParentLayer(self):
        if self.HasParentLayer():
            return Layer(self.GetPath().GetParent())
        return Layer('')

    def GetChildren(self):
        files = Path.Glob(self.GetFilePattern('children'))
        children = []
        for file in files:
            layer = USD.OpenAsAnonymous( file.AsString() )
            thispath = '../{}.usda'.format( self.GetName() )
            if thispath in layer.subLayerPaths:
                children.append( file.GetFileName() )

        return children

    def HasFrameRange(self):
        if not self.GetFilePath().Exists():
            return False
        layer = USD.OpenAsAnonymous( self.GetFilePath() )
        if layer.HasStartTimeCode() and layer.HasEndTimeCode():
            return True
        return False

    def GetFrameRange(self):
        if not self.GetFilePath().Exists():
            raise Exception('Layer does not exist')
        if not self.HasFrameRange():
            raise Exception('Layer does not have frame range set')
        layer = USD.OpenAsAnonymous( self.GetFilePath() )
        return (layer.startTimeCode, layer.endTimeCode)

    def HasDescription(self):
        if not self.GetFilePath().Exists():
            return False
        layer = USD.OpenAsAnonymous(self.GetFilePath())
        if layer.HasCustomLayerData() and 'description' in layer.customLayerData:
            return True
        return False

    def GetDescription(self):
        if not self.GetFilePath().Exists():
            raise Exception('Layer does not exist.')
        if not self.HasDescription():
            raise Exception('Layer does not have description set.')
        layer = USD.OpenAsAnonymous( self.GetFilePath() )
        return layer.customLayerData['description']

    def GetSublayers(self):
        pattern = '{}/*.usda*'.format( self.GetRootPath() )
        if self.GetPath() == '':
            pattern = '{}/job/*.usd*'.format( self.GetRootPath() )

        files = Path.Glob( pattern )

        layer = USD.OpenAsAnonymous( self.GetFilePath() )
        sublayers = []
        for file in files:
            if file.HasVersion():
                continue
            relpath = './'+file.GetRelative(-1).AsString()
            if relpath in layer.subLayerPaths:
                sublayers.append(file.GetFileName())

        return sublayers

class SublayerBase(Base):
    def __init__(self, path, **kwargs):
        Base.__init__(self, **kwargs)

    def GetExtension(self):
        format = self.GetFormat()

    def GetFormat(self):
        return self.format

    def GetLayer(self):
        return Layer(path=self.data['layer'])

    def GetVersion(self, offset=0):
        if int(self.data['version']) == 0:
            files = Path.Glob( self.GetFilePattern('session') )
            if not len(files):
                self.data['version'] = 1
                return 1 # First Version

            files = [{'version':item.GetVersion(), 'path':item} for item in files]
            files = sorted( files, key=lambda i:(i['version']), reverse=False)
            version = files[-1]['version']+1+offset # Next Version
            self.data['version'] = version
            return version

        if int(self.data['version']) < 0:
            files = Path.Glob( self.GetFilePattern('session') )
            if not len(files):
                return 1 # First Version
            files = [{'version':item.GetVersion(), 'path':item} for item in files]
            files = sorted( files, key=lambda i:(i['version']), reverse=False)

            version = files[-1]['version']+self.data['version']+1 # Latest Minus Negative Offset
            self.data['version'] = version
            return version

        return self.data['version'] # Current Version

    def GetLatestVersion(self):
        self.data['version'] = -1
        return self.GetVersion()

    def GetVersionAsString(self, offset=0):
        return 'v{}'.format( str(self.GetVersion(offset)).zfill(3) )

    def GetVersionsFromDisk(self):
        files = Path.Glob(self.GetFilePattern('versions'))
        versions = []
        for file in files:
            if file.GetVersion() not in versions:
                versions.append(file.GetVersion())
        return versions

    def GetFormatsOLD(self):
        files = Path.Glob(self.GetFilePattern('formats'))
        formats = []
        for file in files:
            formats.append(file.GetExtension())
        return formats

    def GetThumbnail(self):
        data = self.GetAssetInfo()
        if 'thumbnail' not in data.keys():
            return False
        if not self.GetFilePath('thumbnail').Exists():
            return False

        return self.GetFilePath('thumbnail').AsString()

    def SetAssetInfo(self, data):
        from pxr import Usd, Sdf

        if not self.GetFilePath().Exists():
            return {}

        layer = USD.FindOrOpen(self.GetFilePath())
        stage = Usd.Stage.Open( layer.identifier )
        prim = self.GetPrim(stage)
        modelAPI = Usd.ModelAPI(prim)
        versionSet = prim.GetVariantSet('version')
        versionSet.SetVariantSelection( self.GetVersionAsString() )
        with versionSet.GetVariantEditContext():
            formatSet = prim.GetVariantSet('format')
            formatSet.SetVariantSelection( self.GetFormat() )
            with formatSet.GetVariantEditContext():
                modelAPI = Usd.ModelAPI(prim)
                modelAPI.SetAssetInfo(data)
        layer.Save()

    def GetAssetInfo(self, key=None):
        from pxr import Usd, Sdf

        if not self.GetFilePath().Exists():
            return {}

        stage = Usd.Stage.Open( self.GetFilePath().AsString() )
        prim = self.GetPrim(stage)
        modelAPI = Usd.ModelAPI(prim)
        versionSet = prim.GetVariantSet('version')
        versionSet.SetVariantSelection( self.GetVersionAsString() )
        with versionSet.GetVariantEditContext():
            formatSet = prim.GetVariantSet('format')
            formatSet.SetVariantSelection( self.GetFormat() )
            with formatSet.GetVariantEditContext():
                modelAPI = Usd.ModelAPI(prim)
                data = modelAPI.GetAssetInfo()

                if key is None:
                    return data

                if key not in data.keys():
                    raise Exception('{} key was not found in asset info'.format(key))
                    return False

                return data[key]

    def GetFormats(self):
        from pxr import Usd, Sdf
        if not self.GetFilePath().Exists():
            return []

        stage = Usd.Stage.Open( self.GetFilePath().AsString() )
        prim = self.GetPrim(stage)
        versionSet = prim.GetVariantSet('version')
        #if self.GetVersionAsString() not in versionSet.GetVariantNames():
            #raise Exception('Variant Version {} not found.'.format( self.GetVersionAsString() ))

        versionSet.SetVariantSelection( self.GetVersionAsString() )
        formatSet = prim.GetVariantSet('format')
        return formatSet.GetVariantNames()

    def GetVersions(self, fromDisk=False):
        if not self.GetFilePath().Exists():
            return []

        if fromDisk:
            return self.GetVersionsFromDisk()

        from pxr import Usd, Sdf
        stage = Usd.Stage.Open( self.GetFilePath().AsString() )
        prim = self.GetPrim(stage)
        versionSet = prim.GetVariantSet('version')
        return [ versionAsInt(v) for v in versionSet.GetVariantNames() ]

    def GetVersionsAsString(self, fromDisk=False):
        return [versionAsString(v) for v in self.GetVersions(fromDisk)]

    def SetSession(self, session=None, mode=None):
        # Modes: copy | move | keep | None
        if not session:
            return True

        session = Path(session)
        self.format = session.GetExt().lower()

        if not mode:
            self.paths['session'] = session
            return True

        if mode == 'copy':
            session.Copy( self.GetFilePath('session') )
            return True

        if mode == 'move':
            session.Move( self.GetFilePath('session') )
            return True

        raise Exception('mode {} is invalid'.format(mode))

    def GetPrimPath(self):
        name = self.GetName()
        return '/nerve/{}s/{}'.format(self.__class__.__name__, name)

    def GetPrim(self, stage=None):
        if not stage:
            stage = Usd.Open( self.GetFilePath().AsString() )
        primpath = self.GetPrimPath()
        prim = stage.GetPrimAtPath( primpath )
        if not prim:
            prim = stage.DefinePrim( primpath )
        return prim

    def AttachThumbnail(self, filepath):
        from pxr import Sdf

        if not self.GetFilePath('session').Exists():
            return False

        filepath = Path(filepath)
        if not filepath.Exists():
            return False

        filepath.Copy( self.GetFilePath('thumbnail') )
        data = self.GetAssetInfo()
        data['thumbnail'] = True
        self.SetAssetInfo(data)
        return True

    def Create(self, session=None, mode=None):
        from pxr import Usd, Sdf, Kind, UsdGeom, UsdShade
        from datetime import datetime
        import getpass

        if not self.GetPath():
            raise Exception('Empty Sublayer Path. Skipping Export.')

        # Copy/Move/Keep Session File
        self.SetSession(session, mode)

        # Paths
        abspath = self.GetFilePath('session').AsString()
        relpath = './'+self.GetFilePath('session').GetRelative(-2).AsString()
        # Absolute Path if session is kept, relative if copied/moved to project
        outpath = abspath if session and not mode else relpath
        #outpath = relpath

        # Main File
        layer = USD.CreateOrOpen( self.GetFilePath() )

        # Sublayer only if session is usd
        if self.GetFormat().lower() in ['usd', 'usda']:
            layer.subLayerPaths = [outpath]

        # Set Sublayer Custom Layer Data
        self.SetCustomLayerData(layer)

        #layer.SetPerimissionToEdit(True)
        stage = Usd.Stage.Open(layer.identifier)

        # Version Variant
        prim = self.GetPrim(stage)

        versionSet = prim.GetVariantSets().AddVariantSet('version')
        versionSet.AddVariant( self.GetVersionAsString() )
        versionSet.SetVariantSelection( self.GetVersionAsString() )
        with versionSet.GetVariantEditContext():
            modelAPI = Usd.ModelAPI(prim)
            data = {}
            data['description'] = self.data['description'] if 'description' in self.data.keys() else ''
            if 'thumbnail' in self.data.keys() and nerve.Path(self.data['thumbnail']).Exists():
                data['thumbnail'] = True
            data['date'] = datetime.now().strftime('%a %d-%b-%y %H:%M:%S')
            data['user'] = getpass.getuser()
            modelAPI.SetAssetInfo(data)

            formatSet = prim.GetVariantSets().AddVariantSet('format')
            formatSet.AddVariant( self.GetFormat() )
            formatSet.SetVariantSelection( self.GetFormat() )
            with formatSet.GetVariantEditContext():
                modelAPI = Usd.ModelAPI(prim)
                data = {}
                data['name'] = self.GetFormat()
                data['identifier'] = Sdf.AssetPath(outpath)
                data['date'] = datetime.now().strftime('%a %d-%b-%y %H:%M:%S')
                data['user'] = getpass.getuser()
                modelAPI.SetAssetInfo(data)

        layer.Save()

        # Sublayer to shot
        layer = USD.FindOrOpen( self.GetLayer().GetFilePath() )
        sublayerFile = './'+self.GetFilePath().GetHead()
        if self.GetFormat().lower() in ['usd', 'usda']:
            if sublayerFile not in layer.subLayerPaths:
                layer.subLayerPaths.append( sublayerFile )
        layer.Save()

class Sublayer(SublayerBase):
    def __init__(self, path, **kwargs):
        SublayerBase.__init__(self, path, **kwargs)

        defaults = {}
        defaults['path'] = str(path)
        defaults['layer'] = ''
        defaults['version'] = 0
        defaults['frameRange'] = None
        defaults['filePerFrame'] = False
        self.SetDefaults(defaults, **kwargs)

        self.format = kwargs['format'].lower() if 'format' in kwargs.keys() else 'usd'

        self.SetPaths()

    def SetPaths(self):
        self.patterns['session'] = '{0}/{1}/{1}_v???.{2}'.format(self.GetRootPath(), self.GetName(), self.GetFormat())

        self.patterns['versions'] = '{0}/{1}/{1}_v???.*'.format(self.GetRootPath(), self.GetName())
        self.patterns['formats'] = '{0}/{1}/{1}_{2}.*'.format(self.GetRootPath(), self.GetName(), self.GetVersionAsString())

        self.patterns['range'] = '{0}/{1}/{1}_{2}/{1}_v???.*.{3}'.format( self.GetRootPath(), self.GetName(), self.GetVersionAsString(), self.GetFormat())
        self.patterns['children'] = '{0}/{1}/*.usd*'.format( self.GetRootPath(), self.GetName() )

        self.paths['main'] = '{0}/{1}.usda'.format(self.GetRootPath(), self.GetName())
        self.paths['session'] = '{0}/{1}/{1}_{2}.{3}'.format(self.GetRootPath(), self.GetName(), self.GetVersionAsString(), self.GetFormat() )
        self.paths['latest'] = '{0}/{1}/{1}_{2}.{3}'.format(self.GetRootPath(), self.GetName(), self.GetVersionAsString(-1), self.GetFormat() )
        self.paths['range'] = '{0}/{1}/{1}_{2}/{1}_{2}.{3}.{4}'.format( self.GetRootPath(), self.GetName(), self.GetVersionAsString(), '{}', self.GetFormat() )
        self.paths['thumbnail'] = '{0}/{1}/{1}_{2}.{3}.jpg'.format(self.GetRootPath(), self.GetName(), self.GetVersionAsString(), self.GetFormat() )

    def Create(self, session=None, mode=None):
        SublayerBase.Create(self, session, mode)

        # Parent Sublayer
        if self.GetPath().HasParent():
            parent = Sublayer( self.GetPath().GetParent() )
            layer = USD.CreateOrOpen( parent.GetFilePath() )
            relpath = './'+self.GetFilePath().GetRelative(-2).AsString()
            if relpath not in layer.subLayerPaths:
                layer.subLayerPaths.insert(0, relpath)
            layer.Save()

            # Parent Layer
            layer = USD.CreateOrOpen( self.GetLayer().GetFilePath() )
            layer.SetPermissionToEdit(True)
            relpath = './'+parent.GetFilePath().GetRelative(-2).AsString()
            if relpath not in layer.subLayerPaths:
                layer.subLayerPaths.insert(0, relpath)
            layer.Save()

    def GetRootPath(self):
        outpath = Path(self.GetLayer().GetRootPath())
        if not self.data['layer']:
            outpath+= Path('job')
        outpath+= self.GetPath().GetParent()
        return outpath.AsString()

    def GetChildren(self):
        if self.GetName() == '':
            return self.GetLayer().GetSublayers()

        files = Path.Glob(self.GetFilePattern('children'))
        children = []
        for file in files:

            layer = USD.OpenAsAnonymous( self.GetFilePath() )
            thispath = './{0}/{1}.usda'.format( self.GetName(), file.GetFileName() )
            if thispath in layer.subLayerPaths:
                children.append( file.GetFileName() )
        return children

class Asset(SublayerBase):
    def __init__(self, path, **kwargs):
        SublayerBase.__init__(self, path, **kwargs)

        defaults = {}
        defaults['path'] = str(path)
        defaults['layer'] = ''
        defaults['version'] = 0
        defaults['frameRange'] = None
        defaults['filePerFrame'] = False
        defaults['format'] = 'usd'
        self.SetDefaults(defaults, **kwargs)

        self.format = self.data['format']

        self.format = kwargs['format'].lower() if 'format' in kwargs.keys() else 'usd'

        self.SetPaths()

    def Exists(self):
        return self.GetFilePath().Exists()

    def SetPaths(self):
        self.patterns['session'] = '{0}/{1}/{1}_v???.*'.format(self.GetRootPath(), self.GetName())

        self.patterns['versions'] = '{0}/{1}/{1}_v???.*'.format(self.GetRootPath(), self.GetName())
        self.patterns['formats'] = '{0}/{1}/{1}_{2}.*'.format(self.GetRootPath(), self.GetName(), self.GetVersionAsString())
        self.patterns['range'] = '{0}/{1}/{1}_{2}/{1}_v???.*.{3}'.format( self.GetRootPath(), self.GetName(), self.GetVersionAsString(), self.GetFormat())
        self.patterns['children'] = '{0}/{1}/*.usda*'.format( self.GetRootPath(), self.GetName() )

        self.paths['main'] = '{0}/{1}.usda'.format(self.GetRootPath(), self.GetName())
        self.paths['session'] = '{0}/{1}/{1}_{2}.{3}'.format(self.GetRootPath(), self.GetName(), self.GetVersionAsString(), self.GetFormat() )
        self.paths['latest'] = '{0}/{1}/{1}_{2}.{3}'.format(self.GetRootPath(), self.GetName(), self.GetVersionAsString(-1), self.GetFormat() )
        self.paths['range'] = '{0}/{1}/{1}_{2}/{1}_{2}.{3}.{4}'.format( self.GetRootPath(), self.GetName(), self.GetVersionAsString(), '{}', self.GetFormat() )

        self.paths['thumbnail'] = '{0}/{1}.png'.format( self.GetRootPath(), self.GetName() )

    def Create(self, session=None, mode=None):
        SublayerBase.Create(self, session, mode)

        if self.GetPath().HasParent():
            parent = Asset( self.GetPath().GetParent() )
            layer = USD.CreateOrOpen( parent.GetFilePath() )
            relpath = './'+self.GetFilePath().GetRelative(-2).AsString()
            if relpath not in layer.subLayerPaths:
                layer.subLayerPaths.insert(0, relpath)
            layer.Save()

    def GetAssets(self):
        assets = []
        files = Path.Glob( self.GetJobPath() + 'assets/*.usda' )
        for file in files:
            assets.append( file.GetFileName() )
        return assets

    def GetChildren(self):
        if self.data['path'] == '':
            return self.GetAssets()

        if not self.GetFilePath().Exists():
            return []

        children = []
        layer = USD.OpenAsAnonymous( self.GetFilePath() )
        for sublayer in layer.subLayerPaths:
            sublayer = Path(sublayer)
            if not sublayer.HasVersion():
                children.append( sublayer.GetFileName() )
        return children

    def GetRootPath(self):
        outpath = self.GetJobPath() + 'assets'
        outpath+= self.GetPath().GetParent()
        return outpath
