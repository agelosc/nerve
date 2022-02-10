import os, sys, json
import logging
from functools import partial

import nerve

import maya.cmds as cmds
import maya.mel as mel
import maya.utils as mu

class Path(nerve.Path):
    def __init__(self, path):
        nerve.Path.__init__(self, path, '|')

    def ClearNamespaces(self):
        path = Path('|'.join(self.segments))
        for i in range(len(path.segments)):
            path.segments[i] = path.segments[i].split(':')[-1]
        return path

def menu():
    print("NERVE::Initialising...")
    mu.executeDeferred('gNerve = nerve.maya.deferred();')

def deferred():
    #Menu
    gMainWindow = mel.eval('global string $gMainWindow; $temp1=$gMainWindow;')
    if gMainWindow != '':
        print("NERVE 6::Loading UI...")
        import UI
        UI.Menu()
    
    # Set Job
    workspace = nerve.Path(cmds.workspace(q=True, o=True))
    dir = workspace.GetParent()
    job = Job(dir)
    if job.Exists():
        job.Set(dir)

def asset(**kwargs):
    if 'format' not in kwargs.keys():
        raise Exception('format not specified.')
    
    format = nerve.Format(kwargs['format']).GetLong()
    if not hasattr(sys.modules[__name__], format):
        raise Exception('Invalid Format {}'.format(format))

    return getattr(sys.modules[__name__], format)(**kwargs)

class Job(nerve.Job):

    @staticmethod
    def Set(path):
        job = nerve.Job(path)
        if not job.Exists():
            print('Invalid job path: {}'.format(path)),
            return False

        proj = nerve.Path( job.GetDir() ) + 'maya'
        if not proj.Exists():
            print('Maya project not found {}.'.format(proj)),
            return False

        os.environ['JOB'] = job.GetDir()
        cmds.workspace(proj.AsString(), openWorkspace=True)
        print('Project set to {}.'.format(proj)),
        return True

    def Create(self, addToRecents=True):
        # Create Job
        nerve.Job.Create(self)
        # Add To Recent Jobs
        if addToRecents:
            self.AddToRecent(self.GetDir())
        # Create app directories
        app = nerve.apps.maya( self.GetDir() )
        app.Create()

        return True

class Base:
    def GetOptionsString(self):
        options = ''
        for key,val in self.data.items():
            if val is False:
                continue
            if val is True:
                options+= ' -'+key
                continue
            options+= ' -{} {}'.format(key, val)
        return options    

    def _ReleaseUI(self, anim=True):
        title = nerve.Format( self.GetFormat() ).GetLong()
        result = cmds.layoutDialog(ui=partial(self._releaseUI, anim), title=title )
        if result == 'Cancel' or result == 'dismiss':
            return False

        #nerve.String.pprint(self.data)
        self.Release()

    def _GatherUI(self):
        title = nerve.Format( self.GetFormat() ).GetLong()

        result = cmds.layoutDialog(ui=partial(self._gatherUI), title=title)
        if result == 'Cancel' or result == 'dismiss':
            return False

        #nerve.String.pprint(self.data)
        self.Gather()

    def _releaseUI(self, anim=True):
        def refresh(*args):
            data = args[0]
            if not data['anim']:
                return True
            idx = cmds.optionMenuGrp(data['menu'], q=True, select=True)
            items = cmds.optionMenuGrp(data['menu'], q=True, itemListLong=True)

            label = cmds.menuItem(items[idx-1], q=True, label=True)
            if label == 'Current Frame':
                currentTime = int(cmds.currentTime(q=True))
                cmds.intFieldGrp(data['frameRange'], e=True, v1=currentTime, v2=currentTime, enable=False)
            if label == 'Custom Frame Range':
                cmds.intFieldGrp(data['frameRange'], e=True, enable=True)
            if label == 'Current Frame Range':
                min = cmds.playbackOptions(q=True, min=True)
                max = cmds.playbackOptions(q=True, max=True)
                cmds.intFieldGrp(data['frameRange'], e=True, v1=int(min), v2=int(max), enable=False)

        def DoIt(*args):

            if data['anim']:
                idx = cmds.optionMenuGrp(data['menu'], q=True, select=True)
                items = cmds.optionMenuGrp(data['menu'], q=True, itemListLong=True)
                label = cmds.menuItem(items[idx-1], q=True, label=True)

                if label == 'Current Frame':
                    if 'frameRange' in self.data.keys():
                        del(self.data['frameRange'])
                if label == 'Custom Frame Range' or label == 'Current Frame Range':
                    min = cmds.intFieldGrp(data['frameRange'], q=True, v1=True)
                    max = cmds.intFieldGrp(data['frameRange'], q=True, v2=True)
                    self.data['frameRange'] = (min, max)

            return cmds.layoutDialog(dismiss='OK')

        def Cancel(*args):
            return cmds.layoutDialog(dismiss='Cancel')

        animmodes = ['Current Frame', 'Custom Frame Range', 'Current Frame Range']
        data = {}
        data['anim'] = anim
        cmds.columnLayout()
        if anim:
            cmds.frameLayout(label='Animation', marginHeight=10, marginWidth=10, font="boldLabelFont", width=400-2)
            if True:
                cmds.columnLayout()
                if True:
                    data['menu'] = cmds.optionMenuGrp(label='Animation')
                    for animode in animmodes:
                        cmds.menuItem(label=animode)
                    data['frameRange'] = cmds.intFieldGrp(label='Frame Range', numberOfFields=2)
                cmds.setParent('..')
            cmds.setParent('..')
            cmds.optionMenuGrp(data['menu'], e=True, changeCommand=partial(refresh, data))

        cmds.frameLayout(labelVisible=False, marginHeight=10, marginWidth=10, font="boldLabelFont", width=400-2)
        if True:
            cmds.rowLayout(numberOfColumns=3)
            if True:
                bwidth = 182
                cmds.button(label="OK", width=bwidth, height=50, command=partial(DoIt, data))
                cmds.text(label='', width=10)
                cmds.button(label="Cancel", width=bwidth, height=50, command=Cancel)
            cmds.setParent('..')
        cmds.setParent('..')

        cmds.setParent('..')
        refresh((data))

    def _gatherUI(self):
        def DoIt(*args):
            buttons = cmds.radioCollection(args[0]['mode'], q=True, collectionItemArray=True)
            for button in buttons:
                if cmds.radioButton(button, q=True, select=True):
                    self.data['mode'] = cmds.radioButton(button, q=True, label=True)
                    self.data['gatherMethod'] = self.data['mode']
                    cmds.layoutDialog(dismiss='OK')
                    return True


            cmds.layoutDialog(dismiss='OK')

        def Cancel(*args):
            return cmds.layoutDialog(dismiss='Cancel')

        data = {}
        cmds.columnLayout()
        if True:
            cmds.frameLayout(label='Options', marginHeight=10, marginWidth=10, font="boldLabelFont", width=400-2)
            if True:
                cmds.rowColumnLayout(numberOfRows=1, columnOffset=[1, 'right', 40])
                if True:
                    cmds.text(label='Method')
                    data['mode'] = cmds.radioCollection()
                    buttons = []
                    for mode in self.gather:
                        buttons.append(cmds.radioButton(label=mode.capitalize()))
                    cmds.radioCollection(data['mode'], e=True, select=buttons[0])

                cmds.setParent('..')
            cmds.setParent('..')
            cmds.frameLayout(labelVisible=False, marginHeight=10, marginWidth=10, font="boldLabelFont", width=400-2)
            if True:
                cmds.rowColumnLayout(numberOfRows=1)
                if True:
                    bwidth = 182
                    cmds.button(label="OK", width=bwidth, height=50, command=partial(DoIt, data))
                    cmds.text(label='', width=10)
                    cmds.button(label="Cancel", width=bwidth, height=50, command=Cancel)
                cmds.setParent('..')
            cmds.setParent('..')
        cmds.setParent('..')

