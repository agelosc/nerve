import os, sys, json
from re import L
from functools import partial

import nerve

import maya.cmds as cmds
import maya.mel as mel
import maya.utils as mu

log = nerve.log

class Path(nerve.Path):
    def __init__(self, path):
        nerve.Path.__init__(self, path, '|')

    def ClearNamespaces(self):
        path = Path('|'.join(self.segments))
        for i in range(len(path.segments)):
            path.segments[i] = path.segments[i].split(':')[-1]
        return path

def init():
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

    melpath = nerve.Path('$NERVE_LOCAL_PATH/apps/maya/mel')
    cmd = 'source "'+ melpath.AsString() +'/performFileDropAction.mel";'
    mel.eval(cmd)

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

        proj = nerve.Path( job.GetFilePath('job') ) + 'maya'
        if not proj.Exists():
            print('Maya project not found {}.'.format(proj)),
            return False

        os.environ['JOB'] = job.GetFilePath('job').AsString()
        cmds.workspace(proj.AsString(), openWorkspace=True)
        print('Project set to {}.'.format(proj)),
        return True

    def Create(self, addToRecents=True):
        if self.Exists():
            mayapath = self.GetFilePath('job') + 'maya'
            if not mayapath.Exists():
                app = nerve.apps.maya( self.GetFilePath('job') )
                app.Create()

            if addToRecents:
                self.AddToRecent(self.GetFilePath('job'))
            return True

        # Create Job
        nerve.Job.Create(self)
        # Add To Recent Jobs
        if addToRecents:
            self.AddToRecent(self.GetFilePath('job'))
        # Create app directories
        app = nerve.apps.maya( self.GetFilePath('job') )
        app.Create()

        return True

