import os, sys, errno
import json

class Node:
    def __init__(self, **kwargs):
        self.data = {}
        #self.data['dirty'] = True

        '''
        for require in ['name', 'type']:
            if require not in kwargs.keys():
                raise Exception('Node {} is required.'.format(require))
        '''
        for key,val in kwargs.items():
            self.data[key] = val

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return str(self)

class String:
    def __init__(self):
        pass
    @staticmethod
    def IllegalCharacters(str, characters='&<>{}[]~`'):
        for char in characters:
            if char in str:
                return True
        return False

    @staticmethod
    def isEnglish(s):
        try:
            s.encode(encoding='utf=8').decode('ascii')
        except:
            return False
        else:
            return True

    @staticmethod
    def versionAsString(version):
        return 'v{}'.format( str(version).zfill(3) )

    @staticmethod
    def versionAsInt(version):
        if version == '<next>':
            return 0
        return int(version[1:])

    @staticmethod
    def pprint(data):
        import pprint
        pp = pprint.PrettyPrinter()
        pp.pprint(data)

    @staticmethod
    def FileDialog(mode='dir'):
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        if mode == 'dir':
            path = filedialog.askdirectory(mustexist=False)
            root.destroy()
            return file_path

        if mode == 'file':
            file_path = filedialog.askopenfilename()
            root.destroy()
            return file_path

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

    # Static Methods #
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

    @staticmethod
    def GetThisFile():
        return Path( __file__ )

    @staticmethod
    def GetDrives():
        ''' https://stackoverflow.com/questions/4188326/in-python-how-do-i-check-if-a-drive-exists-w-o-throwing-an-error-for-removable '''
        import ctypes, itertools, string, platform

        if 'Windows' not in platform.system():
            return []
        drive_bitmask = ctypes.cdll.kernel32.GetLogicalDrives()
        return list(itertools.compress(string.ascii_uppercase, map(lambda x:ord(x) - ord('0'), bin(drive_bitmask)[:1:-1])))

    @staticmethod
    def Glob(pattern):
        from glob import glob
        if not isinstance(pattern, Path):
            pattern = Path(pattern)
        return [Path(item) for item in sorted(glob(pattern.AsString()))]

    def Replace(self, rep, repwith):
        return Path(self.AsString().replace(rep, repwith))

    # Magic Methods #
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

    # Is Methods #
    def IsAbsolute(self):
        if not len(self.segments):
            return False

        if not self.segments[0]:
            return True

        if len(self.segments[0]) > 1 and self.segments[0][1] == ':':
            return True

        return False

    def IsDir(self):
        return self.isDir

    def IsFile(self):
        return not self.isDir

    def IsValid(self):
        import errno
        segments = self.segments.copy()

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

        if not len(segments):
            return False
        try:
            for seg in segments:
                if not seg.isalnum():
                    return False
                if String.IllegalCharacters(seg):
                    return False
                if not String.isEnglish(seg):
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

    # Get Methods #
    def GetParent(self, offset=1):
        return Path(self.separator.join( self.segments[:-offset] ))

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

    def GetRoot(self):
        if self.IsAbsolute():
            return self.segments[1]
        else:
            return self.segments[0]

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

    def GetContent(self):
        if not self.content:
            return ''
        if isinstance(self.content, Path):
            return self.content.Read()
        return self.content

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

    # Has Methods #
    def HasParent(self):
        if len(self.segments) == 2 and self.IsAbsolute():
            return False
        return len(self.segments)>1

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

    # Set Methods #
    def SetContent(self, content):
        self.content = content

    def SetHead(self, head):
        self.segments[-1] = head
        return self

    # OS Methods #
    def Exists(self):
        return os.path.exists(self.AsString())

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

    # Other Methods #
    def AsString(self, separator=None):
        separator = separator if separator else self.separator
        return separator.join(self.segments)

class Config(dict):
    def Load(self):
        # Current Directorys
        cwd = Path(__file__)

        # Nerve Root Directory
        nrvpath = cwd.GetParent(3)
        # Load Config Files
        files = Path.Glob(nrvpath+'conf/*.json')
        for file in files:
            with open(str(file)) as json_file:
                data = json.load(json_file)
            self.update( data )

        self['path'] = nrvpath
        self['local'] = self.GetLocalData()
        return self

    def GetLocalData(self):
        datafile = Path('$APPDATA') + 'nerve' + 'nerve.json'
        if datafile.Exists():
            with open(datafile.AsString()) as json_file:
                data = json.load(json_file)
            return data

        return {}

    def SetLocalData(self, indata=None):
        if 'local' not in self.keys():
            self['local'] = {}

        datafile = Path('$APPDATA') + 'nerve' + 'nerve.json'

        if not datafile.Exists():
            datafile.SetContent('{}')
            datafile.Create()


        with open(datafile.AsString(), 'w') as outfile:
            json.dump( self['local'], outfile)

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