class Alembic(nerve.Asset, Base):
    def __init__(self, path='', **kwargs):
        kwargs['format'] = 'abc'
        nerve.Asset.__init__(self, path, **kwargs)
        self.AddReleaseMethod('Export')
        self.AddGatherMethod('Import', 'Reference', 'Replace')

        for plugin in ['AbcImport', 'AbcExport']:
            if not cmds.pluginInfo(plugin, q=True, loaded=True):
                cmds.loadPlugin(plugin)

    def Export(self, file=None, **kwargs):
        if not len(cmds.ls(sl=True)):
            print('Nothing selected.'),
            return False

        if not file:
            file = self.GetFilePath('session')
        if not file.GetParent().Exists():
            file.GetParent().Create()

        options = ''
        options+= ' -file {}'.format(file)
        for n in cmds.ls(sl=True, l=True):
            options+= ' -root {}'.format(n)
        frameRange = kwargs['frameRange'] if 'frameRange' in kwargs.keys() else ( cmds.currentTime(q=True), cmds.currentTime(q=True) )
        options+= ' -frameRange {} {}'.format( frameRange[0], frameRange[1] )
        options+= ' -dataFormat ogawa'
        options+= ' -stripNamespaces'
        options+= ' -writeFaceSets'
        options+= ' -writeUVSets'
        options+= ' -uvWrite'

        panel = cmds.paneLayout('viewPanes', q=True, pane1=True)
        cmds.isolateSelect(panel, state=1)

        nerve.Path(file).GetParent().Create()
        cmds.AbcExport(j=options)

        cmds.isolateSelect(panel, state=0)
        
        print('Asset {} released [Alembic]'.format(self.GetPath())),

        return True

    def Reference(self, file=None, **kwargs):
        if file is None:
            file = self.GetFilePath('session')
        options = {}
        options['type'] = 'Alembic'

        args = {}
        args['groupLocator'] = False
        args['returnNewNodes'] = True
        args['reference'] = True
        args['mergeNamespacesOnClash'] = True
        args['namespace'] = kwargs['namespace'] if 'namespace' in kwargs.keys() else nerve.Path(file).GetName()
        args['options'] = ';'.join( ['{}={}'.format(key, val) for key,val in options.items()] )

        return cmds.file(file, **args)

    def Import(self, file=None, **kwargs):
        if not file:
            file = self.GetFilePath('session')
        options = {}
        options['type'] = 'Alembic'

        args = {}
        args['groupLocator'] = False
        args['returnNewNodes'] = True
        args['import'] = True
        args['mergeNamespacesOnClash'] = True
        args['options'] = ';'.join( ['{}={}'.format(key, val) for key,val in options.items()] )
        return cmds.file(file.AsString(), **args)

    def Replace(self, file=None, **kwargs):
        if file is None:
            file = self.GetFilePath('session')

        sel = cmds.ls(sl=True, l=True)
        if not len(sel):
            raise Exception('Nothing Selected.')

        # Replace Reference
        if cmds.referenceQuery(sel[0], isNodeReferenced=True):
            options = {}
            options['type'] = 'Alembic'

            args = {}
            args['groupLocator'] = False
            args['returnNewNodes'] = True
            args['loadReference'] = cmds.referenceQuery(sel[0], referenceNode=True)
            args['options'] = ';'.join( ['{}={}'.format(key, val) for key,val in options.items()] )

            return cmds.file(file, **args)
        else: # Replace From Import
            cmds.AbcImport(file, mode='replace')

    def ReleaseUI(self):
        self._ReleaseUI(anim=True)

    def GatherUI(self):
        self._GatherUI()

class RedshiftProxy(nerve.Asset, Base):
    def __init__(self, path='', **kwargs):
        kwargs['format'] = 'rs'
        nerve.Asset.__init__(self, path, **kwargs)

        self.AddReleaseMethod('Export')
        self.AddGatherMethod('Import', 'Replace')
    
    def Export(self, filepath=None, **kwargs):
        sel = cmds.ls(sl=True, l=True)
        if not len(sel):
            print('Nothing Selected.'),
            return False

        if not filepath :
            filepath  = self.GetFilePath('session')

        if not isinstance(filepath , nerve.Path):
            filepath  = nerve.Path(filepath)

        args = {}
        args['selected'] = True
        args['compress'] = kwargs['compress'] if 'compress' in kwargs.keys() else False

        if not filepath.GetParent().Exists():
            filepath.GetParent().Create()

        if 'frameRange' in self.data.keys():
            dir = filepath.GetParent() + filepath.GetFileName()
            dir.Create()

            panel = cmds.paneLayout('viewPanes', q=True, pane1=True)
            cmds.isolateSelect(panel, state=1)
            for i in range(self.data['frameRange'][0], self.data['frameRange'][1]+1):
                fileName = filepath.GetFileName() + '.{}.rs'.format( str(i).zfill(4) )
                args['filePath'] = str(dir+fileName)
                cmds.currentTime(i, u=True)
                cmds.rsProxy(**args)
            cmds.isolateSelect(panel, state=0)
        else:
            args['filePath'] = filepath.AsString()
            cmds.rsProxy(**args)

        print('Asset {} released [RedshiftProxy]'.format(self.GetPath())),

    def Import(self, file=None, **kwargs):
        if not file:
            file = self.GetFilePath('session')

        proxy = cmds.createNode('RedshiftProxyMesh', name=file.GetName()+'RedshiftProxy', skipSelect=True)
        mesh = cmds.createNode('mesh', name=file.GetName()+'Shape')
        cmds.connectAttr(proxy+'.outMesh', mesh+'.inMesh', f=True)

        trans = cmds.listRelatives(mesh, p=True)[0]
        cmds.setAttr(proxy+'.fileName', file, type='string')
        cmds.setAttr(proxy+'.displayMode', 0)
        if nerve.Path(file).HasFrame():
            cmds.setAttr(proxy+'.useFrameExtension', True)

        cmds.sets(mesh, forceElement='initialShadingGroup')

    def Replace(self, file=None, **kwargs):
        if not file:
            file = self.GetFilePath('session')

        sel = cmds.ls(sl=True, l=True)
        if not len(sel):
            cmds.warning('Nothing Selected. Skipping Replace...')
            return False

        shapes = cmds.ls(sl=True, l=True, dagObjects=True, leaf=True, allPaths=True, type='mesh') or []
        if not len(shapes):
            cmds.warning('Selection is not a refshift Proxy. Skipping Replace...')
            return False
        shape = shapes[0]
        rsProxy = cmds.listConnections( shape+'.inMesh', type='RedshiftProxyMesh') or []

        if not len(rsProxy):
            cmds.warning('Selection is not a refshift Proxy. Skipping Replace...')
            return False

        rsProxy = rsProxy[0]

        cmds.setAttr(rsProxy + '.fileName', file, type='string')

    def ReleaseUI(self):
        self._ReleaseUI(anim=True)

    def GatherUI(self):
        self._GatherUI()

