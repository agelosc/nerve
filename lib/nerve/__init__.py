import os, sys
from re import L
import json, time, logging

class logger:
    def __init__(self, level=logging.DEBUG):
        self.log = logging.getLogger('')
        for h in self.log.handlers:
            self.log.removeHandler(h)
        
        self.log.setLevel(level)

        self.handler = logging.StreamHandler()
        self.format = logging.Formatter('%(levelname)s::%(message)s')
        self.handler.setFormatter(self.format)
        self.log.addHandler(self.handler)

    def namespace(self):
        return False

        import inspect
        frame = inspect.currentframe().f_back.f_back
        ns = []

        # Module
        ns.append(frame.f_globals['__name__'])
        
        # Class
        args, _, _, value_dict = inspect.getargvalues(frame)
        if len(args) and args[0] == 'self':
            instance = value_dict.get('self', None)
            if instance:
                ns.append(instance.__class__.__name__)
        
        func = frame.f_code.co_name
        if func != '<module>':
            ns.append(frame.f_code.co_name)

        self.log = logging.getLogger('.'.join(ns))

    def debug(self, msg, *args, **kwargs):
        self.namespace()
        return self.log.debug(msg, *args, **kwargs)
    def info(self, msg, *args, **kwargs):
        self.namespace()
        return self.log.info(msg, *args, **kwargs)
    def error(self, msg, *args, **kwargs):
        import inspect
        frame = inspect.currentframe().f_back
        info = inspect.getframeinfo(frame)

        self.namespace()
        return self.log.error(str(info.lineno)+'|'+msg, *args, **kwargs)
    def warning(self, msg, *args, **kwargs):
        self.namespace()
        return self.log.warning(msg, *args, **kwargs)
    def critical(self, msg, *args, **kwargs):
        self.namespace()
        return self.log.critical(msg, *args, **kwargs)

log = logger(logging.DEBUG)

