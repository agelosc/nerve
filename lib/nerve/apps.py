import nerve
import shutil, subprocess
from pathlib import Path
APP_DIR = nerve.Path(__file__).GetParent(3) + 'apps'

class Base:
    def __init__(self):
        #
        self.data['appath'] = self.data['path'] + self.data['name']
        self.data['cmdpath'] = self.data['appath'] + (self.data['name'] + '.cmd')
        self.data['cmdpath'].SetContent( self.LoadCmd() )

    def Create(self):
        job = nerve.Job(self.data['path'])
        if not job.Exists():
            job.Create()

        if not self.data['appath'].Exists():
            self.data['appath'].Create()

            template = APP_DIR + self.data['name'] + 'template'
            if template.Exists():
                shutil.copytree( template.AsString(), self.data['appath'].AsString(), dirs_exist_ok=True )

            self.data['cmdpath'].Create()

    def Load(self):
        if not self.data['appath'].Exists():
            self.Create()
        subprocess.Popen( [self.data['cmdpath'].AsString()], stdout=subprocess.PIPE, stderr=subprocess.STDOUT  )

class houdini(Base):
    def __init__(self, path):
        self.data = {}
        self.data['path'] = nerve.Path(path)
        self.data['name'] = 'houdini'
        Base.__init__(self)

    def LoadCmd(self):
        txt = '@echo off\n'
        txt+= 'set JOB={}\n'.format(self.data['path'])
        txt+= 'set HOUDINI_VERSION=19.0.383\n'
        txt+= 'set HOUDINI_PACKAGE_DIR={}/houdini/packages\n'.format(APP_DIR)
        txt+= 'start "" "C:/Program Files/Side Effects Software/Houdini %HOUDINI_VERSION%/bin/houdinifx.exe"\n'
        return txt

class maya(Base):
    def __init__(self, path):
        self.data = {}
        self.data['path'] = nerve.Path(path)
        self.data['name'] = 'maya'
        Base.__init__(self)

    def LoadCmd(self):
        txt = '@echo off\n'
        txt+= 'set JOB={}\n'.format(self.data['path'])
        txt+= 'set MAYA_PROJECT={}\n'.format(self.data['appath'])
        txt+= 'set MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;{}/maya\n'.format(APP_DIR)
        txt+= 'start "" "C:/Program Files/Autodesk/Maya2022/bin/maya.exe" -command nerve\n'
        return txt
