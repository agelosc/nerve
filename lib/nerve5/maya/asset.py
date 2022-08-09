import maya.cmds as cmds
import maya.mel
import nerve5 as nerve
import nerve5.maya

import os
from functools import partial
from shutil import copyfile
import datetime
import json


# Check Versions
def checkVersions():
    refs = cmds.file(q=True, r=True)
    count = 0
    for ref in refs:

        refNode = cmds.referenceQuery(ref, referenceNode=True)
        if not cmds.referenceQuery(refNode, isLoaded=True):
            continue

        ref = ref.split("{")[0]
        ref = ref.replace('\\', '/')
        tmp = ref.split('/')
        if tmp[-3] == 'assets':
            data = {}
            data['job'] = tmp[2]
            data["seq"] = tmp[3]
            data["shot"] = tmp[4]
            data["type"] = tmp[6]
            data["name"] = tmp[-1].split('.')[0].split('_')[0]

            Class = getattr(nerve.maya.asset, data["type"])
            asset = Class(**data)
            asset.importData()

            if '_v' not in tmp[-1]:
                continue

            version = tmp[-1].split('.')[0]
            t = version.split('_')[0]
            version = version.replace( t, '' )
            version = version.replace('_v', '')
            version = int(version)

            if int(asset['version']) > version:

                nodes = cmds.referenceQuery(refNode, nodes=True, dp=True)
                asset["method"] = 'replace'
                cmds.select(nodes[0], r=True)
                asset.gather()
                count+=1
                continue

    if count:
        print '%s assets were updated'%str(count),
    else:
        print 'all assets are up to date',

def checkVersionsOLD():
    sel = cmds.ls(type="objectSet")
    attributes = ['job', 'seq', 'shot', 'type', 'name', 'date']
    count = 0

    for n in sel:
        if cmds.attributeQuery('version', node=n, exists=True) and cmds.attributeQuery('method', node=n, exists=True):
            if cmds.getAttr(n + '.method') == 'reference':

                data = {}
                for attr in attributes:
                    data[attr] = cmds.getAttr(n + '.' + attr)

                Class = getattr(nerve.maya.asset, data['type'])
                asset = Class(**data)
                asset.importData()

                asset.pprint()
                print ''

                version = int(cmds.getAttr(n + '.version'))

                # Newer version exists
                if int(asset['version']) < version:
                    asset["method"] = 'replace'
                    cmds.select( cmds.sets(n, q=True), r=True )
                    cmds.delete(n)
                    #nerve.maya.asset.gather( **asset.data )
                    asset.gather()
                    count+=1
                    continue

                # Same Version
                assetDate = datetime.datetime.strptime(asset["date"], ' %A %d-%b-%Y %H:%M ' )
                localDate = datetime.datetime.strptime(data["date"], ' %A %d-%b-%Y %H:%M ' )

                # version on disk released after date of gather
                if assetDate > localDate:
                    asset["method"] = 'replace'
                    cmds.select( cmds.sets(n, q=True), r=True)
                    cmds.delete(n)
                    asset.gather()
                    count+=1



    if count:
        print '%s assets were updated'%str(count),
    else:
        print 'all assets are up to date',


# Get Sequence file list from obj's job keys
def currentSequences(obj):
    path = nerve.cfg.path('job') + obj['job'] + '/' + obj['seq'] + '/' + obj['shot'] + '/config/'
    return nerve.sequence.list( path )

# get job from keys or from project path
def resolveJob(kwargs={}):
    jobpath = nerve.cfg.path("job")
    keys = kwargs.keys()
    if 'job' not in keys or 'shot' not in keys or 'seq' not in keys:
        workspace = nerve.maya.projPath()
        workspace = workspace.replace( jobpath, '')

        tmp = workspace.split('/')
        kwargs['job'] = tmp[0]
        kwargs['seq'] = tmp[1]
        kwargs['shot'] = tmp[2]

    return kwargs

# Set default option to first value if not already set
def setDefaultOptions(obj):
    for key in obj.options.keys():
        if key not in obj.data.keys():
            obj.data[key] = obj.options[key][0]


def setFromUI(*args):
    obj = args[0]
    key = args[1]
    ctrl = obj.ctrl[args[2]]
    type = args[3]

    if type == 'intField':
        obj[key] = cmds.intField(ctrl, q=True, value=True)

def addField(obj, type, key, **kwargs):

    obj.field[key] = {}
    obj.field[key]['type'] = type

    if type == 'int':
        obj.field[key]['ctrl'] = cmds.intField( value=obj[key], **kwargs )

    if type == 'optionMenu':
        obj.field[key]['ctrl'] = cmds.optionMenu(**kwargs )

    if type == 'textScrollList':
        obj.field[key]['ctrl'] = cmds.textScrollList( **kwargs )

    return obj.field[key]['ctrl']


def setFields(obj):
    if obj.field:
        for key in obj.field.keys():
            field  = obj.field[key]

            if field['type'] == 'int':
                obj[key] = cmds.intField(field["ctrl"], q=True, value=True)
            if field['type'] == 'optionMenu':
                obj[key] = cmds.optionMenu(field['ctrl'], q=True, value=True)
            if field['type'] == 'textScrollList':
                obj[key] = cmds.textScrollList( field['ctrl'], q=True, selectItem=True)