class Image:
    def __init__(self, filename=None):
        self.data = {}
        self.data['file'] = Path(filename)
        
        dirs = Path.Glob('$PROGRAMFILES/ImageMagick-*')
        if not dirs:
            raise Exception('Image Magick not found in default paths.')

        self.data['bin'] = Path(dirs[-1])
        self.data['cmd'] = self.data['bin'] + 'magick.exe'
        self.data['display'] = self.data['bin'] + 'imgdisplay.exe'

    def cmd(self, *args):
        import subprocess
        args = list(args)
        args.insert(0, str(self.data['cmd']))
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr =  process.communicate()
        if stderr:
            print(stderr)

        return stdout

    def CleanTemp(self):
        files = Path.Glob('$TEMP/nerve/images/*')
        for file in files:
            file.Remove()

    def GetFile(self):
        if not self.data['file']:
            timestamp = str(time.time()).replace('.', '_')
            self.data['file'] = Path('$TEMP/nerve/images/{}.png'.format(timestamp))
            #self.CleanTemp()

        return self.data['file']

    def SetFile(self, filename=None):
        if filename is None:
            files = Path.Glob('$TEMP/nerve/images/*')
            if not len(files):
                raise Exception('No recent images found in temp folder.')

            self.data['file'] = files[-1]
            return True

        self.data['file'] = Path(filename)
    
    def GetExtension(self):
        return self.GetFile().GetExtension()

    def SaveClipboard(self, filename=None):
        if not filename:
            filename = self.GetFile()
        
        filename = Path(filename)
        if not filename.GetParent().Exists():
            filename.GetParent().Create()
        return self.cmd( 'clipboard:', str(filename) )

    def GetSize(self):
        if not self.GetFile().Exists():
            return False
        width  = self.cmd('identify', '-ping', '-format', '%w', str(self.GetFile()))
        height = self.cmd('identify', '-ping', '-format', '%h', str(self.GetFile()))
        return (int(width), int(height))

    def Square(self, filename=None):
        if not filename:
            filename = self.GetFile()

        size = self.GetSize()
        width = size[0]
        height = size[1]

        if width != height:
            if width < height:
                args = [
                    self.GetFile().AsString(),
                    '-crop',
                    '{0}x{1}+{2}+{3}'.format(width, width, 0, int((height-width)/2)),
                    '-resize',
                    '512x512!',
                    str(filename)
                ]
                self.cmd(*args)
            else:
                args = [
                    self.GetFile().AsString(),
                    '-crop',
                    '{0}x{1}+{2}+{3}'.format(height, height, int((width-height)/2), 0),
                    '-resize',
                    '512x512!',
                    str(filename)
                ]
                self.cmd(*args)
        else:
            args = [
                self.GetFile().AsString(),
                '-resize',
                '512x512!',
                str(filename)
            ]
            self.cmd(*args)
            
        self.SetFile(filename)

    def GetKays(self, size=None):
        if size is None:
            size = self.GetSize()

        if isinstance(size, int):
            minsize = size
        else:
            #minsize = size[0] if size[0]<size[1] else size[1]
            minsize = size[0] if size[0]>size[1] else size[1]

        if minsize <= 1000:
            return 1
        kays = int(round(minsize/1000))
        return kays

    def Scale(self, scale, filename=None):
        if not filename:
            filename = self.GetFile()
        size = self.GetSize()
        newsize = ( int(round(size[0]*scale)), int(round(size[1]*scale)) )
        newname = '{}.{}K.{}'.format( filename.GetName().split('.')[0], self.GetKays(newsize), filename.GetExtension() )
        newfile = filename.GetParent() + newname
        if newfile.Exists():
            self.SetFile(newfile)
            log.info(newfile + ' already exists. Skipping Scale.')
            return False

        args = [
            self.GetFile().AsString(),
            '-resize',
            '{}x{}!'.format( newsize[0], newsize[1] ),
            str(newfile),
        ]
        self.cmd(*args)
        self.SetFile(newfile)

    def Open(self):
        os.startfile(self.GetFile().AsString())

    def __str__(self):
        return self.GetFile().AsString()
    
    def __repr__(self):
        return str(self)

    def SaveAs(self, filename):
        args = [self.GetFile().AsString(), str(filename)]
        self.SetFile(filename)
        self.cmd(*args)

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
        if version == '<new>':
            return 0
        return int(version[1:])

    @staticmethod
    def pprint(data):
        import pprint
        pp = pprint.PrettyPrinter()
        pp.pprint(data)

    @staticmethod
    def FileDialog(mode='dir', title=None):
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1)

        if not title:
            title = 'Select '+mode

        root.title(title)

        if mode == 'dir':
            path = filedialog.askdirectory(mustexist=False, title=title)
            root.destroy()
            return path

        if mode == 'file':
            file_path = filedialog.askopenfilename(title=title)
            root.destroy()
            return file_path
        
        root.destroy()
        return False

    @staticmethod
    def GetParentPath(path):
        return Path(path).GetParent().AsString()

    @staticmethod
    def UnCamelCase(name, char=' '):
        import re
        result = re.sub('([A-Z]{1})', r'%s\1'%char, name)
        return result.title()

    @staticmethod
    def UnSnakeCase(name, char=' '):
        result = name.replace('_', char)
        return result.title()

    @staticmethod
    def Pretty(name):
        if len(name) <= 3:
            return name
        return String.UnSnakeCase( String.UnCamelCase(name) )

class Path:
    def __init__(self, path=None, separator='/'):
        self.separator = separator
        self.segments = []
        self.content = None
        self.isDir = True

        if path is None:
            return None

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
    def GetThisDir():
        return Path.GetThisFile().GetParent()


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

        return Path(self.AsString().replace(str(rep), str(repwith)))

    # Magic Methods #
    def __repr__(self):
        return self.AsString()

    def __add__(self, other):
        if not isinstance(other, Path):
            other = Path(other)

        if other.IsAbsolute():
            other = other.Trim()

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

    def __bool__(self):
        if not len(self.segments):
            return False
        if len(self.segments) == 1 and self.segments[0] == '':
            return False

        return True

    def __len__(self):
        if not len(self.segments):
            return 0
        if len(self.segments) == 1 and self.segments[0] == '':
            return 0

        return len(self.segments)

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

    def Trim(self):
        return self.GetRelative( len(self.segments)-1 )

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

    def SetExtension(self, ext):
        self.isDir = False
        self.segments[-1]+= '.{}'.format(ext)
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
        import shutil
        from shutil import copyfile

        dest = Path(dest)
        if dest.HasParent() and not dest.GetParent().Exists():
            os.makedirs( dest.GetParent().AsString() )
        
        shutil.copyfile(self.AsString(), dest.AsString())
        return str(dest)

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
        if 'jobs' in self['local'].keys():
            for job in self['local']['jobs']:
                if job not in self['jobs']:
                    self['jobs'].append(job)

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