class OBJ(nerve.Asset, Base):
    def __init__(self, path='', **kwargs):
        kwargs['format'] = 'obj'
        nerve.Asset.__init__(self, path, **kwargs)

        self.AddReleaseMethod('Export')
        self.AddGatherMethod('Import', 'Reference', 'Replace')

        for plugin in ['objExport']:
            if not cmds.pluginInfo(plugin, q=True, loaded=True):
                cmds.loadPlugin(plugin)

    def Export(self, file=None, **kwargs):
        if not len(cmds.ls(sl=True)):
            print('Nothing selected.'),
            return False

        if file is None:
            file = self.GetFilePath('session')
        if not file.GetParent().Exists():
            file.GetParent().Create()

        args = {}
        args['force'] = True
        args['type'] = 'OBJexport'
        args['preserveReferences'] = True
        args['exportSelected'] = True
        args['options'] = 'groups=1;ptgroups=1;materials=1;smoothing=1;normals=1'
        cmds.file(file, **args)

        print('Asset {} released [OBJ]'.format(self.GetPath())),
        return True

    def Reference(self, file=None, **kwargs):
        if file is None:
            file = self.GetFilePath('session')

        args = {}
        args['type'] = 'OBJ'
        args['ignoreVersion'] = True
        args['groupLocator'] = False
        args['mergeNamespacesOnClash'] = True
        args['reference'] = True
        args['namespace'] = kwargs['namespace'] if 'namespace' in kwargs.keys() else nerve.Path(file).GetName()
        args['options'] = 'mo=1'

        cmds.file(file, **args)

    def Import(self, file=None, **kwargs):
        if file is None:
            file = self.GetFilePath('session')
        args = {}
        args['type'] = 'OBJ'
        args['ignoreVersion'] = True
        args['groupLocator'] = False
        args['import'] = True
        args['options'] = 'mo=1'

        cmds.file(file, **args)

    def Replace(self, file=None, **kwargs):
        sel = cmds.ls(sl=True, l=True)
        if not len(sel):
            raise Exception('Nothing Selected.')
            
        if file is None:
            file = cmds.GetFilePath('session')
            
        if not cmds.referenceQuery(sel[0], isNodeReferenced=True):
            cmds.warning('Selection is not referenced. OBJ does not support imported replacements.')
            return False

        args = {}
        args['type'] = 'OBJ'
        args['ignoreVersion'] = True
        args['groupLocator'] = False
        args['loadReference'] = cmds.referenceQuery(sel[0], referenceNode=True)
        args['options'] = 'mo=1'

        cmds.file(file, **args)
        return True

    def GatherUI(self):
        self._GatherUI()        

class Maya(nerve.Asset, Base):
    def __init__(self, path='', **kwargs):
        nerve.Asset.__init__(self, path, **kwargs)

        self.AddReleaseMethod('Export')
        self.AddGatherMethod('Import', 'Reference', 'Replace')

    def Export(self, file=None, **kwargs):
        if not len(cmds.ls(sl=True)):
            print('Nothing Selected.'),
            return False

        if not file:
            file = self.GetFilePath('session')

        if not file.GetParent().Exists():
            file.GetParent().Create()

        args = {}
        args['force'] = True
        args['type'] = self.type
        args['preserveReferences'] = True
        args['exportSelected'] = True
        args['options'] = 'v=0'
        cmds.file(file, **args)
        return True

    def Reference(self, file=None, **kwargs):
        if not file:
            file = self.GetFilePath('session')

        args = {}
        args['type'] = self.type
        args['ignoreVersion'] = True
        args['groupLocator'] = False
        args['mergeNamespacesOnClash'] = True
        args['reference'] = True
        args['namespace'] = kwargs['namespace'] if 'namespace' in kwargs.keys() else nerve.Path(file).GetName()
        args['options'] = 'mo=1'

        cmds.file(file, **args)

    def Import(self, file=None, **kwargs):
        if not file:
            file = self.GetFilePath('session')

        args = {}
        args['type'] = self.type
        args['ignoreVersion'] = True
        args['groupLocator'] = False
        args['import'] = True
        args['options'] = 'v=0'

        cmds.file(file, **args)

    def Replace(self, file=None, **kwargs):
        if not file:
            file = self.GetFilePath('session')

        sel = cmds.ls(sl=True, l=True)
        if not len(sel):
            raise Exception('Nothing Selected.')

        if not cmds.referenceQuery(sel[0], isNodeReferenced=True):
            cmds.warning('Selection is not referenced. Maya does not support imported replacements.')
            return False

        args = {}
        args['type'] = self.type
        args['ignoreVersion'] = True
        args['groupLocator'] = False
        args['loadReference'] = cmds.referenceQuery(sel[0], referenceNode=True)
        args['options'] = 'mo=1'

        cmds.file(file, **args)
        return True

    def GatherUI(self):
        self._GatherUI()

class MayaBinary(Maya):
    def __init__(self, path='', **kwargs):
        kwargs['format'] = 'mb'
        self.type = 'mayaBinary'
        Maya.__init__(self, path, **kwargs)

class MayaAscii(Maya):
    def __init__(self, path='', **kwargs):
        kwargs['format'] = 'ma'
        self.type = 'mayaAscii'
        Maya.__init__(self, path, **kwargs)

class FBX(nerve.Asset, Base):
    def __init__(self, path='', **kwargs):
        kwargs['format'] = 'fbx'
        nerve.Asset.__init__(self, path, **kwargs)

        self.AddReleaseMethod('Export')
        self.AddGatherMethod('Import', 'Reference', 'Replace')

        for plugin in ['fbxmaya']:
            if not cmds.pluginInfo(plugin, q=True, loaded=True):
                cmds.loadPlugin(plugin)

    def Export(self, file=None, **kwargs):
        if not len(cmds.ls(sl=True)):
            print('Nothing Selected'),
            return False

        if not file:
            file = self.GetFilePath('session')
        if not file.GetParent().Exists():
            file.GetParent().Create()

        mel.eval('FBXResetExport')
        mel.eval('FBXProperty Export|AdvOptGrp|UI|GenerateLogData -v 0')

        if 'animation' in kwargs.keys():
            mel.eval('FBXProperty Export|IncludeGrp|Animation -v {}'.format(int(kwargs['animation'])))

        if 'frameRange' in kwargs.keys():
            mel.eval('FBXProperty Export|IncludeGrp|Animation -v 1')
            mel.eval('FBXProperty Export|IncludeGrp|Animation|BakeComplexAnimation -v 1')
            mel.eval('FBXProperty Export|IncludeGrp|Animation|BakeComplexAnimation|BakeFrameStart -v {}'.format(kwargs['frameRange'][0]))
            mel.eval('FBXProperty Export|IncludeGrp|Animation|BakeComplexAnimation|BakeFrameEnd -v {}'.format(kwargs['frameRange'][1]))
            mel.eval('FBXProperty Export|IncludeGrp|Animation|BakeComplexAnimation|BakeFrameStep -v 1')
        else:
            mel.eval('FBXProperty Export|IncludeGrp|Animation|BakeComplexAnimation -v 0')

        nerve.Path(file).GetParent().Create()
        mel.eval('FBXExport -f "{}" -s'.format(file))

    def Reference(self, file=None, **kwargs):

        if not file:
            file = self.GetFilePath('session')        
        args = {}
        args['type'] = 'FBX'
        args['ignoreVersion'] = True
        args['groupLocator'] = False
        args['mergeNamespacesOnClash'] = True
        args['reference'] = True
        args['namespace'] = kwargs['namespace'] if 'namespace' in kwargs.keys() else nerve.Path(file).GetName()
        args['options'] = 'mo=1'

        cmds.file(file, **args)

    def Import(self, file=None, **kwargs):
        if not file:
            file = self.GetFilePath('session')        
        args = {}
        args['type'] = 'FBX'
        args['ignoreVersion'] = True
        args['groupLocator'] = False
        args['import'] = True
        args['options'] = 'mo=1'

        cmds.file(file, **args)

    def Replace(self, file=None, **kwargs):

        if not file:
            file = self.GetFilePath('session')        

        sel = cmds.ls(sl=True, l=True)
        if not len(sel):
            raise Exception('Nothing Selected.')

        if not cmds.referenceQuery(sel[0], isNodeReferenced=True):
            cmds.warning('Selection is not referenced. OBJ does not support imported replacements.')
            return False

        args = {}
        args['type'] = 'OBJ'
        args['ignoreVersion'] = True
        args['groupLocator'] = False
        args['loadReference'] = cmds.referenceQuery(sel[0], referenceNode=True)
        args['options'] = 'mo=1'

        cmds.file(file, **args)
        return True

    def ReleaseUI(self):
        self._ReleaseUI(anim=True)
    
    def GatherUI(self):
        self._GatherUI()