def defaultUI(obj, ui):
    # UI Functions [start]

    def refreshArgs(*args):
        args[0][args[1]] = args[2]

    def doit(*args):
        setFields(args[0])
        if args[0].has('sseq') and not args[0].has('sshot'):
            nerve.maya.error('shot not selected')
            return False

        cmds.layoutDialog(dismiss="OK")

    def cancel(*args):
        cmds.layoutDialog(dismiss="Cancel")

    def refreshSeq(*args):
        obj = args[0]

        # Try and Get Existing Asset
        Class = getattr(nerve.maya.asset, obj['type'])
        keys = ['job', 'seq', 'shot', 'type', 'name', 'version']
        d = {}
        for k in keys:
            d[k] = obj[k]

        print obj['version']
        asset = Class(**d)
        asset.importData()

        # SEQ
        ctrl = obj.ctrl['sseq']

        selection = cmds.textScrollList(ctrl, query=True, selectItem=True)
        cmds.textScrollList(ctrl, edit=True, removeAll=True)

        names = []
        sequences = {}
        files = []

        # Asset [start]

        # Asset Exists
        if 'sseq' in asset.keys():
            # Asset does not have sseq set
            if asset["sseq"] is None:
                obj['sseq'] = '<None>' if selection is None else str(selection[0])
                names.append('<None>')
                cmds.textScrollList(ctrl, edit=True, append='<None>');
            # Asset has Sseq set
            else:
                obj['sseq'] = asset['sseq'] if selection is None else str(selection[0])
                tmp = currentSequences(obj)
                for t in tmp:
                    #name = t.split('/')[-1].split('_')[-1].replace('.json', '')
                    name = t.split('/')[-1]
                    name = '_'.join(name.split('_')[1:])
                    name = name.replace('.json', '')
                    #if name == asset['sseq']:
                    files.append(t)
                    #break
        # Asset does not exist
        else:
            obj['sseq'] = '<None>' if selection is None else str(selection[0])
            names.append('<None>')
            cmds.textScrollList(ctrl, edit=True, append='<None>');
            files = currentSequences(obj)
        # Asset [end]

        for file in files:
            #name = file.split('/')[-1].split('_')[-1].replace('.json', '')
            name = file.split('/')[-1]
            name = '_'.join(name.split('_')[1:])
            name = name.replace('.json', '')

            sequences[name] = file
            names.append(name)
            cmds.textScrollList(ctrl, edit=True, append=name)

        if obj['sseq'] in names:
            cmds.textScrollList(ctrl, edit=True, selectItem=obj['sseq'])

        if obj['sseq'] == '<None>':
            obj['sseq'] = None

        # SHOT
        ctrl = obj.ctrl['sshot']
        if obj.has('sseq'):
            obj['sshot'] = []

            # load active sequence
            seq = nerve.sequence( sequences[ obj['sseq'] ] )
            seq.load()

            # Get current frameRange
            min = cmds.playbackOptions(q=True, min=True)
            max = cmds.playbackOptions(q=True, max=True)

            # get scroll list selection
            selection = cmds.textScrollList(ctrl, query=True, selectItem=True)

            if selection is None:
                # Select Current Shot
                for shot in seq["shots"]:
                    if shot["startFrame"] == min and shot["endFrame"] == max:
                        obj['sshot'].append( shot )
            else:
                for sel in selection:
                    obj['sshot'].append( seq.getShotByName( str(sel) ) )

            cmds.textScrollList(ctrl, edit=True, removeAll=True)
            shots = []

            c = 1
            for shot in seq["shots"]:
                shotName = seq.shotName(shot)
                shots.append(shotName)

                if obj['mode'] == 'release':
                    cmds.textScrollList(ctrl, edit=True, append=shotName)

                # Highlight existing shots
                if asset.has('sseq') and asset['sseq'] == obj['sseq']:
                    for assetShot in asset['sshot']:
                        if shotName == seq.shotName(assetShot):
                            cmds.textScrollList(ctrl, edit=True, lineFont=[c, 'boldLabelFont'])
                            if obj["mode"] == 'gather':
                                cmds.textScrollList(ctrl, edit=True, append=shotName)


                c+=1

            for shot in obj['sshot']:
                if seq.shotName( shot ) in shots:
                    cmds.textScrollList(ctrl, edit=True, selectItem=seq.shotName(shot))
        else:
            cmds.textScrollList(ctrl, edit=True, removeAll=True)

    # UI Functions [end]

    form = cmds.setParent(q=True)
    width = 400
    cmds.formLayout(form, e=True, width=width)

    cmds.columnLayout()
    # MULTI UI
    if obj.settings["multi"]:
        cmds.frameLayout(label='Sequence/Shot', marginHeight=10, marginWidth=10, font="boldLabelFont", width=width-2)

        cmds.rowColumnLayout(numberOfRows=1, height=170)
        twidth = 189
        obj.ctrl['sseq'] = cmds.textScrollList( height=170, width=twidth, numberOfRows=5, allowMultiSelection=False, font="plainLabelFont", selectCommand=partial(refreshSeq, obj))
        obj.ctrl['sshot'] = cmds.textScrollList( height=170, width=twidth,  numberOfRows=5, allowMultiSelection=True, font="plainLabelFont", selectCommand=partial(refreshSeq, obj))
        cmds.setParent('..')
        cmds.setParent('..')
        refreshSeq( obj )

    # CUSTOM UI
    ui()

    # GENERIC OPTIONS
    if len(obj.options):
        cmds.frameLayout(label='Options', marginHeight=10, marginWidth=10, font="boldLabelFont", width=width-2)
        # Controls
        for key in obj.options.keys():
            values = obj.options[key]

            # Radio Buttons
            if len(values) <= 4 :
                cmds.rowColumnLayout( numberOfRows=1 , columnOffset=[1, "right", 40])
                cmds.text(label=nerve.uncamelCase(key))
                obj.ctrl[key] = cmds.radioCollection()
                buttons = {}
                for i in range(len(values)):
                    buttons[values[i]] = cmds.radioButton(label=values[i])
                    cmds.radioButton( buttons[values[i]], edit=True, onCommand=partial( refreshArgs, obj, key, values[i] ) )
                cmds.setParent("..")
                cmds.radioCollection(obj.ctrl[key], edit=True, select=buttons[ obj.data[key] ])
            else:
                # Option Menu
                cmds.rowColumnLayout( numberOfRows=1, columnOffset=[1, "right", 40])

                cmds.text(label=nerve.uncamelCase(key))
                obj.ctrl[key] = cmds.optionMenu()

                for v in values:
                    cmds.menuItem( p=obj.ctrl[key],  label=v)

                for i in range(0, len(values) ):
                    if obj.data[key] == values[i]:
                        cmds.optionMenu(obj.ctrl[key], edit=True, select=i+1)

                cmds.optionMenu(obj.ctrl[key], edit=True, changeCommand=partial( refreshArgs, obj, key ) )
                cmds.setParent("..")

            cmds.setParent("..")

    # Buttons
    #cmds.columnLayout()
    cmds.separator(style='in')
    cmds.frameLayout(labelVisible=False, marginHeight=10, marginWidth=10, font="boldLabelFont", width=width-2, )

    if True:
        cmds.rowColumnLayout(numberOfRows=1)

        bwidth = 182
        cmds.button(label="OK", width=bwidth, height=50, command=partial(doit, obj))
        cmds.text(label='', width=10)
        cmds.button(label="Cancel", width=bwidth, height=50, command=cancel)
        cmds.setParent('..')

    cmds.setParent('..')


def createSet(obj, nodes, name=None):
    if name is None:
        name = obj['type'] + '_' + obj['name']
        name = str(name).upper()

    if len(cmds.ls(name, sets=True)):
        cmds.delete(name)
    set = cmds.sets(nodes, name=name)

    for key in obj.keys():
        cmds.addAttr( set, ln=key, dt='string')
        cmds.setAttr( set + '.' + key, str(obj[key]), type='string' )
        cmds.setAttr( set + '.' + key, lock=True)

def getNamespace(obj):
    # Namespace
    namespace = obj["type"] + '_' + obj["name"]
    original = namespace

    # increment namespace
    if cmds.namespace(exists=original):
        c = 1
        while cmds.namespace(exists=namespace):
            namespace = original + '_' + str(c).zfill(2)
            c = c + 1

    return str(namespace).upper()
    #return namespace

# RELEASE
def release(ui=False, **kwargs):
    kwargs = resolveJob(kwargs)

    if 'name' not in kwargs.keys():
        nerve.error('Name not set.')
    if 'type' not in kwargs.keys():
        nerve.error('Type not set.')

    Class = getattr(nerve.maya.asset, kwargs['type'])
    obj = Class(**kwargs)

    # Thumbnail
    if obj.has('thumb'):
        if os.path.exists( obj["thumb"] ):
            ext = obj["thumb"].split('.')[-1]
            path = obj.datapath() + obj.datafile().replace('.json', '.' + ext)
            copyfile( obj["thumb"], path )
            obj["thumb"] = path
    # UI
    if obj.has("ui"):
        obj.ui = obj["ui"]
        del(obj.data["ui"])

    if ui:
        obj.ui = True

    # Date
    import datetime
    obj["date"] = datetime.datetime.now().strftime( ' %A %d-%b-%Y %H:%M ' )

    # From
    import getpass
    import socket
    obj["from"] = getpass.getuser() + '@' + socket.gethostname()

    if obj.release():
        obj.exportData()

    return obj

# GATHER
def gather(**kwargs):
    kwargs = resolveJob(kwargs)

    if 'name' not in kwargs.keys():
        nerve.error('Name not set.')
    if 'type' not in kwargs.keys():
        nerve.error('Type not set.')

    Class = getattr(nerve.maya.asset, kwargs['type'])
    obj = Class(**kwargs)

    # UI
    if obj.has('ui'):
        obj.ui = obj.data['ui']
        del(obj.data['ui'])

    #obj.ui = True # debug
    obj.importData()
    return obj.gather()


class model(nerve.assetBase):
    def __init__(self,**kwargs):
        nerve.assetBase.__init__(self)
        self.data = kwargs

        # Defaults
        self.default('fileType', 'mayaBinary')
        self.default('method', 'import')

        # Settings
        self.settings = {}
        self.settings['multi'] = False

        # Options
        self.options = {}

        self.field = {}

        # UI
        self.ui = False
        self.ctrl = {}

    # path
    def filepath(self):
        self["path"] = self.datapath()
        return self["path"]

    # filename
    def filename(self):
        filename = self['name']
        filename+= self.versionStr()
        filename+= '.' + self['extension']

        self["filename"] = filename
        return filename

    def releaseUI(self):
        pass

    def gatherUI(self):
        pass

    def release(self):
        # UI
        if self.ui:
            # Options
            self.options["fileType"] = ['mayaBinary', 'mayaAscii', 'obj']
            self['mode'] = 'release'
            result = cmds.layoutDialog( ui=partial(defaultUI, self, self.releaseUI ) )
            if result == 'Cancel' or result == 'dismiss':
                print 'Release Canceled...',
                return False

        # New version
        if not self.has('version'):
            self["version"] = self.latestVersion()+1

        # RELEASE
        # maya export
        if self["fileType"] == 'mayaAscii' or self['fileType'] == 'mayaBinary':
            # extension
            self["extension"] = 'ma' if self["fileType"] == 'mayaAscii' else 'mb'
            filepath = self.filepath() + self.filename()
            cmds.file( filepath, options='v=0', type=self["fileType"], preserveReferences=True, exportSelected=True, force=True )
        # obj export
        if self['fileType'] == 'obj':
            self['extension'] = 'obj'
            filepath = self.filepath() + self.filename()
            cmds.file( filepath, options='groups=1;ptgroups=1;materials=1;smoothing=1;normals=1', type="OBJexport", preserveReferences=True, exportSelected=True, force=True)

        nerve.maya.confirm('Asset Released', 'Release')
        return True

    def gather(self):
        # UI
        if self.ui:
            # Options
            self.options['method'] = ['import', 'reference', 'replace']
            #setDefaultOptions(self)
            self['mode'] = 'gather'
            result = cmds.layoutDialog( ui=partial( defaultUI, self, self.gatherUI ) )
            if result == 'Cancel' or result == 'dismiss':
                print 'Gather Canceled...',
                return False

        # GATHER
        options = 'v=0'
        if self['fileType'] == 'obj':
            options = 'mo=1'
        filepath = self.filepath() + self.filename()

        # Import
        if self['method'] == 'import':
            nodes = cmds.file(filepath, i=True, type=self['fileType'], options=options, preserveReferences=True, defaultNamespace=True, mergeNamespacesOnClash=True, returnNewNodes=True)
            #createSet(self, nodes)
        # Reference
        if self['method'] == 'reference':
            namespace = getNamespace(self)
            nodes = cmds.file(filepath, reference=True, type=self["fileType"], sharedNodes="renderLayersByName", options=options, namespace=namespace, returnNewNodes=True )
            createSet(self, nodes, namespace)
        # Replace
        if self['method'] == 'replace':
            sel = cmds.ls(sl=True)
            if len(sel) == 0:
                nerve.maya.error( 'Nothing selected to replace' )
                return False

            if cmds.referenceQuery( sel[0], isNodeReferenced=True ):
                referenceNode = cmds.referenceQuery(sel[0], referenceNode=True)
                namespace = cmds.referenceQuery(sel[0], namespace=True)
                nodes = cmds.file(filepath, loadReference=referenceNode, type=self["fileType"], returnNewNodes=True, options=options)
                createSet(self, nodes, namespace)
            else:
                nerve.maya.error("Cannot replace asset. Selection is not a reference.")
                return False