class Format:
    formats = {}
    # Common
    formats['usd'] = 'USD'
    formats['usda'] = 'USDAscii'

    # Maya
    formats['abc'] = 'Alembic'
    formats['mb'] = 'MayaBinary'
    formats['ma'] = 'MayaAscii'
    formats['fbx'] = 'FBX'
    formats['obj'] = 'OBJ'
    formats['rs'] = 'RedshiftProxy'
    formats['tex'] = 'Texture'
    formats['hdr'] = 'HDRI'
    formats['mat'] = 'Material'

    def __init__(self, format):
        for key in self.formats.keys():
            if format.lower() == key:
                self.name = key
                self.long = self.formats[key]
                return None

        for key,val in self.formats.items():
            if format == val:
                self.name = key
                self.long = val
                return None

        raise Exception('Format '+format+'Not Found.')
        
    def GetLong(self):
        return self.long
    
    def SetLong(self, long):
        self.long = long

    def GetName(self):
        return self.name

    @classmethod
    def All(cls, long=False):
        if long:
            return [val for key,val in cls.formats.items()]

        return cls.formats.keys()

class Base:
    def __init__(self, **kwargs):
        self.data = {}

    def __eq__(self, other):
        return self.data == other.data

    def __str__(self):
        import pprint
        return pprint.pformat(self.data, indent=4)

    def __repr__(self):
        return str(self)

    def __bool__(self):
        return self.Exists()
    
    def LoadCustomLayerData(self):
        from pxr import Vt
        if not self.GetFilePath().Exists():
            return {}

        layer = USD.OpenAsAnonymous(self.GetFilePath())
        data = {}
        for key,val in layer.customLayerData.items():
            if isinstance( val, (Vt.DoubleArray, Vt.IntArray)):
                val = tuple(val)
            if isinstance( val, (Vt.StringArray)):
                val = list(val)
            data[key] = val

        return data
    
    def SetCustomLayerData(self, data):
        from pxr import Vt

        for key,val in data.items():
            if isinstance(val, dict):
                val = self.SetCustomLayerData(val)
            if isinstance(val, Path):
                val = str(val)
            if isinstance(val, (tuple, list)):
                if isinstance(val[0], int):
                    val = Vt.IntArray(val)
                if isinstance(val[0], float):
                    val = Vt.DoubleArray(val)
                if isinstance(val[0], str):
                    val = Vt.StringArray(val)
            data[key] = val
        return data

    def SaveCustomLayerData(self, data):
        from pxr import Vt
        layer = USD.FindOrOpen( self.GetFilePath() )
        data = self.SetCustomLayerData(data)
        layer.customLayerData = data
        layer.Save()

    def GetLayerData(self, key, default=''):
        data = self.LoadCustomLayerData()
        if key in data.keys():
            return data[key]
        return default

    def Exists(self):
        return self.GetFilePath().Exists()

    def GetName(self):
        return Path(self.data['path']).GetHead()
    
    def GetPrettyName(self):
        data = self.LoadCustomLayerData()
        if 'name' in data.keys():
            return data['name']

        return self.GetName()

    def SetPrettyName(self, name):
        data = self.LoadCustomLayerData()
        if name:
            data['name'] = name
        else:
            del data['name']
        self.SaveCustomLayerData(data)

    def GetPath(self):
        return self.data['path']

    def HasCover(self):
        return self.GetFilePath('cover').Exists()
    
    def SetCover(self, cover):
        cover = Path(cover)
        if not cover.Exists():
            log.error('cover image not found {}.'.format(cover))
            return False
        img = Image(cover)
        img.Square()

