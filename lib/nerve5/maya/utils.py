import maya.cmds as cmds
import maya.mel as mel

from functools import partial


def UI():
    data = []
    #data.append( { 'ctrl':'', 'label':'', 'command':'' } )

    # plugins
    data.append({ 'ctrl':'plugins', 'type':'submenu', 'label':'Plugins'})
    data.append({ 'label':'Redshift', 'command': partial(loadPlugin,'redshift4maya'), 'parent':'plugins' } )
    data.append({ 'label':'OBJ Export', 'command': partial(loadPlugin,'objExport'),  'parent':'plugins' } )
    data.append({ 'label':'Exocortex Alembic', 'command': partial(loadPlugin,'MayaExocortexAlembic'),  'parent':'plugins' } )
    data.append( {'type':'seperator'} )
    data.append( { 'label':'Clear Namespaces', 'command':clearNamespaces } )
    data.append( {'type':'seperator'} )
    data.append( { 'label':'Import Reference', 'command':importReference } )
    data.append( { 'label':'Remove Reference', 'command':removeReference } )
    data.append( { 'label':'Duplicate Reference', 'command':duplicateReference } )
    data.append( {'type':'seperator'} )
    data.append( { 'label':'Locator To Pivot', 'command':locatorToPivot } )
    data.append( { 'label':'Locator To Average', 'command':locatorToAverage } )
    data.append( {'type':'seperator'} )
    data.append( { 'label':'Remove Unknown Nodes', 'command':removeUnknownNodes } )
    data.append( { 'label':'Remove Unknown Plugins', 'command':removeUnknownPlugins } )
    data.append( { 'label':'Remove Turtle', 'command':removeTurtle } )

    return data


def removeUnknownNodes(*args):
    nodes = cmds.ls(type='unknown')
    for n in nodes:
        print 'Deleting: '+n

    if len(nodes):
        cmds.delete(nodes)
    else:
        print 'No unknown nodes found.',

def removeUnknownPlugins(*args):
    unknownPlugins = cmds.unknownPlugin(q=True, list=True)
    if unknownPlugins is None:
        print 'No unknown plugins found.',
        unknownPlugins = []
    for up in unknownPlugins:
        print 'Deleting: '+up
        cmds.unknownPlugin(up, remove=True)

def loadPlugin(*args):
    if not cmds.pluginInfo(args[0], q=True, loaded=True):
        cmds.loadPlugin(args[0])
        print args[0] + " loaded...",
    else:
        print args[0] + " is already loaded...",

def importReference(*args):

    def clearSets():
        selection = cmds.ls(sl=True)
        for sel in selection:
            tmp = sel.split(':')
            namespace = tmp[0]
            name = ':'.join( tmp[1:] )
            #namespace = namespace.replace(":", "")
            if cmds.namespace(exists=namespace):
                cmds.namespace(force=True, moveNamespace=[namespace, ":"])
                cmds.namespace(removeNamespace=namespace)

        return True

    sel = cmds.ls(sl=True)
    if len(sel) == 0:
        cmds.error("Nothing selected")

    for n in sel:
        cmds.select(n, replace=True)
        tmp = cmds.sets()
        if cmds.referenceQuery(n, isNodeReferenced=True):
            referenceNode = cmds.referenceQuery(n, referenceNode=True, topReference=True)
            referencePath = cmds.referenceQuery(referenceNode, filename=True)
            cmds.file(referencePath, edit=True, namespace='TMP')
            cmds.file(referencePath, importReference=True)

        setMembers = cmds.sets(tmp, query=True)
        cmds.select(setMembers, replace=True)
        clearSets()
        unknownRefNodes = cmds.ls("_UNKNOWN_*")
        if len(unknownRefNodes):
            cmds.delete(unknownRefNodes)

        cmds.delete(tmp)