class USDBase(nerve.Asset, Base):
    def __init__(self, path='', **kwargs):
        nerve.Asset.__init__(self, path, **kwargs)

        self.AddReleaseMethod('Export')
        self.AddGatherMethod('Import', 'Reference', 'Replace', 'Proxy')

        for plugin in ['mayaUsdPlugin']:
            if not cmds.pluginInfo(plugin, q=True, loaded=True):
                cmds.loadPlugin(plugin)

    def Export(self, file=None, **kwargs):
        if not len(cmds.ls(sl=True)):
            print('Nothing Selected.'),
            return False
        
        if not file:
            file = self.GetFilePath('session')

        if not file.GetParent().Exists():
            file.GetParent().Create()

        args = {}

        args['selection'] = True
        args['defaultMeshScheme'] = 'none'
        args['mergeTransformAndShape'] = True
        args['stripNamespaces'] = True
        args['exportUVs'] = True
        args['exportColorSets'] = False
        args['exportDisplayColor'] = False
        args['filterTypes'] = ('parentConstraint')


        if not ('frameRange' in kwargs.keys()): # Static
            args['file'] = file
            args['staticSingleSample'] = True

            # Export Static
            cmds.mayaUSDExport(**args)

            return True
        else: # Animation
            panel = cmds.paneLayout('viewPanes', q=True, pane1=True)
            cmds.isolateSelect(panel, state=1)


            if not ('filePerFrame' in kwargs.keys() and kwargs['filePerFrame']): # Export Single Anim
                args['frameRange'] = kwargs['frameRange']
                args['staticSingleSample'] = False
                args['file'] = file
                cmds.mayaUSDExport(**args)
            else: # File Per Frame
                sel = cmds.ls(sl=True, l=True)
                if len(sel) > 1:
                    raise Exception('Only one object can be exported as a file per frame.')

                clipPath = sel[0].replace('|', '/')

                args['staticSingleSample'] = True
                file = nerve.Path(file)
                dir = file.GetParent() + file.GetFileName()
                dir.Create()

                clips = []
                for i in range(kwargs['frameRange'][0], kwargs['frameRange'][1]+1):
                    cmds.currentTime(i, u=True)
                    fileName = file.GetFileName() + '.{}.{}'.format( str(i).zfill(4), file.GetExtension() )
                    args['file'] = dir+fileName
                    #args['frameRange'] = (i,i)
                    clips.append(args['file'].AsString())
                    cmds.mayaUSDExport(**args)
                # Stitch Clips
                nerve.USD.StitchClips( file.AsString(), clips, clipPath, kwargs['frameRange'])


            cmds.isolateSelect(panel, state=0)

        args['staticSingleSample'] = True

    def Reference(self, file=None, **kwargs):
        if not file:
            file = self.GetFilePath('session')        
        options = {}
        options['readAnimData'] = "1"
       # if 'frameRange' in kwargs.keys():
        #    options['frameRange'] = '({},{})'.format(frameRange[0], frameRange[1])

        args = {}
        args['type'] = 'USD Import'
        args['reference'] = True
        args['namespace'] = kwargs['namespace'] if 'namespace' in kwargs.keys() else nerve.Path(file).GetName()
        args['options'] = ';'.join( ['{}={}'.format(key, val) for key,val in options.items()] )

        return cmds.file(file, **args)

    def Import(self, file=None, **kwargs):
        if not file:
            file = self.GetFilePath('session')        
        args = {}
        args['file'] = file
        args['readAnimData'] = True
        #if 'frameRange' in kwargs.keys():
        #    args['frameRange'] = frameRange

        cmds.mayaUSDImport(**args)

    def Proxy(self, file=None, **kwargs):
        if not file:
            file = self.GetFilePath('session')        
        print("CREATE PROXY")

    def Replace(self, file=None, **kwargs):
        sel = cmds.ls(sl=True, l=True)
        
        if not len(sel):
            raise Exception('Nothing selected.')

        if not file:
            file = self.GetFilePath('session')             

        if cmds.referenceQuery(sel[0], isNodeReferenced=True):
            options = {}

            args = {}
            args['returnNewNodes'] = True
            args['loadReference'] = cmds.referenceQuery(sel[0], referenceNode=True)
            args['options'] = ';'.join( ['{}={}'.format(key, val) for key,val in options.items()] )

            return cmds.file(file, **args)
        else:
            raise Exception('Selection is not referenced.')

    def ReleaseUI(self):
        return self._ReleaseUI(anim=True)

    def GatherUI(self):
        self._GatherUI()

class USDAscii(USDBase):
    def __init__(self, path='', **kwargs):
        kwargs['format'] = 'usda'
        self.type = 'usdascii'
        USDBase.__init__(self, path, **kwargs)

class USD(USDBase):
    def __init__(self, path='', **kwargs):
        kwargs['format'] = 'usd'
        self.type = 'USD'
        USDBase.__init__(self, path, **kwargs)