class Job(Base):
    def __init__(self, job=None, **kwargs):
        Base.__init__(self, **kwargs)
        
        if not job:
            job = Path(os.environ['JOB']) if 'JOB' in os.environ.keys() else Path(conf['JOB'])
        
        self.data['job'] = Path(job)
        self.data['path'] = self.data['job'].GetHead()

    def GetFilePath(self, key=None):
        if not key:
            return self.GetFilePath('root') + 'job.usda'
        if key == 'root':
            return self.data['job'] + conf['DIR']
        if key == 'job':
            return self.data['job']
        if key == 'cover':
            return self.GetFilePath('root') + 'job.png'

    def Create(self):
        from pxr import Usd, UsdGeom
        if self.Exists():
            self.AddToRecent(self.GetFilePath('job'))
            return True

        if not self.GetFilePath().GetParent().Exists():
            self.GetFilePath().GetParent().Create()

        for d in ['elements/input', 'elements/output', 'elements/2D', 'elements/3D']:
            folder = Path(self.GetFilePath('job')) + d
            if not folder.Exists():
                folder.Create()

        layer = USD.CreateOrOpen( self.GetFilePath() )
        layer.Clear()
        stage = Usd.Stage.Open(layer)
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
        layer.Save()

        self.AddToRecent( self.GetFilePath('job') )

    def Delete(self):
        if self.GetFilePath('job').Exists():
            self.GetFilePath('job').Remove(recursive=True)

    @staticmethod
    def AddToRecent(path):
        if isinstance(path, Path):
            path = path.AsString()

        key = 'jobs'
        if key in conf['local'].keys():
            if path not in conf['local'][key]:
                conf['local'][key].append( path )
        else:
            conf['local'][key] = [ path ]
        conf.SetLocalData()

    @staticmethod
    def RemoveFromRecents(path):
        path = Path(path)
        if 'jobs' not in conf.keys():
            return False

        if str(path) in conf['local']['jobs']:
            conf['local']['jobs'].remove(str(path))
            conf.SetLocalData()
            log.info('Job {} removed from recents'.format(path)),
            return True

        log.warning('Job {} not found in recents. Skipping...'.format(path)),
        return True

    @staticmethod
    def GetRecent():
        conf.Load()
        key = 'jobs'
        if 'jobs' not in conf.keys():
            return []
        
        return conf['jobs']

