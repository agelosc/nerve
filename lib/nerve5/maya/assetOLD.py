import maya.cmds as cmds

import nerve5 as nerve

import os
from functools import partial
import inspect

assetTypes = ['model']

def resolveJob(kwargs={}):
    jobpath = nerve.cfg.path("job")
    keys  = kwargs.keys()
    if 'job' not in keys or 'shot' not in keys or 'seq' not in keys:
        workspace = cmds.workspace(q=True, rootDirectory=True)
        workspace = workspace.replace( jobpath, '' )

        tmp = workspace.split('/')
        kwargs['job'] = tmp[0]
        kwargs['seq'] = tmp[1]
        kwargs['shot'] = tmp[2]

    return kwargs

# RELEASE
def release(**kwargs):
    # job
    kwargs = resolveJob(kwargs)
    # name
    if 'name' not in kwargs.keys():
        nerve.error('Name of asset not set')
    # type
    if 'type' not in kwargs.keys():
        nerve.error('Asset type not set')

    # create object
    Class = getattr(nerve.maya.asset, kwargs['type'])
    obj = Class( kwargs )

    # Default Version
    if 'version' not in obj.args.keys():
        obj.args["version"] = obj.nextVersion()

    # Release
    if obj.release(ui=True):
        obj.exportData()

    return obj

def defaultUI(obj):
    form = cmds.setParent(q=True)
    width = 400
    cmds.formLayout(form, e=True, width=width)

    cmds.frameLayout(label='Asset Options', marginHeight=10, marginWidth=10, font="boldLabelFont")

    # Controls
    for key in obj.opt.keys():
        values = obj.opt[key]

        if len(values) <= 4 :
            # Radio Buttons
            cmds.rowColumnLayout( numberOfRows=1 , columnOffset=[1, "right", 40])
            cmds.text(label=nerve.uncamelCase(key))
            obj.ui[key] = cmds.radioCollection()
            buttons = {}
            for i in range(len(values)):
                buttons[values[i]] = cmds.radioButton(label=values[i])

            cmds.setParent("..")
            cmds.radioCollection(obj.ui[key], edit=True, select=buttons[ obj.args[key] ])
        else:
            # Option Menu
            cmds.rowColumnLayout( numberOfRows=1, columnOffset=[1, "right", 40])
            cmds.text(label=nerve.uncamelCase(key))
            obj.ui[key] = cmds.optionMenu()
            for v in values:
                cmds.menuItem( p=obj.ui[key],  label=v)

            for i in range(0, len(values) ):
                if obj.args[key] == values[i]:
                    cmds.optionMenu(obj.ui[key], edit=True, select=i+1)
            cmds.setParent("..")

    cmds.separator(style='in')
    cmds.rowColumnLayout(numberOfRows=1)
    cmds.button(label="OK", width=(width/2) - 5, height=30, command=partial(defaultUI_doIt, obj))
    cmds.text(label='', width=10)
    cmds.button(label="Cancel", width=(width/2) - 5, height=30, command=defaultUI_cancel)
    cmds.setParent('..')

def defaultUI_doIt(*args):
    obj = args[0]

    for key in obj.opt.keys():
        values = obj.opt[key]

        if len(values) <=4:
            button = cmds.radioCollection(obj.ui[key], q=True, select=True)
            obj.args[key] = cmds.radioButton(button, q=True, label=True)
        else:
            # Option Menu
            idx = int(cmds.optionMenu( obj.ui[key], q=True, select=True )) - 1
            obj.args[key] = values[idx]

    cmds.layoutDialog(dismiss="OK")

def defaultUI_cancel(*args):
    cmds.layoutDialog(dismiss="Cancel")

# GATHER
def gather(**kwargs):
    # job
    kwargs = resolveJob(kwargs)
    # name
    if 'name' not in kwargs.keys():
        nerve.error('Name of asset not set')
    # type
    if 'type' not in kwargs.keys():
        nerve.error('Asset type not set')

    Class = getattr(nerve.maya.asset, kwargs["type"])
    obj = Class( kwargs )

    # Default Version
    if 'version' not in obj.args.keys():
        obj.args["version"] = obj.versions()[-1]

    # Gather
    obj.importData()
    obj.gather(ui=True)