class Node:
    def __init__(self, node):
        self.node = node
        self.data = {}

    @staticmethod
    def GetType(node):
        if cmds.nodeType(node) == 'transform':
            shape = cmds.listRelatives(node, s=True)
            if shape:
                return cmds.nodeType(shape)
            return 'transform'

        return cmds.nodeType(node)

    @staticmethod
    def GetDagTuple(node):
        transform = None
        shape = None
        if cmds.nodeType(node) == 'transform':
            transform = node
            tmp = cmds.listRelatives(transform, s=True)
            if tmp:
                shape = tmp[0]
            
            return (transform, shape)
        else:
            shape = node
            tmp= cmds.listRelatives(shape, p=True)
            if tmp:
                transform = tmp[0]
            return (transform, shape)

    @staticmethod
    def CleanName(name):
        return name.split(':')[-1]

    @staticmethod
    def GetDisplacement(node):
        sgs = Node.GetShadingEngines(node)
        displacement = []
        for sg in sgs:
            con = cmds.listConnections(sg + '.displacementShader')
            if con:
                displacement.append(con)
        return displacement        

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
            
        return []
        
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
    def listHistoryOLD(plug, nodeType, **kwargs):
        history = cmds.listHistory(plug, **kwargs)
        for h in history:
            if cmds.nodeType(h) == nodeType:
                return h
        return False

    @staticmethod
    def findHistory(plug, nodeType):
        con = cmds.listConnections(plug, s=True, d=False) or []
        for c in con:
            if cmds.nodeType(c) == nodeType:
                return c
            return Node.findHistory(c, nodeType)
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

        if atype in ['float', 'double', 'doubleAngle', 'doubleLinear']:
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

        if atype in ['float3', 'double3']:
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

        if atype in ['string']:
            data['value'] = cmds.getAttr(plug) or ''
            data['default'] = cmds.attributeQuery(attr, n=node, listDefault=True) or ''
            data['type'] = 'string'
            return data

        
        #print(plug, atype)
        raise Exception('attribute type not defined:'+ atype)

    @staticmethod
    def AssignMaterial(object, material):
        if not cmds.objExists(object):
            log.error('{} does not exist.'.format(object))
            return False
        if not cmds.objExists(material):
            log.error('{} does not exist.'.format(material))
            return False
            
        sg = cmds.listConnections(material + '.outColor', type='shadingEngine')
        if not sg:
            sgname = material.replace('_M', '') + '_SG'
            sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sgname)
            cmds.connectAttr(material + '.outColor', sg + '.surfaceShader', f=True)
        else:
            sg = sg[0]

        cmds.sets(object, e=True, forceElement=sg)

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
                atype = cmds.getAttr(data['name'] + '.'+ attr, type=True)
                if atype != 'Tdata':
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
        sel = cmds.ls(sl=True)
        return sel

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

        if ntype == 'RedshiftNormalMap':
            tex = cmds.shadingNode('RedshiftNormalMap', asTexture=True, **args)
            uv = cmds.shadingNode('place2dTexture', asUtility=True)
            cmds.connectAttr(uv + '.outUV', tex + '.uvCoord', f=True)
            return tex

        if ntype == 'shadingGroup' or ntype == 'shadingEngine':
            sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, **args)
            return sg

        if cmds.getClassification(ntype, satisfies='shader'):
            return cmds.shadingNode(ntype, asShader=True, **args)
        if cmds.getClassification(ntype, satisfies='utility'):
            return cmds.shadingNode(ntype, asUtility=True, **args)
        if cmds.getClassification(ntype, satisfies='texture'):
            return cmds.shadingNode(ntype, asTexture=True, **args)
        if cmds.getClassification(ntype, satisfies='drawdb/geometry'):
            if 'name' in args.keys():
                name = 'DomeLight_' + args['name']
                shape = name + 'Shape'
                del(args['name'])
                node = cmds.createNode(ntype, name=shape, **args)
                transform = cmds.listRelatives(node, p=True)[0]
                cmds.rename(transform, name)
                return True
            else:
                return cmds.createNode(ntype, **args)
            
        
        return cmds.createNode(ntype, **args)

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

    def ReleaseMaterials(self):
        data = {}
        data['path'] = self.data['path'] + '/materials'
        data['version'] = -1
        mat = Material(**data)
        mat.Release()

    def _ReleaseUI(self, anim=True):
        title = nerve.Format( self.GetFormat() ).GetLong()
        result = cmds.layoutDialog(ui=partial(self._releaseUI, anim), title=title )
        if result == 'Cancel' or result == 'dismiss':
            return False

        #nerve.String.pprint(self.data)
        return self.Release()

    def _GatherUI(self):
        title = nerve.Format( self.GetFormat() ).GetLong()

        result = cmds.layoutDialog(ui=partial(self._gatherUI), title=title)
        if result == 'Cancel' or result == 'dismiss':
            return False

        #nerve.String.pprint(self.data)
        self.Gather(self.data['gatherMethod'])

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
        self.AddGatherMethod('Import', 'Attach', 'Reference', 'Replace', 'Proxy')

        for plugin in ['AbcImport', 'AbcExport']:
            if not cmds.pluginInfo(plugin, q=True, loaded=True):
                cmds.loadPlugin(plugin)

    def Export(self, **kwargs):
        if not len(cmds.ls(sl=True)):
            print('Nothing selected.'),
            return False

        filepath = self.GetFilePath('session')
        if not filepath.GetParent().Exists():
            filepath.GetParent().Create()

        options = ''
        options+= ' -file {}'.format(filepath)
        for n in cmds.ls(sl=True, l=True):
            options+= ' -root {}'.format(n)
        if 'frameRange' in self.data.keys():
            frameRange = self.data['frameRange']
            options+= ' -frameRange {} {}'.format(frameRange[0], frameRange[1])
            
        #options+= ' -dataFormat ogawa'
        options+= ' -stripNamespaces'
        options+= ' -writeVisibility'
        #options+= ' -writeFaceSets'
        options+= ' -renderableOnly'
        options+= ' -eulerFilter'
        #options+= ' -writeUVSets'
        options+= ' -uvWrite'

        panel = cmds.paneLayout('viewPanes', q=True, pane1=True)
        cmds.isolateSelect(panel, state=1)

        cmds.AbcExport(j=options)
        cmds.isolateSelect(panel, state=0)
        
        #print('Asset {} released [Alembic]'.format(self.GetPath())),
        self.Create()
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

    def Attach(self, filepath=None, **kwargs):
        if not filepath:
            filepath = self.GetFilePath('session')
        
        sel = cmds.ls(sl=True, l=True)
        if not len(sel):
            cmds.warning('Nothing selected')
            return False

        args = {}
        args['mode'] = 'import'
        #args['createIfNotFound'] = True
        #args['removeIfNoUpdate'] = True
        for n in sel:
            args['connect'] = n
            return cmds.AbcImport(filepath.AsString(), **args)

    def Import(self, filepath=None, **kwargs):
        if not filepath:
            filepath = self.GetFilePath('session')
        options = {}
        options['type'] = 'Alembic'

        args = {}
        args['groupLocator'] = False
        args['returnNewNodes'] = True
        args['import'] = True
        args['mergeNamespacesOnClash'] = True
        args['options'] = ';'.join( ['{}={}'.format(key, val) for key,val in options.items()] )
        return cmds.file(filepath.AsString(), **args)

    def Proxy(self, filepath=None, **kwargs):
        if not filepath:
            filepath = self.GetFilePath('session')
        
        gpu = Node.create('gpuCache', name=self.GetName() + 'Shape')        
        parent = cmds.listRelatives(gpu, p=True)[0]
        #cmds.rename(parent, self.GetName())
        cmds.gpuCache(gpu, e=True, refresh=True)
        cmds.setAttr(gpu + '.cacheFileName', filepath.AsString(), type='string')
        cmds.gpuCache(gpu, e=True, refresh=True)
        return [parent]

    def Replace(self, filepath=None, **kwargs):
        if filepath is None:
            filepath = self.GetFilePath('session')

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

            return cmds.file(filepath, **args)
        
        # Replace Proxy
        if Node.GetType(sel[0]) == 'gpuCache':
            dag = Node.GetDagTuple(sel[0])
            cmds.setAttr(dag[1] + '.cacheFileName', filepath, type='string')
            return True
        
        cmds.AbcImport(filepath, mode='replace')

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

        if not cmds.pluginInfo('redshift4maya', q=True, loaded=True):
            cmds.loadPlugin('redshift4maya')
    
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

        self.Create()
        return True

    def Import(self, file=None, **kwargs):
        frameRange = None
        if self.HasFrameRange():
            frameRange = self.GetFrameRange()

        if not file:
            if frameRange:
                file = self.GetFilePath('range')
            else:
                file = self.GetFilePath('session')

        proxy = cmds.createNode('RedshiftProxyMesh', name=self.GetName()+'RedshiftProxy', skipSelect=True)
        mesh = cmds.createNode('mesh', name=self.GetName()+'Shape')
        cmds.connectAttr(proxy+'.outMesh', mesh+'.inMesh', f=True)

        trans = cmds.listRelatives(mesh, p=True)[0]
        cmds.setAttr(proxy+'.fileName', file.AsString().format('####'), type='string')
        cmds.setAttr(proxy+'.displayMode', 1)
        if nerve.Path(file).HasFrame():
            cmds.setAttr(proxy+'.useFrameExtension', True)

        cmds.sets(mesh, forceElement='initialShadingGroup')
        if frameRange:
            cmds.setAttr(proxy + '.useFrameExtension', True)

        return trans

    def Replace(self, filepath=None, **kwargs):
        if not filepath:
            filepath = self.GetFilePath('session')

        sel = cmds.ls(sl=True, l=True)
        if not len(sel):
            cmds.warning('Nothing Selected. Skipping Replace...')
            return False

        if Node.GetType(sel[0]) == 'mesh':
            dag = Node.GetDagTuple(sel[0])
            rs = cmds.listConnections( dag[1] + '.inMesh', type='RedshiftProxyMesh') or []
            if len(rs):
               cmds.setAttr(rs[0] + '.fileName', filepath, type='string')
               return True

        return False
        #cmds.warning('Selection is not redshift Proxy. Trying Swaping instead...')
        #nerve.maya.UI.Dialog.ConfirmCancel('Selecton is not a Redsfhit Proxy. Try Swapping Asset?')

    def ReleaseUI(self):
        return self._ReleaseUI(anim=True)

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

        self.Create()
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

        #if self.data['materials']:
        #self.ReleaseMaterials()
        self.Create()
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

    def Import(self, filepath=None, **kwargs):
        if not filepath:
            filepath = self.GetFilePath('session')

        args = {}
        args['type'] = self.type
        args['ignoreVersion'] = True
        args['groupLocator'] = False
        args['import'] = True
        args['options'] = 'v=0'
        args['returnNewNodes'] = True

        root = cmds.ls('|*', l=True, type='transform')
        cmds.file(filepath, **args)
        newnodes = cmds.ls('|*', l=True, type='transform')

        nodes = []
        for nn in newnodes:
            if cmds.nodeType(nn) != 'transform':
                continue
            if nn in root:
                continue
            nodes.append(nn)
        return nodes

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
        self.Create()

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
        self.Create()

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