class Asset(Base):
    def __init__(self, path='', **kwargs):
        Base.__init__(self, **kwargs)

        self.data['path'] = Path(path)
        for key in kwargs.keys():
            self.data[key] = kwargs[key]

        # Defaults
        defaults = {}
        defaults['job'] = Path(os.environ['JOB']) if 'JOB' in os.environ.keys() else Path(conf['JOB'])
        for key,val in defaults.items():
            if key not in self.data.keys():
                self.data[key] = val

        self.release = []
        self.gather = []

    def GetFormatObject(self):
        import inspect
        
        formatLong = Format(self.GetFormat()).GetLong()
        module = inspect.getmodule(self)
        #module = sys.modules[__name__]
        if not hasattr( module, formatLong ):
            log.error('Module {} does not have a {} object class definition.'.format(__name__, formatLong))
            return False
        return getattr( module, formatLong)(**self.data)

    def Release(self, _name=None, **kwargs):
        self = self.GetFormatObject()

        if not self.release:
            log.error('Asset does not have release methods assigned.')
            return False

        if _name is None:
            return getattr(self, self.release[0])(**kwargs)

        if _name not in self.release:
            log.error('Asset does not have a [{}] release method assigned.'.format(_name))
            return False

        return getattr(self, _name)(**kwargs)

    def Gather(self, _name=None, **kwargs):
        self = self.GetFormatObject()

        if not self.gather:
            log.error('Asset does not have gather methods assigned')
        
        if _name is None:
            return getattr(self, self.gather[0])(**kwargs)

        if _name not in self.gather:
            log.error('Asset does not have a [{}] gahter method assigned'.format(_name))
            return False
        
        return getattr(self, _name)(**kwargs)

    def Create(self):
        from datetime import datetime
        import getpass

        # Create Parent Path
        if not self.GetFilePath().GetParent().Exists():
            self.GetFilePath().GetParent().Create()

        # Load Layer
        layer = USD.CreateOrOpen(self.GetFilePath())

        # Set Sublayer
        abspath = self.GetFilePath('session').AsString()
        relpath = './'+self.GetFilePath('session').GetRelative(-1).AsString()
        if self.GetFormat().lower() in ['usd', 'usda'] and self.GetFilePath('session').Exists():
            layer.subLayerPaths = [relpath]

        # Asset Data
        data = self.LoadCustomLayerData()
        for key in ['job', 'path', 'description', 'version', 'format', 'name']:
            if key in self.data.keys():
                data[key] = self.data[key]

        # Format Data
        fdata = {}
        for key in ['comment', 'frameRange']:
            if key in self.data.keys():
                fdata[key] = self.data[key]
        fdata['date'] = datetime.now().strftime('%a %d-%b-%y %H:%M:%S')
        fdata['user'] = getpass.getuser()

        # Append Version/Format
        if 'versions' not in data.keys():
            data['versions'] = {}
        vstr = self.GetVersionAsString()
        if vstr not in data['versions'].keys():
            data['versions'][vstr] = {}
        frm = self.GetFormat()
        data['versions'][vstr][frm] = fdata

        self.SaveCustomLayerData(data)
        layer.Save()

        # Parent
        if self.data['path'].HasParent():
            parent = self.GetParentAsset()
            parent.CreateGroup( self.data['path'].GetHead() )

    def CreateGroup(self, child):
        layer = USD.CreateOrOpen(self.GetFilePath())

        data = self.LoadCustomLayerData()
        for key in ['job', 'path']:
            if key in self.data.keys():
                data[key] = self.data[key]

        if 'children' not in data.keys():
            data['children'] = []
        if child not in data['children']:
            data['children'].append( str(child) )

        self.SaveCustomLayerData(data)
        layer.Save()

        if self.data['path'].HasParent():
            parent = self.GetParentAsset()
            parent.CreateGroup(self.data['path'].GetHead())

    def AddReleaseMethod(self, *args):
        for arg in args:
            if arg not in self.release:
                self.release.append(arg)

    def AddGatherMethod(self, *args):
        for arg in args:
            if arg not in self.gather:
                self.gather.append(arg)        

    def GetVersions(self, asString=False):
        if not self.GetFilePath().Exists():
            return []

        data = self.LoadCustomLayerData()
        if 'versions' not in data.keys():
            return []

        versions = [ String.versionAsInt(key) for key in data['versions'].keys() ]
        versions.sort()
        if asString:
            return [String.versionAsString(v) for v in versions]
        return versions

    def GetVersion(self):
        # Set and Get Next Version if not set
        if 'version' not in self.data.keys() or int(self.data['version']) == 0:
            versions = self.GetVersions()
            if not len(versions):
                self.data['version'] = 1
                return self.data['version']

            self.data['version'] = versions[-1]+1
            return self.data['version']

        if 'version' in self.data.keys() and self.data['version'] == -1:
            versions = self.GetVersions()
            if not versions:
                self.data['version'] = 0
                return self.GetVersion()
                
            return versions[-1]

        return self.data['version']

    def SetVersion(self, version):
        if isinstance(version, str) and version[0] == 'v':
            version = String.versionAsInt(version)
        self.data['version'] = int(version)
        return self
    
    def GetVersionAsString(self):
        return String.versionAsString( self.GetVersion() )

    def GetExtension(self):
        if 'ext' in self.data.keys():
            return self.data['ext']
        return self.GetFormat()
    
    def SetExtension(self, ext):
        self.data['ext'] = ext
        return self

    def GetFormat(self):
        if 'format' in self.data.keys():
            return self.data['format']
        
        self.data['format'] = 'usd'
        return self.data['format']
    
    def SetFormat(self, format):
        self.data['format'] = format
        return self

    def GetFormats(self):
        data = self.LoadCustomLayerData()
        if 'versions' not in data.keys():
            return []
        vstr = self.GetVersionAsString()
        if vstr not in data['versions'].keys():
            return []

        return list(data['versions'][vstr].keys())

    def GetFormatData(self):
        data = self.LoadCustomLayerData()
        if 'versions' not in data.keys():
            return {}
        vstr = self.GetVersionAsString()
        if vstr not in data['versions'].keys():
            return {}
        frm = self.GetFormat()
        if frm not in data['versions'][vstr].keys():
            return {}
        return data['versions'][vstr][frm]

    def HasFrameRange(self):
        data = self.GetFormatData()
        return 'frameRange' in data.keys()

    def GetFrameRange(self):
        data = self.GetFormatData()
        return data['frameRange']

    def GetChildrenOLD(self):
        if not self.data['path']:
            files = Path.Glob( self.GetFilePath('root') + '/*.usda')
            return [f.GetName() for f in files]

        data = self.LoadCustomLayerData()
        if 'children' not in data.keys():
            return []
        data['children'].sort()
        return data['children']

    def GetChildren(self):
        path = '/'
        if self.data['path']:
            path+= str(self.data['path'])
        pattern = self.GetFilePath('root') +  Path(path).GetHead() + '/*.usda'
        files = Path.Glob(pattern)
        return [f.GetName() for f in files]

    def HasChildren(self):
        return bool(self.GetChildren())

    def GetFilePath(self, key=None):
        name = self.data['path'].GetHead()
        if key is None:
            if not self.data['path']:
                name = 'default'
            return self.GetFilePath('root') + (name+'.usda')

        if key == 'job':
            return Path(self.data['job'])

        if key == 'root':
            path = self.GetFilePath('job') + conf['DIR'] + 'assets'
            path+= self.data['path'].GetParent()
            return Path(path)

        if key == 'session':
            pathlist = [self.GetFilePath('root'), name, self.GetVersionAsString(), self.GetExtension()]
            return Path('{0}/{1}/{1}_{2}.{3}'.format(*pathlist))

        if key == 'range':
            pathlist = [self.GetFilePath('root'), name, self.GetVersionAsString(), self.GetExtension()]
            return Path('{0}/{1}/{1}_{2}/{1}_{2}.{{}}.{3}'.format(*pathlist))

        if key == 'cover':
            return self.GetFilePath('root') + (name + '.png')

    def GetParentAsset(self):
        data = {}
        data['path'] = Path(self.data['path']).GetParent()
        data['job'] = self.data['job']
        inst = self.__class__
        return inst(**data)

    def GetChildAsset(self, child):
        data = {}
        data['path'] = Path(self.data['path']) + child
        data['job'] = self.data['job']
        return type(self)(**data)
    
    def GetChildAssets(self):
        assets = []
        for child in self.GetChildren():
            assets.append( self.GetChildAsset(child) )
        return assets