class Node:
    def __init__(self, node):
        self.node = node
        self.data = {}

    @staticmethod
    def CleanName(name):
        return name.split(':')[-1]

    @staticmethod
    def GetShadingEngines(obj, hierarchy=True):
        if 'dagNode' in cmds.nodeType(obj, inherited=True):
            objects = [obj]
            if hierarchy:
                objects += cmds.listRelatives(obj, allDescendents=True, fullPath=True, type='mesh') or []

            shadingEngines = []
            for n in objects:
                if cmds.nodeType(n) != 'mesh':
                    continue
                shadingEngines+= cmds.listConnections(n, destination=True, source=False, plugs=False, type='shadingEngine') or []
            
            return list(set(shadingEngines))
        
        if cmds.getClassification(cmds.nodeType(obj), satisfies='shader'):
            
            sgs = cmds.listConnections(obj + '.outColor', type='shadingEngine') 
            if sgs:
                return list(set(sgs))
            
        return None
        
    @staticmethod
    def GetMaterials(sel=None):
        if sel is None:
            sel = cmds.ls(sl=True, l=True)
        
        if not isinstance(sel, list):
            sel = [sel]
        
        if not len(sel):
            return []
        
        materials = []
        for n in sel:
            # Dag Node
            if 'dagNode' in cmds.nodeType(n, inherited=True):
                shadingEngines = Node.GetShadingEngines( n )
                for sg in shadingEngines:
                    materials+=cmds.listConnections( sg+'.surfaceShader', source=True, destination=True, plugs=False) or []
                continue
            # Shader
            if cmds.getClassification(cmds.nodeType(n), satisfies='shader'):
                materials.append( n )
                continue

            # Other Node
            future = cmds.listHistory(n, future=True, fastIteration=True, pruneDagObjects=True)
            for f in future:
                if cmds.getClassification(cmds.nodeType(n), satisfies='shader'):
                    materials.append( n )
        
        return list(set(materials))

    @staticmethod
    def uvtexture(placement, textures=None):
        if textures is None:
            textures = cmds.ls(sl=True, l=True, type='file')

        if not isinstance(textures, list):
            textures = [textures]
        
        if not len(textures):
            return False

        attribs = [
            'coverage',
            'translateFrame',
            'rotateFrame',
            'mirrorU',
            'mirrorV',
            'stagger',
            'wrapU',
            'wrapV',
            'repeatUV',
            'offset',
            'rotateUV',
            'noiseUV',
            'vertexUvOne',
            'vertexUvTwo',
            'vertexUvThree',
            'vertexCameraOne'
        ]
        for tex in textures:
            for attr in attribs:
                cmds.connectAttr(placement + '.' + attr, tex + '.' + attr, f=True)
            cmds.connectAttr(placement + '.outUV', tex + '.uv', f=True)
            cmds.connectAttr(placement + '.outUvFilterSize', tex + '.uvFilterSize', f=True)

    @staticmethod
    def listHistory(plug, nodeType, **kwargs):
        history = cmds.listHistory(plug, **kwargs)
        for h in history:
            if cmds.nodeType(h) == nodeType:
                return h
        return False

    @staticmethod
    def setAttr(node, attr, value):
        #print(node, attr)
        plug = node + '.' + attr
        attrdata = Node.GetAttrData(node, attr)
        
        if attrdata['type'] == 'string':
            cmds.setAttr(plug, value, type='string')
            return True
        
        if attrdata['type'] == 'vector':
            if isinstance(value, (list, tuple)):
                cmds.setAttr(plug, value[0], value[1], value[2], type='double3')
            else:
                cmds.setAttr(plug, value, value, value, type='double3')
            return True
        
        if attrdata['type'] == 'vector2':
            cmds.setAttr(plug, value[0], value[1])
            return True

        if attrdata['type'] == 'float':
            val = value
            if isinstance(value, (list, tuple)):
                val = value[0]

            if 'min' in attrdata.keys() and val < attrdata['min']:
                cmds.warning('Cannot set '+node+'.'+attr+' below its minimum value of '+str(attrdata['min']))
                return True
            if 'max' in attrdata.keys() and val > attrdata['max']:
                cmds.warning('Cannot set '+node+'.'+attr+' above its maximum value of '+str(attrdata['max']))
                return True

            cmds.setAttr(plug, val)
            return True

        cmds.setAttr(plug, value)

    @staticmethod
    def getAttr(node, attr):
        return Node.GetAttrData(node, attr)['value']

    @staticmethod
    def attrExists(node, attr):
        return cmds.attributeQuery(attr, n=node, exists=True)
    
    @staticmethod
    def connectAttr(outnode, outplug, innode, inplug):
        return cmds.connectAttr(outnode+'.'+outplug, innode+'.'+inplug, f=True)

    @staticmethod
    def listAttr(node):
        attribs = cmds.attributeInfo(node, all=True)
        exclude = ['TdataCompound', 'message', 'Tdata']
        attributes = []
        for attr in attribs:
            # Exclude
            if cmds.attributeQuery(attr, n=node, hidden=True):
                continue
            if cmds.attributeQuery(attr, n=node, listParent=True):
                continue
            if not cmds.attributeQuery(attr, n=node, writable=True, readable=True):
                continue
            atype = cmds.getAttr(node + '.'+attr, type=True)
            if atype in exclude:
                continue

            attributes.append(attr)

        return attributes

    @staticmethod
    def GetAttrData(node, attr):
        plug = node+'.'+attr
        atype = cmds.getAttr(plug, type=True)

        data = {}
        data['name'] = attr
        if cmds.listConnections(plug):
            innode = cmds.listConnections(plug)[0]
            inplug = cmds.listConnections(plug, plugs=True)[0]
            data['node'] = innode
            data['plug'] = inplug.replace(innode, '')[1:]

        if atype in ['float', 'double', 'doubleAngle']:
            data['value'] = cmds.getAttr(plug)
            data['default'] = cmds.attributeQuery(attr, n=node, listDefault=True)[0]
            data['type'] = 'float'
            if cmds.attributeQuery(attr, n=node, minExists=True):
                data['min'] = cmds.attributeQuery(attr, n=node, min=True)[0]
            if cmds.attributeQuery(attr, n=node, maxExists=True):
                data['max'] = cmds.attributeQuery(attr, n=node, max=True)[0]
            return data

        if atype == 'float2':
            data['value'] = cmds.getAttr(plug)[0]
            data['default'] = tuple(cmds.attributeQuery(attr, n=node, listDefault=True))
            data['type'] = 'vector2'
            return data

        if atype == 'float3':
            data['value'] = cmds.getAttr(plug)[0]
            data['default'] = tuple(cmds.attributeQuery(attr, n=node, listDefault=True) or [0,0,0])
            data['type'] = 'vector'
            return data

        if atype == 'bool':
            data['value'] = cmds.getAttr(plug)
            data['default'] = bool(cmds.attributeQuery(attr, n=node, listDefault=True)[0])
            data['type'] = 'bool'
            return data

        if atype == 'short' or atype == 'long':
            data['value'] = cmds.getAttr(plug)
            data['default'] = int(cmds.attributeQuery(attr, n=node, listDefault=True)[0])
            data['type'] = 'int'
            if cmds.attributeQuery(attr, n=node, minExists=True):
                data['min'] = cmds.attributeQuery(attr, n=node, min=True)[0]
            if cmds.attributeQuery(attr, n=node, maxExists=True):
                data['max'] = cmds.attributeQuery(attr, n=node, max=True)[0]            
            return data

        if atype == 'enum':
            data['options'] = cmds.attributeQuery(attr, n=node, listEnum=True)[0].split(':')
            data['value'] = cmds.getAttr(plug)
            data['default'] = int(cmds.attributeQuery(attr, n=node, listDefault=True)[0])
            data['type'] = 'enum'
            return data

        if atype == 'string':
            data['value'] = cmds.getAttr(plug) or ''
            data['default'] = cmds.attributeQuery(attr, n=node, listDefault=True) or ''
            data['type'] = 'string'
            return data
        
        raise Exception('attribute type not defined:'+ atype)

    @staticmethod
    def GetRandomValue(node, attr):
        def setRange(value, oldmin, oldmax, min, max):
            ''' OutValue = Min + (((Value-OldMin)/(OldMax-OldMin)) * (Max-Min))'''
            return min + (((value-oldmin)/(oldmax-oldmin)) * (max-min))

        def decimal(value, places=1000):
            return int(value*places)/float(places)

        def rand():
            return decimal(random.random())

        import random

        attrdata = Node.GetAttrData(node, attr)
        if attrdata['type'] == 'float':
            min = attrdata['min'] if 'min' in attrdata.keys() else 0
            max = attrdata['max'] if 'max' in attrdata.keys() else 1
            rand = setRange(rand(), 0, 1, min, max)
            return rand

        if attrdata['type'] == 'bool':
            return not cmds.getAttr(node+'.'+attr)
        if attrdata['type'] == 'vector':
            return (rand(), rand(), rand())
        if attrdata['type'] == 'vector2':
            return (rand(), rand())
        if attrdata['type'] == 'int':
            min = attrdata['min'] if 'min' in attrdata.keys() else 1
            max = attrdata['max'] if 'max' in attrdata.keys() else 10
            return setRange( int(random.random() * 1000, 0, 1, min, max ) )
        if attrdata['type'] == 'enum':
            return int( random.random() * len(attrdata['options']))
        if attrdata['type'] == 'string':
            return str( random.random() )
        
        return random.random()

    def Serialize(self, history=None):
        self.data['name'] = Node.CleanName(self.node)
        self.data['type'] = cmds.nodeType(self.node)
        self.data['attr'] = {}

        if history is None:
            self.data['history'] = {}
            history = self.data['history']

        for attr in Node.listAttr(self.node):
            attrdata = Node.GetAttrData(self.node, attr)
            if attrdata['default'] != attrdata['value']:
                self.data['attr'][attr] = {'value':attrdata['value']}

            if 'node' in attrdata.keys():
                if attr not in self.data['attr'].keys(): # create attr dict
                    self.data['attr'][attr] = {}

                nodeClean = Node.CleanName( attrdata['node'] )
                self.data['attr'][attr]['node'] = nodeClean
                self.data['attr'][attr]['plug'] = attrdata['plug']

                if nodeClean not in history.keys():
                    history[nodeClean] = {}
                    history[nodeClean] = Node( attrdata['node'] ).Serialize( history )

        return self.data

    def Unserialize(self, data, history=None, clearNamespace=True):
        # Namespace
        ns = 'nrv'
        cmds.namespace(setNamespace=':')
        if not cmds.namespace(exists=ns):
            cmds.namespace(add=ns)
        cmds.namespace(setNamespace=ns)

        # History
        if history is None:
            history = data['history']
        
        data['name'] = Node.create(data['type'], data['name'])
        for attr,adata in data['attr'].items():

            if 'value' in adata.keys(): # Set Attr
                Node.setAttr(data['name'], attr, adata['value'])

            if 'node' in adata.keys(): # Connect Node
                node = adata['node']
                nodens = ns+':'+adata['node']
                if not cmds.objExists(nodens): 
                    Node( node ).Unserialize( history[node], history, False )
                    cmds.connectAttr( nodens + '.' + adata['plug'], data['name']+'.'+attr, f=True )

        cmds.select(data['name'], r=True)
        cmds.namespace(setNamespace=':')
        if clearNamespace:
            cmds.namespace(removeNamespace=ns, mergeNamespaceWithRoot=True, f=True)
        return cmds.ls(sl=True)[0]

    @staticmethod
    def create(ntype, name=None):
        args = {}
        if name:
            args['name'] = name

        if ntype == 'file':
            tex = cmds.shadingNode('file', asTexture=True, isColorManaged=True, **args)
            uv = cmds.shadingNode('place2dTexture', asUtility=True)
            Node.uvtexture(uv, tex)
            return tex
        if ntype == 'shadingGroup':
            sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, **args)
            return sg

        if cmds.getClassification(ntype, satisfies='shader'):
            return cmds.shadingNode(ntype, asShader=True, **args)
        if cmds.getClassification(ntype, satisfies='utility'):
            return cmds.shadingNode(ntype, asUtility=True, **args)
        if cmds.getClassification(ntype, satisfies='texture'):
            return cmds.shadingNode(ntype, asTexture=True, **args)
        
        return cmds.createNode(ntype, **args)