class MaterialTables:
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
                'type': self.RedshiftReflectionType
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
                'map': self.RedshiftBump
                #'map': [{'type':'RedshiftBumpMap', 'plug':'out', 'attr':'bump_input'}],
                #'height': [{'type':'RedshiftBumpMap'}],
                },
            'displacement': {
                    'map': self.RedshiftDisplacement
                    #'map': [{'type':'RedshiftDisplacement', 'plug':'out', 'attr':'displacementShader'}],
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
                'map': self.MayaBump,
                },
            'displacement': {
                    'map': self.MayaDisplacement,
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
            'bump': {
                'map': 'normal',
                'height': 'displacement',
            },
            'displacement':{
                'map': self.MayaDisplacement
            }

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
                'color': self.Transparency,
                },  
            'bump': {
                'map': self.MayaBump,
                },
            'displacement': {
                    'map': self.MayaDisplacement,
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
                'map': self.MayaBump,
                },
            'displacement': {
                    'map': self.MayaDisplacement,
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
                'color': self.Transparency,
                },
            'bump': {
                'map': self.MayaBump,
                },
            'displacement': {
                    'map': self.MayaDisplacement,
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
                'color': self.Transparency,
                },
            'bump': {
                'map': self.MayaBump,
                },
            'displacement': {
                    'map': self.MayaDisplacement,
                },
        }
    def mat_surfaceShader(self):
        return {
            'diffuse': {
                'color':'outColor'
            },
            'opacity': {
                'color': self.OutTransparency,
                },
            'displacement':{
                'map': self.MayaDisplacement,
            },
        }

    @staticmethod
    def OutTransparency(abstract, grp, abst, conc, material, mode='set'):
        if mode == 'set':
            value = abstract[grp][abst]
            if isinstance(value, dict):
                tex = Material.GetTexture(value)
                inv = Node.create('reverse')
                Node.connectAttr(tex, 'outColor', inv, 'input')
                Node.connectAttr(inv, 'output', material, 'outTransparency')
            else:
                value = (1-value[0], 1-value[1], 1-value[2])
                Node.setAttr(material, 'outTransparency', value)

        if mode == 'get':
            tex = Node.findHistory(material + '.outTransparency', 'file')
            if tex:
                abstract[grp][abst] = Material.SetMayaTexture(tex)
            else:
                value = Node.getAttr(material, 'outTransparency')
                abstract[grp][abst] = (1-value[0], 1-value[1], 1-value[2])

    @staticmethod
    def Transparency(abstract, grp, abst, conc, material, mode='set'):
        if mode == 'set':
            value = abstract[grp][abst]
            if isinstance(value, dict):
                tex = Material.GetTexture(value)
                inv = Node.create('reverse')
                Node.connectAttr(tex, 'outColor', inv, 'input')
                Node.connectAttr(inv, 'output', material, 'transparency')
            else:
                value = (1-value[0], 1-value[1], 1-value[2])
                Node.setAttr(material, 'transparency', value)

        if mode == 'get':
            tex = Node.findHistory(material + '.transparency', 'file')
            if tex:
                abstract[grp][abst] = Material.SetMayaTexture(tex)
            else:
                value = Node.getAttr(material, 'transparency')
                abstract[grp][abst] = (1-value[0], 1-value[1], 1-value[2])

    @staticmethod
    def MayaBump(abstract, grp, abst, conc, material, mode='set'):
        if mode == 'set':
            value = abstract[grp][abst]
            if isinstance(value, dict):
                bump = Node.create('bump2d', value['name'] + '_bump')
                tex = Material.GetTexture(value)
                Node.connectAttr(tex, 'outAlpha', bump, 'bumpValue')
               #Node.setAttr(tex, 'alphaIsLuminance', True)
                Node.connectAttr(bump, 'outNormal', material, 'normalCamera')

                Node.setAttr( bump, 'bumpDepth', abstract[grp]['height'])
                Node.setAttr( bump, 'bumpInterp', abstract[grp]['type'])
        if mode == 'get':
            bump = Node.findHistory(material + '.normalCamera', 'bump2d')
            if bump:
                tex = Node.findHistory(material + '.normalCamera', 'file')
                abstract[grp]['height'] = Node.getAttr(bump, 'bumpDepth')
                abstract[grp]['type'] = Node.getAttr(bump, 'bumpInterp')
                if tex:
                    abstract[grp][abst] = Material.SetMayaTexture(tex)

    @staticmethod
    def MayaDisplacement(abstract, grp, abst, conc, material, mode='set'):
        if mode == 'set':
            value = abstract[grp][abst]
            if isinstance(value, dict):
                sg = cmds.listConnections(material + '.outColor', type='shadingEngine')
                if not sg:
                    sg = Node.create('shadingEngine', name=material+'_SG')
                    Node.connectAttr(material, 'outColor', sg, 'surfaceShader')
                else:
                    sg = sg[0]
                disp = Node.create('displacementShader', name=material+'_disp')
                tex = Material.GetTexture(value)                
                Node.connectAttr(disp, 'displacement', sg, 'displacementShader')
                Node.connectAttr(tex, 'outColor', disp, 'vectorDisplacement')

                Node.setAttr(disp, 'displacement', abstract[grp]['scale'])
        if mode == 'get':
            sg = cmds.listConnections(material+'.outColor', type='shadingEngine')
            if sg:
                sg = sg[0]
                disp = cmds.listConnections(sg + '.displacementShader', type='displacementShader')
                if disp:
                    disp = disp[0]
                    abstract[grp]['scale'] = Node.getAttr(disp, 'displacement')
                    tex = Node.findHistory(disp + '.vectorDisplacement', 'file')
                    if tex:
                        abstract[grp]['map'] = Material.SetMayaTexture(tex)
                    
    @staticmethod
    def RedshiftDisplacement(abstract, grp, abst, conc, material, mode='set'):
        value = abstract[grp][abst]

        if mode == 'set':
            if isinstance(value, dict):
                sg = cmds.listConnections(material + '.outColor', type='shadingEngine')
                if not sg:
                    sg = Node.create('shadingEngine', name=material+'_SG')
                    Node.connectAttr(material, 'outColor', sg, 'surfaceShader')
                else:
                    sg = sg[0]                
                disp = Node.create('RedshiftDisplacement')
                tex = Material.GetTexture(value)
                Node.connectAttr(disp, 'out', sg, 'displacementShader')
                Node.connectAttr(tex, 'outColor', disp, 'texMap')

                Node.setAttr(disp, 'scale', abstract[grp]['scale'])

        if mode == 'get':
            sg = cmds.listConnections(material + '.outColor', type='shadingEngine')
            if sg:
                sg = sg[0]
                disp = cmds.listConnections(sg + '.displacementShader', type='RedshiftDisplacement')
                if disp:
                    disp = disp[0]
                    abstract[grp]['scale'] = Node.getAttr(disp, 'scale')
                    tex = Node.findHistory(disp + '.texMap', 'file')
                    if tex:
                        abstract[grp]['map'] = Material.SetMayaTexture(tex)
    
    @staticmethod
    def RedshiftBump(abstract, grp, abst, conc, material, mode='set'):
        value = abstract[grp][abst]
        if mode == 'set':
            if isinstance(value, dict):
                bump = Node.create('RedshiftBumpMap', value['name'] + '_bump' )
                tex = Material.GetTexture(value)
                Node.connectAttr(tex, 'outColor', bump, 'input')
                Node.connectAttr(bump, 'out', material, 'bump_input')

                Node.setAttr(bump, 'scale', abstract[grp]['height'])
                Node.setAttr(bump, 'inputType', abstract[grp]['type'] )

        if mode == 'get':
            bump = Node.findHistory(material + '.bump_input', 'RedshiftBumpMap')
            if bump:
                tex = Node.findHistory(material + '.bump_input', 'file')
                abstract[grp]['height'] = Node.getAttr(bump, 'scale')
                abstract[grp]['type'] = Node.getAttr(bump,'inputType')
                if tex:
                    abstract[grp][abst] =  Material.SetMayaTexture(tex)

            normal = Node.findHistory(material + '.bump_input', 'RedshiftNormalMap')
            if normal:
                abstract[grp]['height'] = Node.getAttr(normal, 'scale')
                abstract[grp]['type'] = 1
                texdata = Material.texture()
                texdata['name'] = normal
                texdata['filepath'] = Node.getAttr(normal, 'tex0')
                texdata['colorSpace'] = 'Raw'
                uv = cmds.listConnections(normal + '.uvCoord', type='place2dTexture')
                if uv:
                    texdata['uvScale'] = (Node.getAttr(uv, 'repeatU'), Node.getAttr(uv, 'repeatV'))
                    texdata['uvOffset'] = (Node.getAttr(uv, 'offsetU'), Node.getAttr(uv, 'offsetV'))
                    texdata['uvRotate'] = Node.getAttr(uv, 'rotateUV')     
                else:
                    texdata['uvScale'] = (Node.getAttr(normal, 'repeats0'), Node.getAttr(normal, 'repeats1'))

    @staticmethod
    def RedshiftReflectionType(abstract, grp, abst, conc, material, mode='set'):
        # types: 0=IOR, 1=metalness
        if mode == 'set':
            if abstract[grp][abst] == 0:
                Node.setAttr(material, 'refl_fresnel_mode', 3)
                return True
            if abstract[grp][abst] == 1:
                Node.setAttr(material, 'refl_fresnel_mode', 2)
                return True
        if mode == 'get':
            if Node.getAttr(material, 'refl_fresnel_mode') == 3:
                abstract[grp][abst] = 0
                return True
            if Node.getAttr(material, 'refl_fresnel_mode') == 2:
                abstract[grp][abst] = 1
                return True

