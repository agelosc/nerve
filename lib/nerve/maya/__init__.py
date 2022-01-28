import os, sys
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

class Node(nerve.Node):
    def __init__(self, **kwargs):
        nerve.Node.__init__(self, **kwargs)

    def SetDataFromScene(self, path=None):
        if path is None:
            path = self.data['path']

        self.data['name'] = path.AsString().split('|')[-1].split(':')[-1]
        self.data['path'] = path
        self.data['type'] = cmds.nodeType(path)
        self.data['app'] = 'maya'
        self.data['classification'] = cmds.getClassification( self.data['type'] )[0]
        self.data['hasParent'] = path.HasParent()
        self.data['parent'] = self.GetParentData()
        self.data['dirty'] = False

    def GetParentData(self):
        path = Path(self.data['path'])
        if not path.HasParent():
            return None
        args = {}
        args['path'] = path.GetParent()
        args['name'] = Path(path.GetHead()).ClearNamespaces()
        args['type'] = cmds.nodeType(self.data['path'])

        return Node(**args).data

    def HasParent(self):
        return self.data['hasParent']

    def GetParent(self):
        return Node( **self.data['parent'] )

    def GetPath(self):
        return self.data['path']

    def Create(self):
        if self.data['type'] not in cmds.allNodeTypes():
            raise Exception('Node type {} is invalid.'.format(self.data['type']))

        if 'shader' in self.data['classification']:
            return cmds.shadingNode(self.data['type'], asShader=True, name=self.data['name'])
        else:
            if not self.HasParent():
                return cmds.createNode(self.data['type'], name=self.data['name'] )

            # Has Parent
            if self.GetParent().Exists():
                return cmds.createNode(self.data['type'], name=self.data['name'], parent=self.GetParent().GetPath() )
            else:
                return self.GetParent().Create()

    def Exists(self):
        return cmds.objExists(self.data['path'])

    @staticmethod
    def GetSelectedNodes():
        sel = cmds.ls(sl=True, l=True)
        nodes = []
        for n in sel:
            nodes.append( Node.node(n) )

        return nodes

    @staticmethod
    def node(path):
        node = Node()
        node.SetDataFromScene(path)
        return node

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

    def Create(self):
        # Create Job
        nerve.Job.Create(self)
        # Add To Recent Jobs
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
        

