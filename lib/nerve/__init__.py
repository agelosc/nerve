import os, sys, errno
import json

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
        return os.path.isabs(self.AsString())

        #if self.segments[0][1] == ':':
            #return True
        #return not self.segments[0]

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
        return self

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
        self.SetDefaults(defaults, **kwargs)

    def SetDefaults(self, defaults, **kwargs):
        for key,val in defaults.items():
            self.data[key] = kwargs[key] if key in kwargs.keys() else val

    def GetFilePath(self, key='main'):
        if key not in self.paths.keys():
            raise Exception('Invalid path request:'+key)
        return Path(self.paths[key])

    def GetFilePattern(self, key):
        if key not in self.patterns.keys():
            raise Exception('Invalid pattern request: '+key)
        return Path(self.patterns[key])

    def GetPath(self):
        return Path(self.data['path'])

    def GetRootPath(self):
        return Path(self.data['job']) + Path( conf['DIR'] )

    def GetName(self):
        return self.GetPath().GetHead()

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

class SublayerBase(Base):
    def __init__(self, path, **kwargs):
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
        if self.GetFormat().lower() in ['usd', 'usda']:
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

class Asset(SublayerBase):
    def __init__(self, path, **kwargs):
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
        outpath = SublayerBase.GetRootPath(self) + 'assets'
        outpath+= self.GetPath().GetParent()
        return outpath

conf = Config().Load()