class camera(nerve.assetBase):
    def __init__(self,**kwargs):
        nerve.assetBase.__init__(self)
        self.data = kwargs

        # Defaults
        self.default('fileType', 'mayaBinary')
        self.default('method', 'import')

        # Settings
        self.settings = {}
        self.settings['multi'] = True

        # Options
        self.options = {}

        self.field = {}

        # UI
        self.ui = False
        self.ctrl = {}

    # path
    def filepath(self):
        self['path'] = self.datapath()

        if self.has('sseq') and self.has('sshot'):
            vstr = self.versionStr()
            if vstr == '':
                self['path']+=self['name'] + '/'
            else:
                self['path']+=self['name'] + vstr + '/'

            self['path']+=self['sseq'] + '/'

            if not os.path.exists(self['path']):
                os.makedirs(self['path'])

        return self["path"]

    # filename
    def filename(self, shot=None):
        if self.has('sseq') and self.has('sshot'):
            #validate
            if shot is None:
                nerve.error('camera.filename() argument error')
                return False

            filename = 'S'+str(shot['order']).zfill(3)
            filename+= '.' + self['extension']
        else:
            filename = self['name']
            filename+= self.versionStr()
            filename+= '.' + self['extension']

        self["filename"] = filename
        return filename

    def releaseUI(self):
        pass

    def gatherUI(self):
        pass

    def getCameraList(self):
        defaultCameras = ['frontShape', 'perspShape', 'sideShape', 'topShape']
        sel = cmds.ls(sl=True, l=True)

        # nothing selected
        if not len(sel):
            # get scene cameras
            sel = cmds.ls(type='camera')

            notDefault = []
            for n in sel:
                if n not in defaultCameras:
                    notDefault.append(n)

            if len(notDefault) == 1:
                return [notDefault[0]]

            nerve.error('No camera selected')

        # selected
        cameras = []
        for n in sel:
            if cmds.nodeType(n) == 'camera':
                return cmds.listRelatives( n, parent=True )
            else:
                childCams = cmds.listRelatives(n, allDescendents=True, type='camera')
                if childCams is None:
                    nerve.error( 'Selection has no cameras' )
                for childCam in childCams:
                    cameras.append(  cmds.listRelatives( childCam, parent=True )[0] )
                return cameras

    def release(self):
        # UI
        if self.ui:
            # Options
            self.options["fileType"] = ['mayaBinary', 'mayaAscii', 'alembic' ]

            result = cmds.layoutDialog( ui=partial(defaultUI, self, self.releaseUI ) )
            if result == 'Cancel' or result == 'dismiss':
                print 'Release Canceled...',
                return False

        # New version
        if not self.has('version'):
            self["version"] = self.latestVersion()+1

        cameras = self.getCameraList()
        cmds.select(cameras, r=True)


        # RELEASE MULTI
        if self.has('sseq') and self.has('sshot'):
            # save playbackrange
            minFrame = cmds.playbackOptions(q=True, min=True)
            maxFrame = cmds.playbackOptions(q=True, max=True)

            for shot in self['sshot']:
                cmds.playbackOptions(e=True, min=int(shot["startFrame"]))
                cmds.playbackOptions(e=True, max=int(shot["endFrame"]))

                self.releaseByType(cameras, shot)

            cmds.playbackOptions(e=True, min=minFrame)
            cmds.playbackOptions(e=True, max=maxFrame)
        # RELEASE SINGLE
        else:
            self.releaseByType(cameras)


        nerve.maya.confirm('Asset Released', 'Release')
        return True

    def releaseSetExtension(self):
        # maya export
        if self["fileType"] == 'mayaAscii' or self['fileType'] == 'mayaBinary':
            self["extension"] = 'ma' if self["fileType"] == 'mayaAscii' else 'mb'
        # Alembic
        if self['fileType'] == 'alembic':
            self['extension'] = 'abc'

    def releaseByType(self, cameras, shot=None):

        def isFileInUse(filename):
            if os.path.exists(filename):
                try:
                    os.rename(filename, filename)
                except OSError as e:
                    msg = 'File is being used: "' + filename + '"! \n' + str(e)
                    nerve.error(msg)
                    return True

            return False
        # isFileInUse() END

        # Filepath
        self.releaseSetExtension()
        filepath = self.filepath() + self.filename(shot)

        # maya export
        if self["fileType"] == 'mayaAscii' or self['fileType'] == 'mayaBinary':
            cmds.file( filepath, options='v=0', type=self["fileType"], preserveReferences=True, exportSelected=True, force=True )

        if self['fileType'] == 'alembic':
            if isFileInUse(filepath):
                return False

            objects = ','.join( cameras )
            # Camera Arguments
            args = []
            args.append( 'filename=%s'%filepath )
            args.append( 'objects=%s'%objects )
            args.append( 'in=%s'%str(shot["startFrame"]) )
            args.append( 'out=%s'%str(shot["endFrame"]) )
            args.append( 'uvs=0;ogawa=1;step=1;purepointcache=0' )
            args.append( 'dynamictopology=0;normals=1;facesets=0;globalspace=0;withouthierarchy=0;transformcache=0' )
            command = ';'.join(args)

            cmds.ExocortexAlembic_export(j=[command])


    def gather(self):
        # UI
        if self.ui:
            # Options
            self.options['method'] = ['import', 'reference', 'replace']
            #setDefaultOptions(self)

            result = cmds.layoutDialog( ui=partial( defaultUI, self, self.gatherUI ) )
            if result == 'Cancel' or result == 'dismiss':
                print 'Gather Canceled...',
                return False

        # GATHER
        options = 'v=0'
        if self['fileType'] == 'obj':
            options = 'mo=1'
        filepath = self.filepath() + self.filename()

        # Import
        if self['method'] == 'import':
            nodes = cmds.file(filepath, i=True, type=self['fileType'], options=options, preserveReferences=True, defaultNamespace=True, mergeNamespacesOnClash=True, returnNewNodes=True)
            createSet(self, nodes)
        # Reference
        if self['method'] == 'reference':
            namespace = getNamespace(self)
            nodes = cmds.file(filepath, reference=True, type=self["fileType"], sharedNodes="renderLayersByName", options=options, namespace=namespace, returnNewNodes=True )
            createSet(self, nodes, namespace)
        # Replace
        if self['method'] == 'replace':
            sel = cmds.ls(sl=True)
            if len(sel) == 0:
                nerve.maya.error( 'Nothing selected to replace' )
                return False

            if cmds.referenceQuery( sel[0], isNodeReferenced=True ):
                referenceNode = cmds.referenceQuery(sel[0], referenceNode=True)
                namespace = cmds.referenceQuery(sel[0], namespace=True)
                nodes = cmds.file(filepath, loadReference=referenceNode, type=self["fileType"], returnNewNodes=True, options=options)
                createSet(self, nodes, namespace)
            else:
                nerve.maya.error("Cannot replace asset. Selection is not a reference.")
                return False