class Base:
    def __init__(self, **kwargs):
        for attr in ['data', 'paths', 'patterns']:
            if not hasattr(self, attr):
                setattr(self, attr, {})

        defaults = {}
        defaults['job'] = os.environ['JOB'] if 'JOB' in os.environ.keys() else Path(conf['JOB'])
        defaults['description'] = ''
        defaults['comment'] = ''
        self.SetDefaults(defaults, **kwargs)

    def SetDefaults(self, defaults, **kwargs):
        for key,val in defaults.items():
            self.data[key] = kwargs[key] if key in kwargs.keys() else val

    def GetFilePath(self, key='main'):
        if key == 'cover':
            return self.GetCover()

        if key not in self.paths.keys():
            raise Exception('Invalid path request:'+key)
        return Path(self.paths[key])

    def GetFilePattern(self, key):
        if key not in self.patterns.keys():
            raise Exception('Invalid pattern request: '+key)
        return Path(self.patterns[key])

    def GetPath(self):
        return Path(self.data['path'])

    def GetJobPath(self):
        return Path(self.data['job']) + Path( conf['DIR'] )

    def GetName(self):
        return self.GetPath().GetHead()

    def Exists(self):
        return self.GetFilePath().Exists()

    def GetCover(self):
        file = self.GetFilePath()
        ext = file.GetExtension()
        file = file.AsString().replace( '.'+ext, '.png' )
        return Path(file)

    def HasCover(self):
        return self.GetCover().Exists()

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

    def JsonEncode(self):
        data = self.data
        data['name'] = self.GetName()
        data['exists'] = self.Exists()
        data['hasCover'] = self.HasCover()
        data['cover'] = self.GetCover()
        data['file'] = self.GetFilePath().AsString()
        data['path'] = self.GetPath().AsString()

        return data

class Job(Base):
    def __init__(self, directory=None, **kwargs):
        Base.__init__(self, **kwargs)

        if not directory:
            directory = os.environ['JOB'] if 'JOB' in os.environ.keys() else Path(conf['JOB'])

        self.data['directory'] = Path(directory)
        self.data['job'] = Path(directory)

        defaults = {}
        defaults['fps'] = 25
        defaults['path'] = ''
        self.SetDefaults(defaults, **kwargs)

        self.paths['main'] = Path(directory) + conf['DIR'] + 'job.usda'

    def Create(self):
        from pxr import Usd, UsdGeom

        self.GetFilePath().GetParent().Create()

        layer = USD.CreateOrOpen( self.GetFilePath() )
        layer.Clear()
        stage = Usd.Stage.Open(layer)

        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
        layer.Save()

    def Delete(self):
        if self.data['directory'].Exists():
            self.data['directory'].Remove(recursive=True)

    @staticmethod
    def AddToRecent(path):
        key = 'recentJobs'
        if key in conf['local'].keys() and path not in conf['local'][key]:
            conf['local'][key].append( path )
        else:
            conf['local'][key] = [ path ]
        conf.SetLocalData()

    @staticmethod
    def GetRecent():
        key = 'recentJobs'

        if key in conf['local'].keys():
            update = False
            for recent in conf['local'][key]:
                # Remove Jobs that don't exist
                if not Job(recent).Exists():
                    conf['local'][key].remove(recent)
                    update = True
            if update:
                conf.SetLocalData()
        else:
            return []

        return conf['local'][key]

    @staticmethod
    def Get():
        return os.environ['JOB'] if 'JOB' in os.environ.keys() else nerve.conf['JOB']

    def GetDir(self):
        return self.data['directory'].AsString()

    def GetAssets(self):
        assets = []
        files = Path.Glob( self.GetJobPath() + 'assets/*.usda' )
        print(self.GetJobPath())

        for file in files:
            assets.append( file.GetFileName() )
        return assets

    def GetName(self):
        return Path(self.data['directory']).GetHead()

    def JsonEncode(self):
        data = Base.JsonEncode(self)
        data['path'] = self.data['directory']
        return data

    def GetChildren(self):
        return []

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

    def GetRootPath(self):
        jobpath = self.GetJobPath()
        if self.GetPath() == '':
            return jobpath
        return jobpath + 'job' + self.GetPath().GetParent()

    def GetName(self):
        if self.GetPath() == '':
            return Path('job')
        return self.GetPath().GetHead()