class USD(Asset):
    def __init__(self, path, **kwargs):
        Asset.__init__(self, path, **kwargs)

        self.AddReleaseMethod('Export')
    
    def Export(self):
        filepath = self.GetFilePath('session')
        layer = USD.CreateOrOpen(filepath)
        layer.Save()
        self.Create()

    @classmethod
    def CreateOrOpenOLD(cls, path):
        from pxr import Usd, Sdf, Kind, UsdGeom, UsdShade
        import time

        if not isinstance(path, Path):
            path = Path(path)
        if not path.GetParent().Exists():
            path.GetParent().Create()

        layer = Sdf.Layer.FindOrOpen(path.AsString())
        if not layer:
            for i in range(4):
                if not path.Exists():
                    try:
                        layer = Sdf.Layer.CreateNew(path.AsString())
                    except:
                        pass
                    time.sleep(1)

        if not layer:
            raise Exception('Could not create file '+path.AsString())

        return layer

    @classmethod
    def CreateOrOpen(cls, path):
        from pxr import Usd, Sdf, Kind, UsdGeom, UsdShade
        import time

        if not isinstance(path, Path):
            path = Path(path)
        if not path.GetParent().Exists():
            path.GetParent().Create()

        layer = Sdf.Layer.FindOrOpen(path.AsString())
        if not layer:
            tpath = Path('$TEMP/nerve') + path.GetHead()
            layer = Sdf.Layer.CreateNew(tpath.AsString())
            tpath.Copy(path)
            layer = Sdf.Layer.FindOrOpen(path.AsString())
            #layer = Sdf.Layer.CreateNew( path.AsString() )

        if not layer:
            raise Exception('Could not create file '+path.AsString())

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

class USDAscii(Asset):
    def __init__(self, path, **kwargs):
        Asset.__init__(self, path, **kwargs)

        self.SetExtension('usda')
        self.AddReleaseMethod('Export')
    
    def Export(self):
        filepath = self.GetFilePath('session')
        layer = USD.CreateOrOpen(filepath)
        layer.Save()
        self.Create()

conf = Config().Load()