def createSet(obj, nodes, setName=None):
    if setName is None:
        setName = obj.args["type"] + '_' + obj.args["name"]

    # delete if already exists
    if len(cmds.ls(setName, sets=True)):
        cmds.delete(setName)
    else:
        set = cmds.sets(nodes, name=setName)

    for key in obj.args.keys():
        cmds.addAttr( set, ln=key, dt="string" )
        cmds.setAttr( set + "." + key, str(obj.args[key]), type="string")

# MODEL
class model(nerve.assetBase):
    def __init__(self, args):
        nerve.assetBase.__init__(self, args)

    def releaseUI(self):
        return cmds.layoutDialog(ui=partial(defaultUI, self))

    def release(self, ui=False):
        # Validate Input
        sel = cmds.ls(sl=True)
        if len(sel) == 0:
            nerve.maya.error("Nothing Selected")
            return False

        # OPTIONS
        if True:
            # Create Options
            self.opt["fileType"] = ["mayaBinary", "mayaAscii", "obj"]
            self.setDefaultOptions()

            # Override Options UI
            if ui:
                if self.releaseUI() == 'Cancel':
                    return False

        # RELEASE
        if True:
            # maya export
            if self.args["fileType"] == 'mayaAscii' or self.args["fileType"] == 'mayaBinary':
                # extension
                if self.args["fileType"] == 'mayaAscii':
                    self.args["extension"] = 'ma'
                else:
                    self.args["extension"] = 'mb'
                cmds.file( self.filepath(), options='v=0', type=self.args["fileType"], preserveReferences=True, exportSelected=True, force=True )
            # obj export
            elif self.args["fileType"] == 'obj':
                self.args["extension"] = 'obj';
                cmds.file( self.filepath(), options='groups=1;ptgroups=1;materials=1;smoothing=1;normals=1', type="OBJexport", preserveReferences=True, exportSelected=True, force=True)

        return True

    def gather(self, ui=False):
        # OPTIONS
        if True:
            self.opt["mode"] = [ 'import', 'reference', 'replace' ]
            self.setDefaultOptions()

            if ui:
                if self.gatherUI() == 'Cancel':
                    return False
        # GATHER
        if True:
            options = 'v=0'
            if self.args['fileType'] == 'obj':
                options = 'mo=1'

            # Import
            if self["mode"] == 'import':
                nodes = cmds.file(self.filepath(), i=True, type=self.args["fileType"], options=options, preserveReferences=True, defaultNamespace=True, mergeNamespacesOnClash=True, returnNewNodes=True)
                createSet(self, nodes)

            # Reference
            if self["mode"] == 'reference':
                # Namespace
                namespace = self.args["name"]
                original = namespace

                # increment namespace
                if cmds.namespace(exists=original):
                    c = 1
                    while cmds.namespace(exists=namespace):
                        namespace = original + '_' + str(c).zfill(2)
                        c = c + 1

                nodes = cmds.file(self.filepath(), reference=True, type=self.args["fileType"], sharedNodes="renderLayersByName", options=options, namespace=namespace, returnNewNodes=True )
                createSet(self, nodes, self.args["type"] + '_' + namespace)

            # Replace
            if self["mode"] == 'replace':
                sel = cmds.ls(sl=True)
                if len(sel) == 0:
                    nerve.maya.error("Nothing selected to replace.")
                    return False

                if cmds.referenceQuery(sel[0], isNodeReferenced=True):
                    referenceNode = cmds.referenceQuery(sel[0], referenceNode=True)
                    cmds.file(self.filepath(), loadReference=referenceNode, type=self.args["fileType"], options=options)
                else:
                    nerve.maya.error("Cannot replace asset. Selection is not a reference.")
                    return False

    def gatherUI(self):
        return cmds.layoutDialog(ui=partial(defaultUI, self))