class Material(nerve.Material, Base, MaterialTables):
    def __init__(self, path='', **kwargs):
        nerve.Material.__init__(self, path, **kwargs)
        self.AddReleaseMethod('Export')
        self.AddGatherMethod('Import')

    def GetFormatObjectOLD(self):
        formatLong = nerve.Format(self.GetFormat()).GetLong()
        module = sys.modules[__name__]
        if not hasattr( module, formatLong ):
            log.error('Module {} does not have a {} object class definition.'.format(__name__, formatLong))
            return False
        return getattr( module, formatLong)(**self.data)

    @staticmethod
    def GetTexture(texdata, grp=''):
        tex = Node.create('file', texdata['name'])
        uv = cmds.listConnections(tex + '.uv')[0]

        Node.setAttr(tex, 'fileTextureName', texdata['filepath'])
        Node.setAttr(tex, 'colorSpace', texdata['colorSpace'])
        Node.setAttr(tex, 'alphaIsLuminance', texdata['alphaIsLuminance'])

        Node.setAttr(uv, 'repeatU', texdata['uvScale'][0])
        Node.setAttr(uv, 'repeatV', texdata['uvScale'][1])
        Node.setAttr(uv, 'offsetU', texdata['uvOffset'][0])
        Node.setAttr(uv, 'offsetV', texdata['uvOffset'][1])
        Node.setAttr(uv, 'rotateUV', texdata['uvRotate'])

        return tex

    @staticmethod
    def SetMayaTexture(node):
        texdata = Material.texture()
        texdata['name'] = node
        texdata['filepath'] = Node.getAttr(node, 'fileTextureName')
        texdata['colorSpace'] = Node.getAttr(node, 'colorSpace')
        texdata['alphaIsLuminance'] = Node.getAttr(node, 'alphaIsLuminance')
        uv = cmds.listConnections(node + '.uv', type='place2dTextyre')
        if uv:
            texdata['uvScale'] = (Node.getAttr(uv, 'repeatU'), Node.getAttr(uv, 'repeatV'))
            texdata['uvOffset'] = (Node.getAttr(uv, 'offsetU'), Node.getAttr(uv, 'offsetV'))
            texdata['uvRotate'] = Node.getAttr(uv, 'rotateUV')

        return texdata
    
    def GetAbstract(self, shader='RedshiftMaterial', name=None):
        if not name:
            name = self.GetName()
        if name not in self.matdata.keys():
            self.SetMaterial(name)

        abstract = self.matdata[name]['abstract']

        material = Node.create(shader, name=name)
        table = self.GetMaterialTable( shader )
        for grp in table.keys():
            for abst, conc in table[grp].items():
                if callable( conc ): # Callable
                    conc(abstract, grp, abst, conc, material, mode='set')
                else: # Standard
                    value = abstract[grp][abst]
                    attrdata = Node.GetAttrData( material, conc )
                    if isinstance( value, dict): # Texture
                        tex = Material.GetTexture(value)
                        if attrdata['type'] == 'vector':
                            Node.connectAttr(tex, 'outColor', material, conc)
                        if attrdata['type'] == 'float':
                            Node.connectAttr(tex, 'outAlpha', material, conc)
                    else:
                        Node.setAttr(material, conc, value)
        
        sg = cmds.listConnections(material + '.outColor', type='shadingEngine')
        if not sg:
            sg = Node.create('shadingEngine', material + '_SG')
            Node.connectAttr(material, 'outColor', sg, 'surfaceShader')
        return material

    def SetAbstract(self, material):
        if material not in self.matdata.keys():
            self.SetMaterial(material)
        
        abstract = self.matdata[material]['abstract']
        table = self.GetMaterialTable( cmds.nodeType(material) )
        for grp in table.keys():
            for abst, conc in table[grp].items():
                if callable( conc ): # Callable
                    conc(abstract, grp, abst, conc, material, mode='get')
                else:
                    attrdata = Node.GetAttrData(material, conc)
                    #if isinstance(abstract[grp][abst], tuple) and isinstance(attrdata['value'], float):
                        #attrdata['value'] = (attrdata['value'], attrdata['value'], attrdata['value'])

                    abstract[grp][abst] = attrdata['value']
                    if 'node' in attrdata.keys():
                        tex = Node.findHistory(material+'.'+conc, 'file')
                        if tex:
                           abstract[grp][abst] = self.SetMayaTexture(tex)

    def SetConcrete(self, material):
        if material not in self.matdata.keys():
            self.SetMaterial( material )
        node = cmds.listConnections(material+'.outColor', type='shadingEngine')
        if node:
            node = node[0]            
        else:
            node = material
        
        self.matdata[material]['concrete'] = Node(node).Serialize()
        
    def GetConcrete(self, material):
        material = Node(material).Unserialize(self.matdata[material]['concrete'])

    def Convert(self, shader):
        sel = cmds.ls(sl=True)
        if not len(sel):
            cmds.warning('Nothing selected')
            return False

        matlist = []
        materials = Node.GetMaterials( sel )
        for material in materials:
            mattype = cmds.nodeType(material)
            if mattype not in self.GetMaterialTypes():
                continue
            if shader == mattype:
                continue

            self.SetAbstract(material)
            mat = self.GetAbstract(shader, material)
            matlist.append(mat)

        return matlist

    def ExportTextures(self):
        for material in self.matdata.keys():
            abstract = self.matdata[material]['abstract']
            concrete = self.matdata[material]['concrete'] if 'concrete' in self.matdata[material].keys() else None
            for grp in abstract.keys():
                for key, value in abstract[grp].items():
                    if isinstance(value, dict):
                        filepath = nerve.Path(value['filepath'])
                        if not filepath.Exists():
                            cmds.warning('Texture path does not exist. Skipping texture export {}'.format(filepath))
                            continue
                        
                        newpath = self.GetFilePath('textures') + (material+'_'+filepath.GetHead())
                        if newpath == filepath:
                            continue
                        if newpath.Exists():
                            cmds.warning('Texture already exists. Skipping texture export {}'.format(newpath))
                            continue

                        filepath.Copy( newpath )
                        print('Copying texture to {}'.format(newpath))
                        name = value['name']
                        # Abstract Repath
                        value['filepath'] = newpath.AsString()
                        # Concrete Repath
                        if concrete and name in concrete['history'].keys():
                            concrete['history'][name]['attr']['fileTextureName']['value'] = newpath.AsString()

    def Export(self, textures=True):
        sel = cmds.ls(sl=True, l=True)
        if len(sel):
            materials = Node.GetMaterials( sel )
            for material in materials:
                self.SetMaterial(material)
                self.SetAbstract(material)
                self.SetConcrete(material)
        
        if textures:
            self.ExportTextures()

        datafile = self.GetFilePath('session')
        if not datafile.GetParent().Exists():
            datafile.GetParent().Create()
        
        with open(datafile.AsString(), 'w') as outfile:
            json.dump(self.matdata, outfile, indent=4)

        self.Create()

    def Import(self, shader='RedshiftMaterial'):
        datafile = self.GetFilePath('session')
        with open(datafile.AsString(), 'r') as infile:
            indata = json.load(infile)

        materials = []
        for name, data in indata.items():
            if 'concrete' in data.keys() and data['concrete']['type'] == shader:
                material = self.GetConcrete(name)
                materials.append( material )
                continue
                
            material = self.GetAbstract(shader)
            materials.append( material )

        return materials

class Texture(nerve.Texture, Base):
    pass

class HDRI(nerve.HDRI, Base):
    def __init__(self, path='', **kwargs):
        nerve.HDRI.__init__(self, path, **kwargs)
        self.AddReleaseMethod('Export')
        self.AddGatherMethod('Import')

    def Export(self):
        sel = cmds.ls(sl=True, l=True)
        if not len(sel):
            log.error('Nothing Selected.')
            return False
        
        sel = sel[0]
        if cmds.nodeType(sel) == 'transform':
            sel = cmds.listRelatives(sel, s=True)
            if not sel:
                log.error('Invalid Selection.')
                return False
            sel = sel[0]
        
        ntype = cmds.nodeType(sel)
        if ntype == 'RedshiftDomeLight':
            tex = nerve.Path(cmds.getAttr(sel + '.tex0'))
            if not tex.Exists():
                log.error('HDRI file does was not found: {}.'.format(tex.AsString()))
                return False
            
            nerve.HDRI.Export(self, tex.AsString())

        log.error('Invalid Selection Type {}'.format(ntype))
        self.Create()
        return False

    def Import(self):
        filepath = self.GetFilePath('session')
        node = Node.create('RedshiftDomeLight', self.GetName())
        