class rig(nerve.assetBase):
    def __init__(self,**kwargs):
        nerve.assetBase.__init__(self)
        self.data = kwargs

        # Defaults
        self.default('fileType', 'mayaBinary')
        self.default('method', 'reference')

        # Settings
        self.settings = {}
        self.settings['multi'] = False

        # Options
        self.options = {}

        self.field = {}

        # UI
        self.ui = False
        self.ctrl = {}

    # path
    def filepath(self):
        self["path"] = self.datapath()
        return self["path"]

    # filename
    def filename(self):
        filename = self['name']
        filename+= self.versionStr()
        filename+= '.' + self['extension']

        self["filename"] = filename
        return filename

    def releaseUI(self):
        pass

    def gatherUI(self):
        pass

    def release(self):
        # UI
        if self.ui:
            # Options
            self.options["fileType"] = ['mayaBinary', 'mayaAscii']

            result = cmds.layoutDialog( ui=partial(defaultUI, self, self.releaseUI ) )
            if result == 'Cancel' or result == 'dismiss':
                print 'Release Canceled...',
                return False

        # New version
        if not self.has('version'):
            self["version"] = self.latestVersion()+1

        # RELEASE
        # maya export
        if self["fileType"] == 'mayaAscii' or self['fileType'] == 'mayaBinary':
            # extension
            self["extension"] = 'ma' if self["fileType"] == 'mayaAscii' else 'mb'
            filepath = self.filepath() + self.filename()
            cmds.file( filepath, options='v=0', type=self["fileType"], preserveReferences=True, exportSelected=True, force=True )

        nerve.maya.confirm('Asset Released', 'Release')
        return True

    def gather(self):
        # UI
        if self.ui:
            # Options
            self.options['method'] = ['import', 'reference', 'replace']
            #setDefaultOptions(self)

            result = cmds.layoutDialog( ui=partial( defaultUI, self, self.gatherUI ) )
            if result == 'Cancel' or result == 'dismiss':
                print 'Gather Canceled...',
                return False

        # GATHER
        options = 'v=0'
        if self['fileType'] == 'obj':
            options = 'mo=1'
        filepath = self.filepath() + self.filename()

        # Import
        if self['method'] == 'import':
            nodes = cmds.file(filepath, i=True, type=self['fileType'], options=options, preserveReferences=True, defaultNamespace=True, mergeNamespacesOnClash=True, returnNewNodes=True)
            createSet(self, nodes)
        # Reference
        if self['method'] == 'reference':
            namespace = getNamespace(self)
            nodes = cmds.file(filepath, reference=True, type=self["fileType"], sharedNodes="renderLayersByName", options=options, namespace=namespace, returnNewNodes=True )
            createSet(self, nodes, namespace)
        # Replace
        if self['method'] == 'replace':
            sel = cmds.ls(sl=True)
            if len(sel) == 0:
                nerve.maya.error( 'Nothing selected to replace' )
                return False

            if cmds.referenceQuery( sel[0], isNodeReferenced=True ):
                referenceNode = cmds.referenceQuery(sel[0], referenceNode=True)
                namespace = cmds.referenceQuery(sel[0], namespace=True)
                nodes = cmds.file(filepath, loadReference=referenceNode, type=self["fileType"], returnNewNodes=True, options=options)
                createSet(self, nodes, namespace)
            else:
                nerve.maya.error("Cannot replace asset. Selection is not a reference.")
                return False

class animation(nerve.assetBase):
    def __init__(self,**kwargs):
        nerve.assetBase.__init__(self)
        self.data = kwargs

        # Defaults
        self.default('fileType', 'mayaBinary')
        self.default('method', 'reference')

        # Settings
        self.settings = {}
        self.settings['multi'] = True

        # Options
        self.options = {}

        self.field = {}

        # UI
        self.ui = False
        self.ctrl = {}

    # path
    def filepath(self):
        path = self.datapath()
        if self.has('sseq') and self.has('sshot'):
            vstr = self.versionStr()
            if vstr == '':
                path+= self['name'] + '/'
            else:
                path+= self['name'] + vstr + '/'

            path+= self['sseq'] + '/'

        self["path"] = path

        if not os.path.exists(path):
            os.makedirs(path)
        return path

        '''
        self["path"] = self.datapath()
        return self["path"]
        '''

    # filename
    def filename(self, shot=None):
        if self.has('sseq') and self.has('sshot'):
            # validate
            if shot is None:
                nerve.error('animation.filename() argument error.')
                return False

            filename = 'S'+str(shot["order"]).zfill(3)
            filename+= '.' + self['extension']
        else:
            filename = self['name']
            filename+= self.versionStr()
            filename+= '.' + self['extension']

        self["filename"] = filename
        return filename

        '''
        filename = self['name']
        filename+= self.versionStr()
        filename+= '.' + self['extension']

        self["filename"] = filename
        return filename
        '''

    def releaseUI(self):
        pass

    def gatherUI(self):
        pass

    def release(self):
        # UI
        if self.ui:
            # Options
            self.options["fileType"] = ['mayaBinary', 'mayaAscii']

            result = cmds.layoutDialog( ui=partial(defaultUI, self, self.releaseUI ) )
            if result == 'Cancel' or result == 'dismiss':
                print 'Release Canceled...',
                return False

        # New version
        if not self.has('version'):
            self["version"] = self.latestVersion()+1

        # extension
        self["extension"] = 'ma' if self["fileType"] == 'mayaAscii' else 'mb'

        # RELEASE
        if self.has('sseq') and self.has('sshot'):
            # Multi Export
            for shot in self['sshot']:
                filepath = self.filepath() + self.filename(shot)
                cmds.file( filepath, options='v=0', type=self["fileType"], preserveReferences=True, exportSelected=True, force=True )
        else:
            # Normal Export
            filepath = self.filepath() + self.filename()
            cmds.file( filepath, options='v=0', type=self["fileType"], preserveReferences=True, exportSelected=True, force=True )

        nerve.maya.confirm('Asset Released', 'Release')
        return True

    def gather(self):
        def doIt(filepath):
            nodes = []
            # Import
            if self['method'] == 'import':
                nodes = cmds.file(filepath, i=True, type=self['fileType'], options=options, preserveReferences=True, defaultNamespace=True, mergeNamespacesOnClash=True, returnNewNodes=True)
                createSet(self, nodes)
            # Reference
            if self['method'] == 'reference':
                namespace = getNamespace(self)
                nodes = cmds.file(filepath, reference=True, type=self["fileType"], sharedNodes="renderLayersByName", options=options, namespace=namespace, returnNewNodes=True )
                createSet(self, nodes, namespace)
            # Replace
            if self['method'] == 'replace':
                sel = cmds.ls(sl=True)
                if len(sel) == 0:
                    nerve.maya.error( 'Nothing selected to replace' )
                    return False

                if cmds.referenceQuery( sel[0], isNodeReferenced=True ):
                    referenceNode = cmds.referenceQuery(sel[0], referenceNode=True, topReference=True)
                    namespace = cmds.referenceQuery(sel[0], namespace=True)
                    nodes = cmds.file(filepath, loadReference=referenceNode, type=self["fileType"], returnNewNodes=True, options=options)
                    createSet(self, nodes, namespace)
                else:
                    nerve.maya.error("Cannot replace asset. Selection is not a reference.")
                    return False

            return nodes



        # UI
        if self.ui:
            # Options
            self.options['method'] = ['import', 'reference', 'replace']
            #setDefaultOptions(self)

            result = cmds.layoutDialog( ui=partial( defaultUI, self, self.gatherUI ) )
            if result == 'Cancel' or result == 'dismiss':
                print 'Gather Canceled...',
                return False

        nodes = []
        # GATHER
        options = 'v=0'
        if self['fileType'] == 'obj':
            options = 'mo=1'

        # Multi
        if self.has('sseq') and self.has('sshot'):
            for shot in self['sshot']:
                filepath = self.filepath() + self.filename(shot)
                nodes = doIt(filepath)
        else:
            filepath = self.filepath() + self.filename()
            nodes = doIt(filepath)

        return nodes

