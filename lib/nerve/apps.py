import sys
import nerve
import shutil, subprocess

APP_DIR = nerve.Path(__file__).GetParent(3) + 'apps'

class Base:
    def __init__(self):
        self.data = {}

    def GetAppPath(self):
        return nerve.Path(self.data['job']) + self.data['name']

    def GetJob(self):
        return nerve.Job( self.data['job'] )

    def GetCmd(self):
        return self.GetAppPath() + (self.data['name'] + '.cmd')

    def Create(self):
        job = self.GetJob()
        if not job.Exists():
            job.Create()

        if not self.GetAppPath().Exists():
            self.GetAppPath().Create()

        template = APP_DIR + self.data['name'] + 'template'
        if not template.Exists():
            return None

        if sys.version_info > (3,8):
            shutil.copytree( template.AsString(), self.GetAppPath().AsString(), dirs_exist_ok=True)
        else:
            for file in nerve.Path.Glob( template + '/*'):
                target = nerve.Path(file.Replace(template, self.GetAppPath()))
                if not target.Exists():
                    if target.IsFile():
                        shutil.copyfile(str(file), str(target) )
                    else:
                        shutil.copytree( str(file), str(target) )

        cmdfile = self.GetCmd()
        cmdfile.SetContent( self.LoadCmd() )
        cmdfile.Create()

    def Load(self):
        if not self.GetAppPath().Exists():
            self.Create()
        subprocess.Popen( [str(self.GetCmd())], stdout=subprocess.PIPE, stderr=subprocess.STDOUT  )
    

class houdini(Base):
    def __init__(self, jobpath):
        Base.__init__(self)
        self.data['job'] = nerve.Path(jobpath)
        self.data['name'] = 'houdini'
        

    def LoadCmd(self):
        txt = '@echo off\n'
        txt+= 'set JOB={}\n'.format(self.GetJob())
        txt+= 'set HOUDINI_VERSION=19.0.589\n'
        txt+= 'set HOUDINI_PACKAGE_DIR=%NERVE_LOCAL_PATH%/houdini/packages\n'
        txt+= 'start "" "C:/Program Files/Side Effects Software/Houdini %HOUDINI_VERSION%/bin/houdinifx.exe"\n'
        return txt

class maya(Base):
    def __init__(self, jobpath):
        Base.__init__(self)
        self.data['job'] = nerve.Path(jobpath)
        self.data['name'] = 'maya'

    def LoadCmd(self):
        txt = '@echo off\n'
        txt+= 'set JOB={}\n'.format(self.GetJob())
        txt+= 'set MAYA_PROJECT={}\n'.format(self.GetAppPath())
        txt+= 'set MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%NERVE_LOCAL_PATH%/apps\maya\n'
        txt+= 'start "" "C:/Program Files/Autodesk/Maya2022/bin/maya.exe" -command nerve\n'
        return txt