class SublayerBase(Base):
    def __init__(self, path='', **kwargs):
        Base.__init__(self, **kwargs)

        defaults = {}
        defaults['path'] = str(path)
        defaults['layer'] = ''
        defaults['version'] = 0
        defaults['frameRange'] = None
        defaults['filePerFrame'] = False
        defaults['format'] = 'usd'

        self.SetDefaults(defaults, **kwargs)

    def GetFormat(self):
        return self.data['format']

    def GetFormats(self):
        from pxr import Usd, Sdf

        if not self.GetFilePath().Exists():
            return []

        stage = Usd.Stage.Open( self.GetFilePath().AsString() )
        prim = self.GetPrim(stage)
        versionSet = prim.GetVariantSet('version')
        versionSet.SetVariantSelection( self.GetVersionAsString() )
        formatSet = prim.GetVariantSet('format')
        return formatSet.GetVariantNames()

    def GetLayer(self):
        return Layer(path=self.data['layer'])

    def GetJob(self):
        return Job(self.GetJobPath().GetParent())

    # Version #
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

    # Versions #
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

    def GetVersionsFromDisk(self):
        files = Path.Glob(self.GetFilePattern('versions'))
        versions = []
        for file in files:
            if file.GetVersion() not in versions:
                versions.append(file.GetVersion())
        return versions

    # modelAPI AssetInfo
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

    # Prim
    def GetPrimPath(self):
        name = self.GetName()
        return '/nerve/{}s/{}'.format(self.__class__.__name__, name)

    def GetPrim(self, stage=None):
        if not stage:
            stage = Usd.Open( self.GetFilePath().AsString() )
        primpath = self.GetPrimPath()
        prim = stage.GetPrimAtPath( primpath )
        if not prim:
            prim = stage.DefinePrim(primpath)
        return prim

    # Create
    def Create(self):
        from pxr import Usd, Sdf, Kind, UsdGeom, UsdShade
        from datetime import datetime
        import getpass

        if not self.GetPath():
            raise Exception('Empty Path. Skipping Export.')

        # Paths
        abspath = self.GetFilePath('session').AsString()
        relpath = './'+self.GetFilePath('session').GetRelative(-2).AsString()
        outpath = relpath

        # Main File
        layer = USD.CreateOrOpen( self.GetFilePath() )

        # Sublayer only if session is usd
        if self.GetFormat().lower() in ['usd', 'usda'] and Path(abspath).Exists():
            layer.subLayerPaths = [outpath]

        # Set Custom Layer Data
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
            data['comment'] = self.data['comment'] if 'comment' in self.data.keys() else ''
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
                if 'frameRange' in self.data.keys() and self.data['frameRange']:
                    data['frameRange'] = True
                    data['frameStart'] = self.data['frameRange'][0]
                    data['frameEnd'] = self.data['frameRange'][1]
                else:
                    data['frameRange'] = False

                modelAPI.SetAssetInfo(data)

        layer.Save()

        # Sublayer to shot
        if self.__class__.__name__ == 'Sublayer':
            layer = USD.FindOrOpen( self.GetLayer().GetFilePath() )
            sublayerFile = './'+self.GetFilePath().GetHead()
            if self.GetFormat().lower() in ['usd', 'usda']:
                if sublayerFile not in layer.subLayerPaths:
                    layer.subLayerPaths.append( sublayerFile )
            layer.Save()

class Asset(SublayerBase):
    def __init__(self, path='', **kwargs):
        SublayerBase.__init__(self, path, **kwargs)
        self.SetPaths()

    def SetPaths(self):
        # Patterns
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

    def GetRootPath(self):
        outpath = self.GetJobPath() + 'assets'
        outpath+= self.GetPath().GetParent()
        return outpath

    @staticmethod
    def GetChildrenByFilter(path, jobpath):
        path = path.replace('//', '/')
        children = []
        asset = Asset(job=jobpath)
        searchpath = asset.GetRootPath().AsString() + path + '*.usda'

        files = Path.Glob( searchpath )
        return [ f.GetFileName() for f in files ]

    def GetChildren(self):
        if self.data['path'] == '':
            return self.GetJob().GetAssets()

        if not self.GetFilePath().Exists():
            return []

        children = []
        layer = USD.OpenAsAnonymous(self.GetFilePath())
        for sublayer in layer.subLayerPaths:
            sublayer = Path(sublayer)
            if not sublayer.HasVersion():
                children.append( sublayer.GetFileName() )
        return children

    def Create(self):
        SublayerBase.Create(self)

        if self.GetPath().HasParent():
            parent = Asset( self.GetPath().GetParent() )

            if not parent.Exists():
                parent.Create()

            layer = USD.CreateOrOpen( parent.GetFilePath() )
            relpath = './'+self.GetFilePath().GetRelative(-2).AsString()
            if relpath not in layer.subLayerPaths:
                print(relpath)
                layer.subLayerPaths.insert(0, relpath)
            layer.Save()

    def JsonEncode(self, usd=False):
        data = SublayerBase.JsonEncode(self)

        data['format'] = self.GetFormat()
        data['children'] = self.GetChildren()
        data['hasChildren'] = len(data['children'])
        data['parent'] = self.GetPath().GetParent().AsString()
        data['hasParent'] = self.GetPath().HasParent()

        data['versions'] = [ (v, String.versionAsString(v)) for v in self.GetVersions(fromDisk=True) ]
        data['hasVersion'] = len(data['versions']) > 0
        data['version'] = self.GetVersion()
        data['versionAsString'] = self.GetVersionAsString()

        data['formats'] = []
        if usd:
            data['usd'] = self.GetAssetInfo()

        if False:
            print('### Asset ###')
            String.pprint(data)
            print('#############')
        return data

conf = Config().Load()