class alembic(nerve.assetBase):
    def __init__(self, **kwargs):
        nerve.assetBase.__init__(self)
        self.data = kwargs

        # Defaults
        self.default('method', 'import')

        # Settings
        self.settings = {}
        self.settings['multi'] = True

        # Options
        self.options = {}
        self.field = {}

        # UI
        self.ui = True
        self.ctrl = {}

    def getObjects(self, olist=None, shape=False):
        # Shape Arg is used to gather shading Data

        if olist is None:
            olist = self['objlist']
        else:
            olist = [olist]


        # Mesh
        objlist = []
        for obj in olist:
            children = cmds.listRelatives(obj, ad=True, ni=True, f=True, type="mesh")
            for child in children:
                # Skip Intermediate Objects
                if cmds.getAttr(child + '.intermediateObject'):
                    continue

                if shape:
                    if shape not in objlist:
                        objlist.append(child)
                else:
                    getParent = cmds.listRelatives(child, p=True, ni=True, f=True)[0]
                    if getParent not in objlist:
                        objlist.append(getParent)


        # Curves
        for obj in olist:
            children = cmds.listRelatives(obj, ad=True, ni=True, f=True, type="nurbsCurve")
            if children is None:
                continue
            for child in children:
                # Skip Intermiediate Objects
                if cmds.getAttr(child + '.intermediateObject'):
                    continue

                getParent = cmds.listRelatives(child, p=True, ni=True, f=True)[0]
                getGroup = cmds.listRelatives(getParent, p=True, ni=True, f=True)
                if getGroup is not None:
                    if getGroup[0] not in objlist:
                        objlist.append( getGroup[0] )
                else:
                    if getParent not in objlist:
                        objlist.append( getParent )


        return objlist

    def getShadingDataFileOLD(self, filepath):
        return filepath[:-4] + '_Shading.data'

    def getShadingDataFile(self, filepath):
        return filepath[:-4] + '_Style.data'

    def getShadingFile(self, filepath):
        return filepath[:-4] + '_Shading.ma'

    def releaseUI(self):
        def resolveName(n):
            obj = cmds.ls(n, r=True, l=True)[0]
            tmp = ''
            if '|' in obj:
                tmp = obj.split('|')[1]
            tmp = tmp.split(':')[0]
            return tmp
            tmp = tmp.replace('_', ' ')
            tmp = nerve.uncamelCase(tmp)
            tmp = tmp.replace(' ', '')
            return tmp

        def refresh(*args):
            patternText = cmds.textField(self.ctrl['pattern'], q=True, text=True)
            if patternText == '*':
                return False

            buffer = patternText.split(',')

            cmds.textScrollList(self.ctrl['objlist'], e=True, removeAll=True)
            cmds.textScrollList(self.ctrl['namelist'], e=True, removeAll=True)
            self['objlist'] = []
            self['objlistsel'] = []
            self['namelist'] = []

            for pattern in buffer:
                sel = cmds.ls(pattern, r=True, type='transform')
                for n in sel:
                    name = resolveName(n)
                    cmds.textScrollList(self.ctrl['objlist'], e=True, append=n )
                    self['objlist'].append( n )
                    cmds.textScrollList(self.ctrl['namelist'], e=True, append=name)
                    self['namelist'].append( name )

                    cmds.textScrollList(self.ctrl['namelist'], e=True, enable=self['separate'])

            '''
            self['objlistsel'] = cmds.textScrollList( self.ctrl['objlist'], q=True, selectItem=True )
            if self['objlistsel'] is None:
                self['objlistsel'] = []
            '''
            # END refresh()

        def populateObjListSel(*args):
            ctrl = self.ctrl['objlist']
            self['objlistsel'] = cmds.textScrollList( ctrl, q=True, selectItem=True )

        def fromSel(*args):
            selText = ','.join( cmds.ls(sl=True) )
            cmds.textField(self.ctrl['pattern'], e=True, text=selText)
            refresh()
            # END fromSel()

        def rename(*args):
            text = cmds.textScrollList(self.ctrl['namelist'], q=True, selectItem=True)[0]
            idx = cmds.textScrollList(self.ctrl['namelist'], q=True, selectIndexedItem=True)[0]

            result = cmds.promptDialog( title='Rename', message='Name', button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel', text=text)
            if result == 'OK':
                text = cmds.promptDialog(query=True, text=True)
                cmds.textScrollList(self.ctrl['namelist'], e=True, removeIndexedItem=idx)
                cmds.textScrollList(self.ctrl['namelist'], e=True, appendPosition=[idx, text])

            cmds.textScrollList(self.ctrl['namelist'], e=True, deselectAll=True)




        # UI Start
        cmds.frameLayout(label='Asset Settings', marginHeight=10, marginWidth=10, font="boldLabelFont", width=398)
        cmds.columnLayout(numberOfChildren=1)

        cmds.columnLayout()
        if True:
            cmds.rowColumnLayout( numberOfRows=2)
            if True:
                cmds.text(label='Pattern:', align='left')
                cmds.rowColumnLayout(numberOfColumns=2, columnWidth=([1, 265], [2, 70]), columnSpacing=([1,0],[2,20]), columnAlign=([1,"left"], [2,"right"]))
                if True:
                    self.ctrl['pattern'] = cmds.textField(text='|*|*_geo_grp')
                    self.ctrl['fromSel'] = cmds.button('Selection')
                cmds.setParent('..')
            cmds.setParent('..')

            cmds.rowColumnLayout(numberOfRows=2)
            if True:
                cmds.rowColumnLayout(numberOfColumns=2, columnWidth=([1, 265], [2, 90]), columnSpacing=([1,0],[2,10]), columnAlign=([1,"left"], [2,"left"]))
                if True:
                    cmds.text('Asset List:')
                    cmds.text('Alembic Name:')
                cmds.setParent('..')

                cmds.rowColumnLayout(numberOfColumns=2)
                if True:
                    self.ctrl['objlist'] = cmds.textScrollList( height=150, allowMultiSelection=True, width=269 )
                    cmds.textScrollList( self.ctrl['objlist'], e=True, selectCommand=populateObjListSel )
                    self.ctrl['namelist'] = cmds.textScrollList( height=150, allowMultiSelection=False, width=100 )
                cmds.setParent('..')
            cmds.setParent('..')


            def mode(*args):
                self["separate"] = cmds.radioButton(self.ctrl['modeSeparate'], q=True, select=True) is True
                cmds.textScrollList(self.ctrl['namelist'], e=True, enable=self['separate'])

            cmds.rowColumnLayout(numberOfRows=1, columnOffset=[1, 'right',10 ])
            if True:
                cmds.rowColumnLayout(numberOfColumns=3, columnWidth=([1,75]), columnAlign=([1,"left"]))
                if True:
                    cmds.text(label='Method:')
                    self.ctrl['mode'] = cmds.radioCollection()

                    self.ctrl['modeCombine'] = cmds.radioButton(label='Combine', cc=mode, data=False)
                    self.ctrl['modeSeparate'] = cmds.radioButton(label='Separate', cc=mode, data=True)
                cmds.setParent('..')
            cmds.setParent('..')


            def frame(*args):
                if cmds.radioButton(self.ctrl['frameSingle'], q=True, select=True) is True:
                    self['frame'] = 'single'
                else:
                    self['frame'] = 'active'

            cmds.rowColumnLayout(numberOfRows=1, columnOffset=[1, 'right',10 ])
            if True:
                cmds.rowColumnLayout(numberOfColumns=3, columnWidth=([1,75]), columnAlign=([1,"left"]))
                if True:
                    cmds.text(label='Frames:')
                    self.ctrl['frames'] = cmds.radioCollection()

                    self.ctrl['frameActive'] = cmds.radioButton(label='Active     ', cc=frame, data=True)
                    self.ctrl['frameSingle'] = cmds.radioButton(label='Single', cc=frame, data=False)

                cmds.setParent('..')
            cmds.setParent('..')

        cmds.setParent('..')
        cmds.setParent('..')
        cmds.setParent('..')

        # EDIT
        cmds.radioCollection(self.ctrl['mode'], e=True, select=self.ctrl['modeCombine'])
        self['separate'] = False
        cmds.radioCollection(self.ctrl['frames'], e=True, select=self.ctrl['frameActive'])
        self['frame'] = 'active'


        cmds.textScrollList(self.ctrl['namelist'], e=True, selectCommand=rename)
        cmds.textField(self.ctrl['pattern'], e=True, tcc=refresh)
        cmds.button(self.ctrl['fromSel'], edit=True, command=fromSel)
        refresh()

    def gatherUI(self):
        pass

    def filepath(self):
        path = self.datapath()
        if self.has('sseq') and self.has('sshot'):
            vstr = self.versionStr()
            if vstr == '':
                path+= self['name'] + '/'
            else:
                path+= self['name'] + vstr + '/'

            path+= self['sseq'] + '/'

        self["path"] = path

        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def filename(self, shot=None, idx=None, set=False):
        if self.has('sseq') and self.has('sshot'):
            # validate
            if shot is None:
                nerve.error('alembic.filename() argument error.')
                return False

            filename = 'S'+str(shot["order"]).zfill(3)
            if idx is not None:
                filename+= '_' + self['namelist'][idx]
        else:
            filename = self['name']
            if idx is not None:
                filename+= '_' + self['namelist'][idx]
            filename+= self.versionStr()

        # Set Filename Variable
        if set:
            if 'filename' in self.data.keys():
                if self["separate"]:
                    if not len(self['filename']):
                        self['filename'] = []
                    if filename not in self['filename']:
                        self['filename'].append( filename )
                else:
                    self['filename'] = filename
            else:
                if self['separate']:
                    self['filename'] = []
                    self['filename'].append( filename )
                else:
                    self['filename'] = filename

        filename +='.'+self['extension']
        return filename

    def isFileLocked(self, file):
        if os.path.exists(file):
            try:
                os.rename(file, file)
                return False
            except OSError as e:
                print 'File is being used, cannot override: '+file,
                return True

        return False

    def loadPlugin(self):
        if not cmds.pluginInfo("MayaExocortexAlembic", q=True, l=True):
            cmds.loadPlugin("MayaExocortexAlembic")

    def getShaderDataOLD(self, objects):

        def getTextureData(node, attr):
            plug = node + '.' + attr
            data = {}
            history = cmds.listHistory(plug, pruneDagObjects=True)
            history.pop(0)
            for h in history:
                if cmds.nodeType(h) != 'file':
                    continue

                data['file'] = cmds.getAttr(h + '.fileTextureName')
                con = cmds.listConnections(h + '.uvCoord', s=True, d=False, type='place2dTexture9')

                # Set Defaults
                data['translate'] = (0,0)
                data['rotate'] = 0
                data['repeat'] = (1,1)
                data['offset'] = (0,0)

                if con is not None:
                    data['translate'][0] = cmds.getAttr(con[0] + '.translateFrameU')
                    data['translate'][1] = cmds.getAttr(con[0] + '.translateFrameV')
                    data['rotate'] = cmds.getAttr(con[0] + '.rotateFrame')
                    data['repeat'][0] = cmds.getAttr(con[0]+'.repeatU')
                    data['repeat'][1] = cmds.getAttr(con[0]+'.repeatV')
                    data['offset'][0] = cmds.getAttr(con[0]+'.offsetU')
                    data['offset'][1] = cmds.getAttr(con[0]+'.offsetV')

            return data

        # Get ShadingEngines
        shadingEngineList = []
        for obj in objects:
            shape = cmds.listRelatives( obj, s=True, f=True, ni=True)[0]
            shadingEngines = cmds.listConnections(shape, type='shadingEngine')
            if shadingEngines is None:
                shadingEngines = []
            shadingEngines = list(set(shadingEngines))
            for shadingEngine in shadingEngines:
                if shadingEngine not in shadingEngineList:
                    shadingEngineList.append( shadingEngine )

        # Get Shader Data
        standardData = ['color', 'colorWeight', 'alpha', 'transparency', 'opacity', 'reflection', 'reflectionWeight', 'glossiness', 'roughness', 'refraction', 'refractionWeight', 'refrGlossiness', 'refrRoughness']
        shaderTypes = {}
        shaderTypes['surfaceShader'] = { 'color':'outColor', 'alpha':'outMatteOpacity', 'transparency':'outTransparency' }
        shaderTypes['RedshiftMaterial'] = { 'color':'diffuse_color', 'colorWeight':'diffuse_weight', 'opacity':'opacity_color', 'reflection':'refl_color', 'reflectionWeight':'refl_weight', 'roughness':'refl_roughness', 'refraction':'refr_color', 'refractionWeight':'refr_weight', 'refrRoughness':'refr_roughness'}
        shaderTypes['blinn'] = { 'color':'color', 'colorWeight':'diffuse', 'reflection':'specularColor', 'reflectionWeight':'reflectivity', 'roughness':'eccentricity'}
        shaderTypes['phong'] = { 'color':'color', 'colorWeight':'diffuse', 'reflection':'specularColor', 'reflectionWeight':'reflectivity', 'roughness':'cosinePower'}
        shaderTypes['lambert'] = { 'color':'color', 'colorWeight':'diffuse'}
        ## TO FILL ##

        shadingData = {}
        for shadingEngine in shadingEngineList:

            # Create emtpy data object
            data = {}
            for sd in standardData:
                data[sd] = None

            material = cmds.listConnections( shadingEngine + '.surfaceShader', s=True, d=False )
            if material is None:
                continue
            material = material[0]
            data['name'] = material

            shaderType = cmds.nodeType(material)
            data['type'] = shaderType
            if shaderType not in shaderTypes.keys():
                continue

            for name in shaderTypes[shaderType].keys():
                attr = shaderTypes[shaderType][name]

                plug = material + '.' + attr
                con = cmds.listConnections( plug, s=True, d=False )
                # No Connection
                if con is None:
                    attrType = cmds.getAttr(plug, type=True)
                    if attrType == 'float3':
                        data[name] = cmds.getAttr(plug)[0]
                    elif attrType == 'float':
                        data[name] = cmds.getAttr(plug)
                    else:
                        print 'Warning attribute type: '+attrType+' is unknown.'
                # Has Texture
                else:
                    data[name] = getTextureData(material, attr)

            shadingData[shadingEngine] = data
        return shadingData

    def getShaderData(self, objects):

        def getTextureData(node, attr):
            plug = node + '.' + attr
            data = {}
            history = cmds.listHistory(plug, pruneDagObjects=True)
            history.pop(0)
            for h in history:
                if cmds.nodeType(h) != 'file':
                    continue

                data['file'] = cmds.getAttr(h + '.fileTextureName')
                con = cmds.listConnections(h + '.uvCoord', s=True, d=False, type='place2dTexture9')

                # Set Defaults
                data['translate'] = (0,0)
                data['rotate'] = 0
                data['repeat'] = (1,1)
                data['offset'] = (0,0)

                if con is not None:
                    data['translate'][0] = cmds.getAttr(con[0] + '.translateFrameU')
                    data['translate'][1] = cmds.getAttr(con[0] + '.translateFrameV')
                    data['rotate'] = cmds.getAttr(con[0] + '.rotateFrame')
                    data['repeat'][0] = cmds.getAttr(con[0]+'.repeatU')
                    data['repeat'][1] = cmds.getAttr(con[0]+'.repeatV')
                    data['offset'][0] = cmds.getAttr(con[0]+'.offsetU')
                    data['offset'][1] = cmds.getAttr(con[0]+'.offsetV')

            return data

        # Get ShadingEngine list
        shadingEngineList = []
        for obj in objects:
            if cmds.listRelatives( obj, s=True, f=True, ni=True) is None:
                continue

            shape = cmds.listRelatives( obj, s=True, f=True, ni=True)[0]
            shadingEngines = cmds.listConnections(shape, type='shadingEngine')

            # Error Check
            if shadingEngines is None:
                #nerve.maya.confirm("Object has no shading engine. Check SE for details.")
                continue

            shadingEngines = list(set(shadingEngines))
            for shadingEngine in shadingEngines:
                if shadingEngine not in shadingEngineList:
                    shadingEngineList.append( shadingEngine )

        # Set Shading Data
        shadingData = {}
        for shadingEngine in shadingEngineList:
            material = cmds.listConnections( shadingEngine + '.surfaceShader', s=True, d=False )
            if material is None:
                continue
            material = material[0]

            shadingData[shadingEngine] = {}
            shadingData[shadingEngine]['type'] = cmds.nodeType( material )
            shadingData[shadingEngine]['name'] = material
            shadingData[shadingEngine]['attributes'] = {}

            #attributes = cmds.listAttr(material, connectable=True, hasData=True, settable=True, ro=False)
            attributes = cmds.attributeInfo(material, leaf=False, h=False, w=True, logicalAnd=True )
            skip = ['caching', 'frozen', 'isHistoricallyInteresting', 'nodeState']
            for attr in attributes:
                if attr in skip:
                    continue
                if cmds.attributeQuery( attr, n=material, listParent=True  ) is not None:
                    continue

                shadingData[shadingEngine]['attributes'][attr] = { }
                attrType = cmds.attributeQuery( attr, n=material, attributeType=True )
                #print attr + ':' + attrType
                shadingData[shadingEngine]['attributes'][attr]['type'] = attrType
                con = cmds.listConnections( material+'.'+attr, d=False, s=True )

                isconnected = True
                if con is None:
                    isconnected = False

                shadingData[shadingEngine]['attributes'][attr]['isConnected'] = isconnected
                if isconnected:
                    shadingData[shadingEngine]['attributes'][attr]['value'] = getTextureData(material, attr)
                else:
                    if attrType == 'float3':
                        shadingData[shadingEngine]['attributes'][attr]['value'] = cmds.getAttr(material+'.'+attr)[0]
                    else:
                        shadingData[shadingEngine]['attributes'][attr]['value'] = cmds.getAttr(material+'.'+attr)

        return shadingData

    def release(self):
        def doIt(filepath, start, end, objectList):

            # Single Frame Export
            if self['frame'] == 'single':
                start = cmds.currentTime(q=True)
                end = cmds.currentTime(q=True)

            if self.isFileLocked(filepath):
                nerve.maya.confirm('Cannot override: ' + filepath)
                return False

            # Export ABC file
            objects = ','.join( objectList )
            args = []
            args.append( 'filename=%s'%filepath )
            args.append( 'in=%s'%str( start ) )
            args.append( 'out=%s'%str( end ) )
            args.append( 'uvs=1;ogawa=0;step=1;purepointcache=0' )
            args.append( 'objects=%s'%objects )
            args.append( 'dynamictopology=1;normals=1;facesets=1' )
            command = ';'.join(args)
            if True:
                cmds.ExocortexAlembic_export(j=[command])

            # Export ShadingData
            shadingDataFile = self.getShadingDataFile(filepath)
            shadingData = self.getShaderData( objectList )

            with open(shadingDataFile, 'w') as sdf:
                json.dump(shadingData, sdf)

            # Export ShadingFile
            shadingFile = self.getShadingFile(filepath)
            materialList = []

            for shadingEngine in shadingData.keys():
                material = cmds.listConnections( shadingEngine + '.surfaceShader', s=True, d=False )
                if material is None:
                    continue
                material = material[0]
                materialList.append(material)

            for shadingEngine in shadingData.keys():
                material = cmds.listConnections( shadingEngine + '.rsSurfaceShader', s=True, d=False )
                if material is None:
                    continue
                material = material[0]
                materialList.append(material)

            sel = cmds.ls(sl=True, l=True)
            if len(materialList):
                #unrefMatList = cmds.duplicate(materialList, rr=F, ic=True)
                cmds.select(materialList, r=True)

                unknownNodes = cmds.ls(type='unknown')
                if len(unknownNodes):
                    cmds.delete(unknownNodes)
                    cmds.warning( 'Scene contains unknown nodes: '+ ' '.join(unknownNodes) +'.Deleting...' )

                cmds.file(shadingFile, typ='mayaAscii', op='v=0', pr=False, es=True, f=True)
                #cmds.delete(unrefMatList)
            else:
                cmds.warning('no shaders we translated')

            cmds.select(sel, r=True)
        # END doIt()

        self.loadPlugin()
        self['mode'] = 'release'

        # UI
        if self.ui:
            # Options
            result = cmds.layoutDialog( ui=partial(defaultUI, self, self.releaseUI ) )

            if result == 'Cancel' or result == 'dismiss':
                print 'Release Canceled...',
                return False

            if self['objlist'] is None:
                print 'Nothing selected, Release Canceled...',
                return False

        # New version
        if not self.has('version'):
            self["version"] = self.latestVersion()+1

        # Extension
        self["extension"] = 'abc'

        if self.has('sseq') and self.has('sshot'):
            print 'Exporting multi...'
            # Multi Export
            for shot in self['sshot']:
                # Get start-end framerange
                start  = shot["startFrame"]
                end = shot["endFrame"]

                # Separate
                if self['separate']:
                    for i in range(len(self['objlist'])):
                        if self['objlist'][i] not in self['objlistsel']:
                            continue

                        filepath = self.filepath() + self.filename(shot, i, set=True)
                        objList = self.getObjects( self['objlist'][i] )

                        doIt(filepath, start, end, objList )
                else:
                    # Combined
                    filepath = self.filepath() + self.filename(shot, set=True)
                    objList = self.getObjects(self['objlistsel'])
                    doIt(filepath, start, end, objList)
        else:
            # Get start-end framerange
            start = cmds.playbackOptions(q=True, min=True)

            end = cmds.playbackOptions(q=True, max=True)

            # Separate
            if self['separate']:
                for i in range(len(self['objlist'])):
                    if self['objlist'][i] not in self['objlistsel']:
                        continue
                    filepath = self.filepath() + self.filename(idx=i, set=True)
                    objList = self.getObjects( self['objlist'][i] )
                    doIt(filepath, start, end, objList)
            else:
                # Is Combined
                filepath = self.filepath() + self.filename(set=True)
                objList = self.getObjects(self['objlistsel'])
                doIt(filepath, start, end, objList)

        nerve.maya.confirm('Asset Released', 'Release')
        return True

    def gather(self):
        self.loadPlugin()
        self['mode'] = 'gather'

        def doIt(filepath):
            # Read Alembic
            args = []
            args.append( 'filename=%s'%filepath )
            args.append( 'normals=0' )
            args.append( 'uvs=1' )
            args.append( 'facesets=1' )
            args.append( 'overXforms=1' )
            args.append( 'overDforms=1' )
            if self['method'] == 'attach':
                args.append( 'attachToExisting=1' )
            command = ';'.join(args)
            cmds.ExocortexAlembic_import(j=[command])

            # Store Filepath
            self['filepaths'].append(filepath)

        # doIt [END]

        # UI
        if self.ui:
            # Options
            self.options['method'] = ['import', 'importWithShaders', 'attach']

            result = cmds.layoutDialog( ui=partial( defaultUI, self, self.gatherUI ) )
            if result == 'Cancel' or result == 'dismiss':
                print 'Gather Canceled...',
                return False


        self['filepaths'] = []
        # Multi
        if self.has('sseq') and self.has('sshot'):
            for shot in self['sshot']:
                if self['separate']:
                    for i in range(len(self['namelist'])):
                        filepath = self.filepath() + self.filename(shot, idx=i)
                        doIt(filepath)
                else:
                    filepath = self.filepath() + self.filename(shot)
        else:
            if self['separate']:
                for i in range(len(self['namelist'])):
                    filepath = self.filepath() + self.filename(idx=i)
                    doIt(filepath)
            else:
                filepath = self.filepath() + self.filename()
                doIt(filepath)

        # Shading Data
        if self['method'] == 'importWithShaders':
            # Create Shading Groups
            for obj in self['objlistsel']:
                objects = self.getObjects(obj, shape=True)
                for n in objects:
                    attr = cmds.listAttr(n, ud=True)
                    if attr is None:
                        attr = []
                    for at in attr:
                        if at[:8] != 'FACESET_':
                            continue
                        sg = at[8:]
                        if not cmds.objExists(sg):
                            sg = cmds.sets(renderable=True, noSurfaceShader=True, em=True, n=sg)

                        faceIds = cmds.getAttr(n+'.'+at)
                        for fid in faceIds:
                            cmds.sets('%s.f[%s]'%(n, str(fid)), forceElement=sg)

            # Import Shading
            ns = 'nrvSDF'
            for filepath in self['filepaths']:
                # Shading File
                shadingFile = self.getShadingFile( filepath )
                nodes = cmds.file( shadingFile, i=True , returnNewNodes=True, type='mayaAscii', namespace=ns, ignoreVersion=True, renameAll=False, mergeNamespacesOnClash=False, options='v=0', pr=True, importTimeRange='combine')
                # Shading Data File
                shadingDataFile = self.getShadingDataFile( filepath )
                with open(shadingDataFile) as sdf:
                    sdata = json.load(sdf)

                for sg in sdata.keys():
                    nodeName = ns+':'+sdata[sg]['name']
                    if cmds.objExists( nodeName ) and cmds.nodeType(nodeName) == sdata[sg]['type']:
                        cmds.connectAttr( nodeName + '.outColor', sg + '.surfaceShader', f=True )
                    else:
                        print 'WARNING: '+sdata[sg]['name'] + ' could not be connected to ' + sg

                cmds.namespace(removeNamespace=ns, mergeNamespaceWithRoot=True)


class daily(nerve.assetBase):
    def __init__(self, **kwargs):
        nerve.assetBase.__init__(self)
        self.data = kwargs

        # Defaults
        self.default( 'width', cmds.getAttr("defaultResolution.width"))
        self.default( 'height', cmds.getAttr("defaultResolution.height"))
        self.default( 'camera', nerve.maya.activeCamera() )
        self.default( 'extension', 'mov' )

        self.field = {}

        self.huds = {}
        self.show = []

        # Settings
        self.settings = {}
        self.settings['multi'] = True

        # Options
        self.options = {}

        # UI
        self.ui = False
        self.ctrl = {}

    def filepath(self):
        path = self.jobpath()
        path+= 'elements/dailies/'

        if self.has('sseq') and self.has('sshot'):
            vstr = self.versionStr()
            if vstr == '':
                path+= self['name'] + '/'
            else:
                path+= self['name'] + vstr + '/'

            path+= self['sseq'] + '/'

        self["path"] = path

        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def filename(self, shot=None):
        if self.has('sseq') and self.has('sshot'):
            # validate
            if shot is None:
                nerve.error('daily.filename() argument error.')
                return False

            filename = 'S'+str(shot["order"]).zfill(3)
            filename+= '.' + self['extension']
        else:
            filename = self['name']
            filename+= self.versionStr()
            filename+= '.' + self['extension']

        self["filename"] = filename
        return filename

    def getCameraList(self):
        cameraList = cmds.ls(cameras=True)
        cameraList.remove('frontShape')
        cameraList.remove('sideShape')
        cameraList.remove('topShape')

        return cameraList

    def releaseUI(self):
        cmds.frameLayout(label='Daily Settings', marginHeight=10, marginWidth=10, font="boldLabelFont", width=398)
        cmds.columnLayout(numberOfChildren=1)

        # Resolution
        if True:
            w = 60
            cmds.rowLayout(numberOfColumns=5)
            cmds.text(label="Resolution", width=100,  align='right' )

            ctrl1 = addField(self, 'int', 'width', w=w)
            ctrl2 = addField(self, 'int', 'height', w=w)

            # Globals/HD Button
            def setRez(*args):
                cmds.intField(args[0], edit=True, value=args[2])
                cmds.intField(args[1], edit=True, value=args[3])

            cmds.button(label="Globals", width=w, command=partial( setRez, ctrl1, ctrl2, cmds.getAttr("defaultResolution.width"), cmds.getAttr("defaultResolution.height")  ))
            cmds.button(label="HD 720", width=w, command=partial( setRez, ctrl1, ctrl2, 1280, 720 ))

            cmds.setParent('..')

        # Camera
        if True:
            cmds.rowLayout(numberOfColumns=2)
            cmds.text(label="Camera", width=100,  align='right' )

            optionMenuCtrl = addField(self, 'optionMenu', 'camera' )
            for cam in self.getCameraList():
                cmds.menuItem(label=cam)
            cmds.optionMenu(optionMenuCtrl, e=True, value=self['camera'])
            cmds.setParent('..')

        cmds.setParent('..')
        cmds.setParent('..')

        # HUDS
        if True:
            def hudChangeCommand(*args):
                key = args[0]
                self.huds[key]['value'] = cmds.checkBox(self.ctrl[key], q=True, value=True)

            cmds.frameLayout(label="Heads Up Display", marginHeight=10, marginWidth=10, font="boldLabelFont", width=398, collapsable=True, collapse=False)
            huds = {}
            huds["HUDShotNumber"] = { 'value':True, 'name':'Shot Label' }
            huds["HUDViewAxis"] = { 'value':False, 'name':'View Axis' }
            huds["HUDCurrentFrame"] = { 'value':True, 'name':'Frame' }
            huds["HUDCameraNames"] = { 'value':False, 'name':'Camera' }
            huds["HUDFocalLength"] = { 'value':False, 'name':'Focal Length' }
            self.huds = huds

            cmds.rowColumnLayout(numberOfRows=len(huds.keys()))
            for key in huds.keys():
                self.ctrl[key] = cmds.checkBox( label=huds[key]['name'], value=huds[key]['value'] )
                cmds.checkBox(self.ctrl[key], edit=True, changeCommand=partial( hudChangeCommand, key ))

            cmds.setParent('..')
            cmds.setParent('..')

        # SHOW
        if True:
            def showChangeCommand(*args):
                key = args[0]
                for s in self.show:
                    if s['key'] == key:
                        s['value'] = cmds.checkBox(self.ctrl[key], q=True, value=True)

            cmds.frameLayout(label="Show", marginHeight=10, marginWidth=10, font="boldLabelFont", width=398, collapsable=True, collapse=False)
            show = []
            show.append( {'value':False, 'name':'NURBS Curves', 'key':'nurbsCurves'} )
            show.append( {'value':False, 'name':'NURBS Surfaces', 'key':'nurbsSurfaces'} )
            show.append( {'value':True, 'name':'Polygons', 'key':'polymeshes'} )
            show.append( {'value':False, 'name':'Fluids', 'key':'fluids'} )
            show.append( {'value':True, 'name':'Image Planes', 'key':'imagePlane'} )
            show.append(  {'value':True, 'name':'GPU Caches', 'key':'gpuCacheDisplayFilter'} )
            show.append(  {'value':True, 'name':'Particle Instancers', 'key':'particleInstancers'} )
            self.show = show

            cmds.rowColumnLayout(numberOfRows=len(show))

            for s in show:
                key = s['key']
                self.ctrl[key] = cmds.checkBox(label=s['name'], value=s['value'])
                cmds.checkBox(self.ctrl[key], edit=True, changeCommand=partial( showChangeCommand, key ) )

            cmds.setParent('..')
            cmds.setParent('..')

        # Options
        if True:
            def optChangeCommand(*args):
                key = args[0]
                for o in self.opt:
                    if o['key'] == key:
                        o['value'] = cmds.checkBox(self.ctrl[key], q=True, value=True)

            cmds.frameLayout(label="Options", marginHeight=10, marginWidth=10, font="boldLabelFont", width=398, collapsable=True, collapse=False)
            opt = []
            opt.append( {'value':True, 'name':'Viewport2.0', 'key':'v2'} )
            opt.append( {'value':False, 'name':'Audio [missing frame on odd/even frames]', 'key':'sound'} )
            self.opt = opt

            cmds.rowColumnLayout(numberOfRows=len(opt))
            for o in opt:
                key = o['key']
                self.ctrl[key] = cmds.checkBox(label=o['name'], value=o['value'])
                cmds.checkBox(self.ctrl[key], edit=True, changeCommand=partial( optChangeCommand, key ) )

            cmds.setParent('..')
            cmds.setParent('..')

    def release(self):

        # UI
        if self.ui:
            result = cmds.layoutDialog( ui=partial(defaultUI, self, self.releaseUI) )
            if result == 'Cancel' or result == 'dismiss':
                print 'Release Canceled...',
                return False


        # New version
        if not self.has('version'):
            self["version"] = self.latestVersion()+1

        cmds.select(d=True)

        # Window
        if cmds.window('makeDaily', exists=True):
            cmds.deleteUI( 'makeDaily', window=True )

        dailyWin = cmds.window('makeDaily', title='Make Daily', width=self["width"], height=self["height"], titleBar=1, titleBarMenu=1, menuBarVisible=0, menuBar=0, toolbox=0)
        cmds.frameLayout(labelVisible=False)
        view = cmds.modelEditor()
        cmds.modelEditor(view, edit=True, allObjects=False)
        args = {'edit':True, 'displayAppearance':'smoothShaded', 'displayTextures':True, 'camera':self["camera"], 'activeView':True, 'grid':False}

        for s in self.show:
            if s['key'] == 'gpuCacheDisplayFilter':
                args['pluginObjects'] = [s['key'], s['value']]
            else:
                args[s['key']] = s['value']

        cmds.modelEditor(view, **args)

        sound = False
        for o in self.opt:
            if o['key'] == 'v2':
                if o['value']:
                    maya.mel.eval('setRendererInModelPanel "vp2Renderer" ' + view)
                    print "V2"
                else:
                    maya.mel.eval('setRendererInModelPanel "base_OpenGL_Renderer" ' + view)
                    print "OPENGL"
            if o['key'] == 'sound':
                sound = o['value']

        #cmds.modelEditor(view, e=True, grid=False)
        cmds.showWindow()

        # SAVE
        save = {}
        save['minFrame'] = cmds.playbackOptions(q=True, min=True)
        save['maxFrame'] = cmds.playbackOptions(q=True, max=True)
        save['huds'] = {}
        for hud in cmds.headsUpDisplay(listHeadsUpDisplays=True):
            save['huds'][hud] = cmds.headsUpDisplay(hud, q=True, visible=True)

        # HUDS
        if self.ui is True:
            for hud in cmds.headsUpDisplay(listHeadsUpDisplays=True):
                cmds.headsUpDisplay(hud, edit=True, visible=False)
                if hud in self.huds.keys():
                    cmds.headsUpDisplay(hud, edit=True, visible=self.huds[hud]['value'])

        # Multi
        if self.has('sseq') and self.has('sshot'):
            for shot in self['sshot']:

                cmds.playbackOptions(e=True, min=int(shot["startFrame"]))
                cmds.playbackOptions(e=True, max=int(shot["endFrame"]))

                # HUD
                if self.huds['HUDShotNumber']['value']:
                    hud = 'HUDShotNumber'
                    if cmds.headsUpDisplay(hud, exists=True):
                        cmds.headsUpDisplay(hud, remove=True)
                    cmds.headsUpDisplay(removePosition=[7,1])
                    cmds.headsUpDisplay(hud, section=7, block=1, ba="center", blockSize="medium", label='S%s'%str(shot["order"]).zfill(3), labelFontSize="large")

                filepath = self.filepath() + self.filename(shot)
                outfile = nerve.maya.playblast( filepath, self["width"], self["height"], sound=sound)
                if outfile is None:
                    nerve.maya.confirm('Daily was Cancelled', 'Release')
                    return False

            os.system( 'start ' + '/'.join(filepath.replace('\\', '/').split('/')[:-1]) )

        # Single
        else:
            filepath = self.filepath() + self.filename()
            outfile = nerve.maya.playblast( filepath, self["width"], self["height"], sound)
            os.system( 'start ' + filepath )
        cmds.deleteUI(dailyWin)

        # RESTORE
        cmds.playbackOptions(min=save['minFrame'])
        cmds.playbackOptions(max=save['maxFrame'])

        for hud in save['huds'].keys():
            if cmds.headsUpDisplay(hud, q=True, exists=True):
                cmds.headsUpDisplay(hud, edit=True, visible=save['huds'][hud])
        if cmds.headsUpDisplay('HUDShotNumber', exists=True):
            cmds.headsUpDisplay('HUDShotNumber', remove=True)

        nerve.maya.confirm('Asset Released', 'Release')
        return True

    def gatherUI(self):
        cmds.frameLayout(label='Daily Settings', marginHeight=10, marginWidth=10, font="boldLabelFont", width=398)
        cmds.columnLayout()
        cmds.setParent('..')
        cmds.setParent('..')

    def gather(self):
        if self.ui:
            result = cmds.layoutDialog(ui=partial( defaultUI, self, self.gatherUI ))
            if result == 'Cancel' or result == 'dismiss':
                print 'Gather Canceled...',
                return False
        return True