class Material(nerve.Material, Base):
    def __init__(self, path='', **kwargs):
        nerve.Material.__init__(self, path, **kwargs)
        self.SetExtension('json')

        self.AddReleaseMethod('Export')
        self.AddGatherMethod('Import')

    def SetAbstractData(self, node, attr, data):
        if isinstance(data, dict): # Has Texture
            #Node.setAttr( node, attr, data['value'])
            tex = self.SetTextureData( data['texture'] )
            atype = cmds.getAttr(node+'.'+attr, type=True)
            if atype == 'float3':
                cmds.connectAttr( tex + '.outColor', node+'.'+attr, f=True)
            if atype == 'float':
                cmds.connectAttr( tex + '.outAlpha', node+'.'+attr, f=True)
        else: # Does not have texture
            val = data
            if val is None:
                return False
            Node.setAttr( node, attr, val )

    def ConvertFromAbstract(self, material, data):
        mattype = cmds.nodeType(material)

        table = self.GetMaterialTable( mattype )
        for grp in table.keys(): # grp: diffuse, reflection, refraction etc
            for key, attr in table[grp].items(): # key: abstract attr name, attr: concrete attr name
                if isinstance(attr, list): # Has Search Node
                    if grp == 'displacement':
                        cdata = attr[0]
                        if 'node' not in data[grp].keys() and self.HasDisplacement(data):
                            data[grp]['node'] = Node.create( cdata['type'] )
                            data[grp]['plug'] = cdata['plug']

                        utable = self.GetUtilityTable( cdata['type'] )
                        for ukey, uattr in utable[grp].items():
                            self.SetAbstractData(data[grp]['node'], uattr, data[grp][ukey] )
                    else:
                        cdata = attr[0]
                        if 'node' not in data[grp].keys():
                            data[grp]['node'] = Node.create( cdata['type'] )
                        utable = self.GetUtilityTable( cdata['type'] )
                        for ukey, uattr in utable[grp].items():
                            self.SetAbstractData(data[grp]['node'], uattr, data[grp][ukey] )
                        if all(x in cdata for x in ['attr', 'plug']):
                            Node.connectAttr(data[grp]['node'], cdata['plug'], material, cdata['attr'])
                else:
                    self.SetAbstractData(material, attr, data[grp][key])

    def ConvertFromAbstractOLD(self, material, data):
        mattype = cmds.nodeType(material)

        table = self.GetMaterialTable( mattype )
        for grp in table.keys(): # grp: diffuse, reflection, refraction etc
            for key, attr in table[grp].items(): # key: abstract attr name, attr: concrete attr name
                if isinstance(table[grp][key], list): # Has Search Node
                    cdata = table[grp][key][0] # Select first choice
                    if grp == 'displacement' and not data[grp][key]:
                        continue

                    util = Node.create(cdata['type'])
                    if 'attr' in cdata.keys() and 'plug' in cdata.keys():
                        sg = cmds.listConnections(material, type='shadingEngine')
                        if grp == 'displacement':
                            if sg:
                                Node.connectAttr(util, cdata['plug'], sg[0], cdata['attr'])
                        else:
                            Node.connectAttr(util, cdata['plug'], material, cdata['attr'])

                    utable = self.GetUtilityTable(cdata['type'])
                    self.SetAbstractData(util, utable[grp][key], data[grp][key])
                    continue

                self.SetAbstractData(material, attr, data[grp][key])

    def GetTextureColorCorrectData(self, node, cc):
        ntype = cmds.nodeType(node)
        if ntype == 'setRange':
            inmin = cmds.getAttr(node+'.oldMin')[0]
            inmax = cmds.getAttr(node+'.oldMax')[0]
            outmin = cmds.getAttr(node+'.min')[0]
            outmax = cmds.getAttr(node+'.max')[0]

            cc['range'] = (inmin[0], inmax[0], outmin[0], outmax[0])
        return cc

    def SetTextureData(self, data):
        tex = Node.create('file', data['name'])
        uv = cmds.listConnections(tex + '.uv')[0]

        Node.setAttr(tex, 'fileTextureName', data['filepath'])
        Node.setAttr(tex, 'colorSpace', data['colorSpace'])
        Node.setAttr(tex, 'alphaIsLuminance', data['alphaIsLuminance'])
        Node.setAttr(uv, 'repeatU', data['uvScale'][0])
        Node.setAttr(uv, 'repeatV', data['uvScale'][1])
        Node.setAttr(uv, 'offsetU', data['uvOffset'][0])
        Node.setAttr(uv, 'offsetV', data['uvOffset'][1])
        Node.setAttr(uv, 'rotateUV', data['uvRotate'])

        return tex
        
    def GetTextureData(self, node, attr, data=None):
        if not data:
            data = self.texture()

        plug = node+'.'+attr
        con = cmds.listConnections(plug)
        if not con: # texture not found, return empty
            return {}

        con = con[0]
        contype = cmds.nodeType(con)
        if contype == 'file': # Texture found, return data
            data['name'] = Node.CleanName(con)
            data['filepath'] = cmds.getAttr(con + '.fileTextureName')
            data['colorSpace'] = cmds.getAttr(con + '.colorSpace')
            data['alphaIsLuminance'] = cmds.getAttr(con + '.alphaIsLuminance')
            # UV
            uvNode = cmds.listConnections(con + '.uv', type='place2dTexture')
            if uvNode:
                data['uvScale'] = (cmds.getAttr(uvNode[0] + '.repeatU'), cmds.getAttr(uvNode[0] + '.repeatV'))
                data['uvOffset'] = (cmds.getAttr(uvNode[0] + '.offsetU'), cmds.getAttr(uvNode[0] + '.offsetV'))
                data['uvRotate'] = cmds.getAttr(uvNode[0] + '.rotateUV')

            # Color Correct
            gain = Node.getAttr(con, 'colorGain')
            offset = Node.getAttr(con, 'colorOffset')
            
            data['colorCorrect']['gain']*=gain[0]
            data['colorCorrect']['offset']+=offset[0]
            return data

        # Color Correct
        data['colorCorrect'] = self.GetTextureColorCorrectData( con, data['colorCorrect'])
        
        # Next Node
        nextPlug = cmds.listConnections(con, connections=True, source=True, destination=False, plugs=True)
        if not nextPlug: # texture not found, reset al data
            return {}        
        nextCon = nextPlug[0].split('.')[0]
        nextAttr = nextPlug[0].split('.')[-1]

        return self.GetTextureData(nextCon, nextAttr, data)

    def GetAbstractData(self, node, table, data={}):
        for grp in table.keys(): # grp: diffuse, reflection, bump etc...
            if grp not in data.keys():
                data[grp] = {}

            for abst, conc in table[grp].items(): # abstract/concrete attribute names
                if isinstance(conc, list): # if concrete attr is list search for nodes
                    for cdata in conc: # for each attribute in list
                        searchnode = node # store search node
                        if grp == 'displacement': # for displacement, search node is ShadingEngine
                            con = cmds.listConnections(node, type='shadingEngine')
                            if not con: # shading engine not found
                                continue
                            searchnode = con[0]
                        if 'attr' in cdata.keys(): # search node.attribute
                            searchnode+='.'+cdata['attr']

                        if cdata['type'] not in self.GetUtilityTypes():
                            continue
                        history = Node.listHistory(searchnode, cdata['type']) # Get search node history for node
                        if not history:
                            continue

                        ctable = self.GetUtilityTable(cdata['type']) # get utility node table
                        self.GetAbstractData( history, ctable, data ) # set data from utility node

                else: # concrete attribute should exist on node
                    attrdata = Node.GetAttrData(node, conc)
                    data[grp][abst] = attrdata['value']
                    if 'node' in attrdata.keys():
                        data[grp][abst] = {}
                        data[grp][abst]['value'] = attrdata['value']
                        data[grp][abst]['texture'] = self.GetTextureData( node, conc )
        return data
    
    def HasDisplacement(self, data):
        if 'displacement' in data.keys():
            if 'map' in data['displacement'].keys():
                if isinstance(data['displacement']['map'], dict):
                    if data['displacement']['map']['texture']:
                        return True
        return False
    
    def GetDisplacement(self, data):
        return data['displacement']['map']['node']

    def ConvertToAbstract(self, material):
        mattype = cmds.nodeType(material)
        if mattype not in self.GetMaterialTypes():
            return {}
        
        data = self.abstract()
        table = self.GetMaterialTable( mattype ) # Convertion data
        self.GetAbstractData( material, table, data)

        return data

    def Export(self, concrete=True, abstract=True):
        sel = cmds.ls(sl=True, l=True)
        if not len(sel):
            cmds.warning('Nothing selected.')
            return False

        data = {}
        materials = Node.GetMaterials( sel )
        for material in materials:
            data[material] = {}
            data[material]['name'] = Node.CleanName(material)
            data[material]['type'] = cmds.nodeType(material)
            data[material]['sets'] = self.GetShadingEngines(material)
            data[material]['app'] = 'maya'
            # Concrete
            if concrete:
                data[material]['concrete'] = Node(material).Serialize()
            # Abstract
            if abstract and cmds.nodeType(material) in self.GetMaterialTypes():
               data[material]['abstract'] = self.ConvertToAbstract(material)

        # Save File
        datafile = self.GetFilePath('session')
        if not datafile.GetParent().Exists():
            datafile.GetParent().Create()

        with open(datafile.AsString(), 'w') as outfile:
            json.dump(data, outfile, indent=4)

    def Import(self, shader='lambert'):
        datafile = self.GetFilePath('session')
        with open( datafile.AsString(), 'r') as infile:
            indata = json.load( infile )

        materials = []
        for name, data in indata.items(): # material, material data
            if 'concrete' in data.keys() and data['concrete']['type'] == shader:
                material = Node(name).Unserialize(data['concrete'])
                materials.append(material)
                continue
            
            material = Node.create(shader, name=name)
            materials.append(material)
            self.ConvertFromAbstract(material, data['abstract'])
        return materials
    
    def Convert(self, shader, remove=True):
        sel = cmds.ls(sl=True, l=True)
        if not len(sel):
            cmds.warning('Nothing Selected.')
            return False
        
        materials = Node.GetMaterials( sel )
        for material in materials:
            mattype = cmds.nodeType(material)
            if mattype not in self.GetMaterialTypes():
                continue
            if shader == mattype:
                continue

            sgs = Node.GetShadingEngines(material)
            data = self.ConvertToAbstract(material)

            mat = Node.create(shader, name=material+'_'+shader)
            self.ConvertFromAbstract(mat, data)

            for sg in sgs:
                cmds.connectAttr(mat + '.outColor', sg + '.surfaceShader', f=True)
                if self.HasDisplacement(data):
                   Node.connectAttr(data['displacement']['node'], data['displacement']['plug'], sg, 'displacementShader')

    def ConvertOLD(self, shader, remove=True):
        sel = cmds.ls(sl=True, l=True)
        if not len(sel):
            cmds.warning('Nothing selected.')

        materials = []
        for n in sel:
            ntype = cmds.nodeType(n)
            if not cmds.getClassification(ntype, satisfies='shader'):
                continue
            if ntype not in self.GetMaterialTypes():
                continue
            if shader == ntype:
                continue
            
            # New material
            material = Node.create(shader, name=n)

            ctable = self.GetMaterialConvertTable( ntype, shader )
            for grp in ctable.keys():
                for key, val in ctable[grp].items():
                    if not (val['src'] and val['dest']):
                        continue
                    if isinstance(val['src'], list): # Utility Node
                        cdata = val['src']
                        util = Node.create(cdata['type'])
                    else:
                        pass

                    con = cmds.listConnections(n+'.'+val['src'], plugs=True)
                    if con: # Has Texture
                        cmds.connectAttr(con[0], material+'.'+val['dest'], f=True)
                    else:
                        value = Node.getAttr( n, val['src'] )
                        Node.setAttr( material, val['dest'], value )

            # Future
            con = cmds.listConnections(n + '.outColor', plugs=True) or []
            for c in con:
                cmds.connectAttr(material + '.outColor', c, f=True)

            if remove:
                cmds.delete(n)
                name = cmds.rename(material, n)
                materials.append( name )
            else:
                materials.append(material)
            
    
        return materials

    def mat_RedshiftMaterial(self):
       return {
            'diffuse': {
                'color':'diffuse_color',
                'weight':'diffuse_weight',
                'roughness':'diffuse_roughness'
                },
            'translucency':{
                'color':'transl_color',
                'weight':'transl_weight',
                },    
            'reflection': {
                'color': 'refl_color',
                'weight': 'refl_weight',
                'roughness':'refl_roughness',
                'anisotropy': 'refl_aniso',
                'rotation': 'refl_aniso_rotation',
                'metalness': 'refl_metalness',
                'reflectivity': 'refl_reflectivity',
                'ior': 'refl_ior',
                },
            'refraction': {
                'color': 'refr_color',
                'weight': 'refr_weight',
                'roughness': 'refr_roughness',
                'ior': 'refr_ior',
                'dispersion': 'refr_abbe',
                'thinWalled': 'refr_thin_walled',
                'transmittance': 'refr_transmittance',
                'absorption': 'refr_absorption_scale',
                },
            'sheen': {
                'color': 'sheen_color',
                'weight': 'sheen_weight',
                'roughness': 'sheen_roughness',
                },   
            'coat': {
                'color': 'coat_color',
                'weight': 'coat_weight',
                'roughness': 'coat_roughness',
                'ior': 'coat_ior',
                },
            'sss': {
                'weight': 'ms_amount',
                'radius': 'ms_radius_scale',
                'colorSingle': 'ss_scatter_coeff',
                'weightSingle': 'ss_amount',
                'phaseSingle': 'ss_phase',
                'colorShallow': 'ms_color0',
                'weightShallow': 'ms_weight0',
                'radiusShallow': 'ms_radius0',
                'colorMid': 'ms_color1',
                'weightMid': 'ms_weight1',
                'radiusMid': 'ms_radius1',
                'colorDeep': 'ms_color2',
                'weightDeep': 'ms_weight2',
                'radiusDeep': 'ms_radius2',
                },   
            'emission': {
                'color': 'emission_color',
                'weight': 'emission_weight',
                },
            'opacity': {
                'color': 'opacity_color',
                },
            'bump': {
                'map': [{'type':'RedshiftBumpMap', 'plug':'out', 'attr':'bump_input'}],
                #'height': [{'type':'RedshiftBumpMap'}],
                },
            'displacement': {
                    'map': [{'type':'RedshiftDisplacement', 'plug':'out', 'attr':'displacementShader'}],
                    #'scale': [{'type':'bump2d', 'attr':'normalCamera'}],
                },                
        }
    def mat_aiStandardSurface(self):
        return self.mat_standardSurface()
    def mat_standardSurface(self):
        return {
            'diffuse': {
                'color': 'baseColor',
                'weight': 'base',
                'roughness': 'diffuseRoughness'
            },
            'reflection': {
                'color': 'specularColor',
                'weight': 'specular',
                'roughness':'specularRoughness',
                'anisotropy': 'specularAnisotropy',
                'rotation': 'specularRotation',
                'metalness': 'metalness',
                'ior': 'specularIOR',
                },
            'refraction': {
                'weight': 'transmission',
                'roughness': 'transmissionExtraRoughness',
                'dispersion': 'transmissionDispersion',
                'thinWalled': 'thinWalled',
                'transmittance': 'transmissionColor',
                'absorption': 'transmissionDepth',
                },
            'sheen': {
                'color': 'sheenColor',
                'weight': 'sheen',
                'roughness': 'sheenRoughness',
                },   
            'coat': {
                'color': 'coatColor',
                'weight': 'coat',
                'roughness': 'coatRoughness',
                'ior': 'coatIOR',
                },         
            'sss': {
                'weight': 'subsurface',
                'radius': 'subsurfaceScale',
                'colorShallow': 'subsurfaceColor',
            },
            'emission': {
                'color': 'emissionColor',
                'weight': 'emission',
                },
          'opacity': {
                'color': 'opacity',
                },
            'bump': {
                'map': [{'type':'bump2d', 'plug':'outNormal', 'attr':'normalCamera'}],
                },
            'displacement': {
                    'map': [{'type':'displacementShader', 'plug':'displacement', 'attr':'displacementShader'}],
                },                                                                                      
        }
    def mat_usdPreviewSurface(self):
        return {
            'diffuse': {
                'color': 'diffuseColor'
            },
            'reflection': {
                'color': 'specularColor',
                'roughness':'roughness',
                'metalness': 'metallic',
                'ior': 'ior',
                },
            'coat': {
                'weight': 'clearcoat',
                'roughness': 'clearcoatRoughness',
                },     
            'emission': {
                'color': 'emissiveColor',
                },
            'opacity': {
                'color': 'opacity',
                },                                              
        }
    def mat_lambert(self):
        return {
            'diffuse': {
                'color':'color',
                'weight':'diffuse'
                },
            'emission': {
                'color': 'incandescence',
                }, 
            'opacity': {
                'color': 'transparency',
                },  
            'bump': {
                'map': [{'type':'bump2d', 'plug':'outNormal', 'attr':'normalCamera'}],
                },
            'displacement': {
                    'map': [{'type':'displacementShader', 'plug':'displacement', 'attr':'displacementShader'}],
                },
        }
    def mat_blinn(self):
        return {
            'diffuse': {
                'color':'color',
                'weight': 'diffuse',
            },
            'translucency':{
                'weight':'translucence',
            },
            'reflection': {
                'color': 'specularColor',
                'metalness': 'reflectivity',
                'roughness':'eccentricity',
                'reflectivity': 'reflectedColor',
                },  
            'emission': {
                'color': 'incandescence',
                },
            'opacity': {
                'color': 'transparency',
                },
            'bump': {
                'map': [{'type':'bump2d', 'plug':'outNormal', 'attr':'normalCamera'}],
                },
            'displacement': {
                    'map': [{'type':'displacementShader', 'plug':'displacement', 'attr':'displacementShader'}],
                },                                                               
        }
    def mat_phong(self):
        return {
            'diffuse': {
                'color':'color',
                'weight':'diffuse'
            },
            'translucency':{
                'weight':'translucence',
            },
            'reflection': {
                'color': 'specularColor',
                'metalness': 'reflectivity',
                'reflectivity': 'reflectedColor',
                },
            'emission': {
                'color': 'incandescence',
                },
            'opacity': {
                'color': 'transparency',
                },
            'bump': {
                'map': [{'type':'bump2d', 'plug':'outNormal', 'attr':'normalCamera'}],
                },
            'displacement': {
                    'map': [{'type':'displacementShader', 'plug':'displacement', 'attr':'displacementShader'}],
                },                                                                  
        }
    def mat_phongE(self):
        return {
            'diffuse': {
                'color':'color',
                'weight':'diffuse'
            },
            'translucency':{
                'weight':'translucence',
            },   
            'reflection': {
                'color': 'specularColor',
                'roughness':'roughness',
                'metalness': 'reflectivity',
                'reflectivity': 'reflectedColor',
                },
            'emission': {
                'color': 'incandescence',
                },
            'opacity': {
                'color': 'transparency',
                },
            'bump': {
                'map': [{'type':'bump2d', 'plug':'outNormal', 'attr':'normalCamera'}],
                },
            'displacement': {
                    'map': [{'type':'displacementShader', 'plug':'displacement', 'attr':'displacementShader'}],
                },                                                      
        }
    def mat_surfaceShader(self):
        return {
            'diffuse': {
                'color':'outColor'
            },
            'opacity': {
                'color': 'outTransparency',
                },              
        }

    def util_bump2d(self):
        return {
            'bump': {
                'map': 'bumpValue',
                'height': 'bumpDepth',
                'type': 'bumpInterp',
            },
        }
    def util_displacementShader(self):
        return {
            'displacement': {
                'map': 'vectorDisplacement',
                'scale': 'scale',
            }
        }
    def util_RedshiftBumpMap(self):
        return {
            'bump': {
                'map': 'input',
                'height': 'scale',
                'type': 'inputType',
            }

        }
    def util_RedshiftDisplacement(self):
        return {
            'displacement': {
                'map': 'texMap',
                'scale': 'scale',
            }

        }        