class HDRI(Asset):
    def __init__(self, path='', **kwargs):
        kwargs['format'] = 'hdr'
        Asset.__init__(self, path, **kwargs)
        self.AddReleaseMethod('Export')

    def GetKays(self):
        img = Image(self.GetFilePath('session'))
        return img.GetKays()

    def SetCover(self):
        log.info('Creating HDRI Cover for {}, this might take a while.'.format(self.GetPath()))
        filepath = self.GetFilePath('session')
        img = Image(filepath)
        size = img.GetSize()
        width = size[0]
        height = size[1]

        if width != height:
            if width < height:
                args = [
                    filepath.AsString(),
                    '-crop',
                    '{0}x{1}+{2}+{3}'.format(width, width, 0, int((height-width)/2)),
                    '-resize',
                    '512x512!',
                    str(self.GetFilePath('cover'))
                ]
                img.cmd(*args)
            else:
                args = [
                    filepath.AsString(),
                    '-crop',
                    '{0}x{1}+{2}+{3}'.format(height, height, int((width-height)/2), 0),
                    '-resize',
                    '512x512!',
                    str(self.GetFilePath('cover'))
                ]
                img.cmd(*args)
        else:
            args = [
                filepath.AsString(),
                '-resize',
                '512x512!',
                str(self.GetFilePath('cover'))
            ]
            img.cmd(*args)

    def SetCoverOLD(self):
        filepath = self.GetFilePath('session')
        if not filepath.Exists():
            log.error('HDRI file does not exist. Cannot set cover: {}'.format( filepath )  )
            return False

        cover = Image(filepath)
        size = cover.GetSize()
        width = size[0]
        height = size[1]

        args = [
            filepath.AsString(),
            #'-auto-level',
            #'-auto-gamma',
            '-crop',
            '{}x{}+{}+{}'.format( width, height, int((width-height))/2, 0),
            '-resize',
            '512x512',
            #'-background',
            #'black',
            #'-gravity',
            #'center',
            #'-extent',
            #'512x512',            
            str(self.GetCover())
        ]
        log.info('Creating HDRI Cover. This might take a while.')
        cover.cmd(*args)
        cover.SetFile(self.GetCover())
        return True

    def Export(self, filepath):
        import shutil

        if not isinstance(filepath, Path):
            filepath = Path(filepath)

        if not filepath.Exists():
            raise Exception('error reading file {}'.format(filepath))

        # Create Parent
        if not self.GetFilePath('session').GetParent().Exists():
            self.GetFilePath('session').GetParent().Create()
        
        self.SetExtension( filepath.GetExtension() )
        filepath.Copy( self.GetFilePath('session') )
        self.Create()

        # Cover
        self.SetCover()

class Texture(Asset):
    def __init__(self, path='', **kwargs):
        kwargs['format'] = 'tex'
        Asset.__init__(self, path, **kwargs)

        self.AddReleaseMethod('Copy')
        self.AddGatherMethod('View')
    
    def Copy(self, **kwargs):
        if 'filepath' not in kwargs.keys():
            log.error('Filepath not set')
            return False
        
        filepath = kwargs['filepath']
        if not isinstance(filepath, Path):
            filepath = Path(filepath)

        if not filepath.Exists():
            log.error('Texture file does not exist')
            return False

        self.SetExtension( filepath.GetExtension() )
        filepath.Copy(self.GetFilePath('session'))
        self.Create()

        cover = Image(self.GetFilePath('session'))
        cover.Square( self.GetCover() )
        return True