def removeReference(*args):
    sel = cmds.ls(sl=True)
    if len(sel) == 0:
        cmds.error("Nothing selected")

    for n in sel:
        tmp = n.split(':')
        namespace = tmp[0]
        name = ':'.join( tmp[1:] )

        if cmds.referenceQuery(n, isNodeReferenced=True):
            referencePath = cmds.referenceQuery(n,filename=True)
            cmds.file(referencePath, removeReference=True)
        if cmds.namespace(exists=namespace):
            cmds.namespace(force=True, moveNamespace=[namespace, ":"])
            cmds.namespace(removeNamespace=namespace)

def clearNamespaces(*args):
    cmds.namespace(set=":")
    tmp = cmds.namespaceInfo(listOnlyNamespaces=True)

    c = 0
    while (len(tmp) != 2) and c < 20:
        namespaces = []
        for t in tmp:
            if t != "UI" and t != "shared":
                namespaces.append(t)

        for ns in namespaces:
            cmds.namespace(mv=[ns, ":"], force=True)
            cmds.namespace(rm=ns)

        tmp = cmds.namespaceInfo(listOnlyNamespaces=True)
        c = c + 1

def locatorToPivot(*args):
    sel = cmds.ls(sl=True, l=True)
    for n in sel:
        name = n.split("|")[-1].split(":")[-1]
        pos = cmds.xform(n, q=True, ws=True, piv=True)
        rot = cmds.xform(n, q=True, ws=True, ro=True)

        loc = cmds.spaceLocator(p=(0, 0, 0))
        cmds.xform(loc[0], ws=True, t=(pos[0], pos[1], pos[2]))
        cmds.xform(loc[0], ws=True, ro=(rot[0], rot[1], rot[2]))
        cmds.rename(loc[0], name)

def locatorToAverage(*args):
    sel = cmds.ls(sl=True, l=True, fl=True)
    if len(sel) <= 1:
        cmds.error("More than one object must be selected for average position")

    avg = (0,0,0)
    for n in sel:
        pos = cmds.xform(n, q=True, ws=True, t=True)
        avg =( avg[0] + pos[0], avg[1] + pos[1], avg[2] + pos[2] )

    avg = ( avg[0]/len(sel), avg[1]/len(sel), avg[2]/len(sel) )
    loc = cmds.spaceLocator(p=(0,0,0))[0]
    cmds.xform(loc, ws=True, t=avg)
    cmds.xform(loc, s=(0.1, 0.1, 0.1))

def removeTurtle(*args):
    nodes = ['TurtleDefaultBakeLayer', 'TurtleRenderOptions', 'TurtleUIOptions', 'TurtleBakeLayerManager']
    for node in nodes:
        if cmds.objExists(node):
            cmds.lockNode(node, l=False)
            cmds.delete(node)
    cmds.unloadPlugin("Turtle.mll",f=True)


def duplicateReference(*args):
    sel = cmds.ls(sl=True)

    data = {}
    data["file"] = os.environ["TMP"] + "/test.mb"
    data["options"] = cmds.optionVar(query="mayaBinaryOptions")
    data["format"] = "mayaBinary"
    data["namespace"] = "DUP"

    cmds.file(data["file"], options=data["options"], type=data["format"], preserveReferences=True, exportSelected=True, force=True)
    nodes = cmds.file(data["file"], i=True, type=data["format"], options=data["options"], sharedNodes="renderLayersByName", namespace=data["namespace"], preserveReferences=True, returnNewNodes=True)

    refNode = cmds.referenceQuery(nodes[0], referenceNode=True, topReference=True)
    refPath = cmds.referenceQuery(refNode, filename=True)

    # Get Parent DAG node
    node = nodes[0]
    for n in nodes:
        node = cmds.ls(n, dag=True, l=True)
        if len(node):
            node = node[0].split("|")[1]
            break

    n1 = node.split(":")[0]
    n2 = node.split(":")[1]
    cmds.file(refPath, edit=True, namespace=n2)
    cmds.namespace(force=True, moveNamespace=[n1, ":"])
    cmds.namespace(removeNamespace=n1)