class Material(Asset):
    def __init__(self, path='', **kwargs):
        kwargs['format'] = 'mat'
        Asset.__init__(self, path, **kwargs)
        self.SetExtension('json')
        self.matdata = {}

    def GetFilePath(self, key=None):
        if key == 'textures':
            return Asset.GetFilePath(self, 'root') + self.GetName() + 'textures'
        return Asset.GetFilePath(self, key)

    def MinMatdata(self):
        abstract = self.abstract()
        for material in self.matdata.keys():
            for grp in self.matdata[material]['abstract'].keys():
                for attr, value in self.matdata[material]['abstract'][grp].items():
                    if isinstance(value, dict):
                        continue
                    if value != abstract[grp][attr]:
                        continue
                    del(self.matdata[material]['abstract'][grp][attr])
            
            for grp in self.matdata[material]['abstract'].keys():
                if not self.matdata[material]['abstract'][grp]:
                    del(self.matdata[material]['abstract'][grp])

    def SetMaterial(self, name=None):
        if not name:
            name = self.GetName()
        if name not in self.matdata.keys():
            self.matdata[name] = { 'abstract': self.abstract() }

    def Set(self, value, grp, attr, material=None, **kwargs):
        if not material:
            material = self.GetName()
        if not self.matdata or material not in self.matdata.keys():
            self.SetMaterial(material)

        self.matdata[material]['abstract'][grp][attr] = value
        for key,val in kwargs.items():
            # Set other grp value
            if key in self.matdata[material]['abstract'][grp].keys():
                self.matdata[material]['abstract'][grp][key] = val
            # set other texture value
            if key in self.matdata[material]['abstract'][grp][attr].keys():
                self.matdata[material]['abstract'][grp][attr][key] = val            

    def SetTexture(self, filepath, grp, attr, material=None, **kwargs ):
        if not material:
            material = self.GetName()
        if not self.matdata or material not in self.matdata.keys():
            self.SetMaterial(material)

        filepath = Path(filepath)
        texdata = self.texture()
        texdata['name'] = filepath.GetName()
        texdata['filepath'] = filepath.AsString()
        if grp in ['bump', 'displacement']:
            texdata['colorSpace'] = 'Raw'
        if attr in ['roughness']:
            texdata['colorSpace'] = 'Raw'

        self.matdata[material]['abstract'][grp][attr] = texdata
        for key,val in kwargs.items():
            # Set other grp value
            if key in self.matdata[material]['abstract'][grp].keys():
                self.matdata[material]['abstract'][grp][key] = val
            # set other texture value
            if key in self.matdata[material]['abstract'][grp][attr].keys():
                self.matdata[material]['abstract'][grp][attr][key] = val

    def GetTypes(self, prefix):
        types = []
        for m in dir(self):
            if callable(getattr(self, m)) and m.startswith(prefix+'_'):
                types.append( m.replace(prefix+'_', '') )
        return types

    def GetTable(self, ttype, prefix):
        if ttype not in self.GetTypes(prefix):
            raise Exception('Table not found: '+ttype)
        return getattr(self, prefix+'_'+ttype)()

    def GetMaterialTypes(self):
        return self.GetTypes('mat')
    
    def GetMaterialTable(self, mattype):
        return self.GetTable(mattype, 'mat')

    @staticmethod
    def abstract():
        return {
        'diffuse': {
            'color': (1.0, 1.0, 1.0),
            'weight': 0.8,
            'roughness': 0.0
            },
        'translucency':{
            'color':(0.5, 0.5, 0.5),
            'weight': 0.0,
            },
        'reflection': {
            'color': (1.0, 1.0, 1.0),
            'weight': 1.0,
            'roughness': 0.22,
            'anisotropy': 0.0,
            'rotation': 0.0,
            'metalness': 0.0,
            'reflectivity': (0.04, 0.04, 0.04),
            'ior': 1.5,
            'type': 0, # types: 0=IOR, 1=metalness
            },
        'refraction': {
            'color': (1.0, 1.0, 1.0),
            'weight': 0.0,
            'roughness': 0.0,
            'ior': 1.5,
            'dispersion': 0.0,
            'thinWalled': False,
            'transmittance': (1.0, 1.0, 1.0),
            'absorption': 1.0,
            'extinction': (0.0, 0.0, 0.0),
            'extinctionScale': 1.0
            },
        'sheen': {
            'color': (1.0, 1.0, 1.0),
            'weight': 0.0,
            'roughness': 0.3,
            },
        'coat': {
            'color': (1.0, 1.0, 1.0),
            'weight': 0.0,
            'roughness': 0.01,
            'ior': 1.4
            },
        'sss': {
            'weight': 0.0,
            'radius': 1.0,
            
            'colorSingle': (1.0, 1.0, 1.0),
            'weightSingle': 0.0,
            'phaseSingle': 0.0,
            'radiusSingle': 1.0,
            # Skin
            'colorShallow': (1.0, 0.9, 0.7),
            'weightShallow': 0.6,
            'radiusShallow': 0.038,
            'colorMid': (0.95, 0.7, 0.5),
            'weightMid': 0.25,
            'radiusMid': 0.063,
            'colorDeep': (0.7, 0.1, 0.1),
            'weightDeep': 1.0,
            'radiusDeep': 0.15,
            },
        'emission': {
            'color': (0.0, 0.0, 0.0),
            'weight': 0.0,
            },
        'opacity': {
            'color': (1.0, 1.0, 1.0),
            'transparency': (0.0, 0.0, 0.0),
            },
        'bump': {
            'map': None,
            'height': 0.01,
            'type': 0, # 0: Bump, 1: Tangent Space Normal, 2: Object Space Normal
            },

        'displacement': {
            'map': None,
            'scale': 1.0,
        },
    }

    @staticmethod
    def texture():
        return {
            'name':'',
            'filepath':'',
            'alphaIsLuminance':False,
            'colorSpace':'sRGB',
            'outColor': True,
            'uvScale':(1.0, 1.0),
            'uvOffset': (0.0,0.0),
            'uvRotate': 0.0,
        }

        return {
            'saturation':1.0,
            'contrast': 1.0,
            'hue':0.0,
            'gamma': 1.0,
            'gain': 1.0,
            'offset': 0.0,
            'invert':False,
            'range': (0,1,0,1) # inmin, inmax, outmin, outmax
        }