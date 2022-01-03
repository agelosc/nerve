import maya.cmds as cmds

import nerve
import nerve.maya.UI
reload(nerve.maya.UI)

# Utilities


def duplicate():
    return cmds.duplicate(returnRootsOnly=True)

def instance():
    return cmds.instance()

def duplicateInputGraph():
    return cmds.duplicate(returnRootsOnly=True, upstreamNodes=True)

def removeUnknownNodes():
    nodes = cmds.ls(type='unknown')
    if not len(nodes):
        print("Scene doesn't have any unknown nodes."),
        return False

    for n in nodes:
        print('deleting {}'.format(n))
        try:
            cmds.delete(n)
        except:
            print('## Cannot Delete {}'.format(n))

    print('Deleted {} unknown nodes.'.format(len(nodes))),
    return True

def removeUnknownPlugins():
    unknownPlugins = cmds.unknownPlugin(q=True, list=True) or []
    if not len(unknownPlugins):
        print('No unknown plugins found.'),
        return False

    for up in unknownPlugins:
        print('Removing: {}'.format(up))
        cmds.unknownPlugin(up, remove=True)

    print('Removed {} unknown plugins.'.format(len(unknownPlugins)))

def removeTurtle():
    nodes = ['TurtleDefaultBakeLayer', 'TurtleRenderOptions', 'TurtleUIOptions', 'TurtleBakeLayerManager']
    for node in nodes:
        if cmds.objExists(node):
            cmds.lockNode(node, l=False)
            cmds.delete(node)
    cmds.unloadPlugin("Turtle.mll",f=True)

def importReference():
    sel = cmds.ls(sl=True)
    if not len(sel):
        print('Nothing selected.'),
        return False

    namespaces = []
    for n in sel:
        cmds.select(n, replace=True)
        if not cmds.referenceQuery(n, isNodeReferenced=True):
            continue

        refNode = cmds.referenceQuery(n, referenceNode=True, topReference=True)
        refPath = cmds.referenceQuery(refNode, filename=True)
        namespace = n.rpartition(':')[0]
        if namespace not in namespaces:
            namespaces.append(namespace)

        cmds.file(refPath, importReference=True)

        for ns in namespaces:
            cmds.namespace(force=True, moveNamespace=(ns, ':'))
            cmds.namespace(removeNamespace=ns)

        unknownRefNodes = cmds.ls('_UNKNOWN_*') or []
        if unknownRefNodes:
            cmds.delete(unknownRefNodes)

def removeReference():
    sel = cmds.ls(sl=True)
    if not len(sel):
        print('Nothing Selected.'),
        return False

    for n in sel:
        if not cmds.referenceQuery(n, isNodeReferenced=True):
            continue
        namespace = n.rpartition(':')[0]

        refPath = cmds.referenceQuery(n, filename=True)
        cmds.file(refPath, removeReference=True)

        if cmds.namespace(exists=namespace):
            cmds.namespace(force=True, moveNamespace=(namespace, ':'))
            cmds.namespace(removeNamespace=namespace)

def clearNamespaces():
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
        c=c+1

def locatorToPivot():
    sel = cmds.ls(sl=True, l=True)
    for n in sel:
        name = n.split("|")[-1].split(":")[-1]
        pos = cmds.xform(n, q=True, ws=True, piv=True)
        rot = cmds.xform(n, q=True, ws=True, ro=True)

        loc = cmds.spaceLocator(p=(0, 0, 0))
        cmds.xform(loc[0], ws=True, t=(pos[0], pos[1], pos[2]))
        cmds.xform(loc[0], ws=True, ro=(rot[0], rot[1], rot[2]))
        cmds.rename(loc[0], name)

def locatorToAverage():
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

# Redshift
def rsRelease():
    if not len(cmds.ls(sl=True)):
        print('Nothing selected.'),
        return False

    result = nerve.maya.UI.Dialog(msg='Asset Path')
    if not result:
        return False

    asset = nerve.Asset(path=result, version=1, format='rs')
    nerve.maya.ReleaseUI(asset.GetFilePath('session'))

def rsGather():
    result = nerve.maya.UI.Dialog(msg='Asset Path')
    if not result:
        return False

    asset = nerve.Asset(path=result, version=1, format='rs')
    if not asset.Exists():
        print('Asset not found.'),
        return False
    nerve.maya.GatherUI(asset.GetFilePath('session'))

def lockRsProxyHistory():
    for proxy in cmds.ls(type='RedshiftProxyMesh'):
        mesh = cmds.listConnections(proxy + '.outMesh', p=True) or []
        for m in mesh:
            try:
                cmds.setAttr(m, lock=True)
            except:
                pass

def enableRsTesselation():
    sel = cmds.ls(sl=True, l=True)
    if not len(sel):
        print('Nothing selcted.'),
        return False

    cmds.select(hi=True)
    objects = cmds.ls(sl=True, l=True, type='shape')
    for obj in objects:
        if not cmds.attributeQuery('rsEnableSubdivision', n=obj, exists=True):
            continue
        cmds.setAttr(obj + '.rsEnableSubdivision', 1)

    cmds.select(sel, r=True)

def disableRsTesselation():
    sel = cmds.ls(sl=True, l=True)
    if not len(sel):
        print('Nothing selcted.'),
        return False

    cmds.select(hi=True)
    objects = cmds.ls(sl=True, l=True, type='shape')
    for obj in objects:
        if not cmds.attributeQuery('rsEnableSubdivision', n=obj, exists=True):
            continue
        cmds.setAttr(obj + '.rsEnableSubdivision', 0)

    cmds.select(sel, r=True)

def enableRsDisplacement():
    sel = cmds.ls(sl=True, l=True)
    if not len(sel):
        print('Nothing selcted.'),
        return False

    cmds.select(hi=True)
    objects = cmds.ls(sl=True, l=True, type='mesh')
    for obj in objects:
        if not cmds.attributeQuery('rsEnableDisplacement', n=obj, exists=True):
            continue
        cmds.setAttr(obj + '.rsEnableDisplacement', 1)

    cmds.select(sel, r=True)

def disableRsDisplacement():
    sel = cmds.ls(sl=True, l=True)
    if not len(sel):
        print('Nothing selcted.'),
        return False

    cmds.select(hi=True)
    objects = cmds.ls(sl=True, l=True, type='mesh')
    for obj in objects:
        if not cmds.attributeQuery('rsEnableDisplacement', n=obj, exists=True):
            continue
        cmds.setAttr(obj + '.rsEnableDisplacement', 0)

    cmds.select(sel, r=True)

# Rendering
def disableSmoothRender():
    sel = cmds.ls(sl=True, l=True)
    reselect=True
    if not len(sel):
        sel = cmds.ls(type='mesh')
        reselect = False


    cmds.select(hi=True)
    objects = cmds.ls(sl=True, l=True, type='mesh')

    for obj in objects:
        cmds.setAttr(obj + '.useSmoothPreviewForRender', 0)
        cmds.setAttr(obj + '.renderSmoothLevel', 0)

    if reselect:
        cmds.select(sel, r=True)

def enableSmoothRender():
    sel = cmds.ls(sl=True, l=True)
    reselect=True
    if not len(sel):
        sel = cmds.ls(l=True, type='mesh')
        reselect=False

    cmds.select(hi=True)
    objects = cmds.ls(sl=True, l=True, type='mesh')
    for obj in objects:
        cmds.setAttr(obj + '.useSmoothPreviewForRender', 1)
        cmds.setAttr(obj + '.renderSmoothLevel', 2)
    if reselect:
        cmds.select(sel, r=True)

def localRender():
    import os
    mayaPath = nerve.Path(os.environ['MAYA_LOCATION']) + 'bin' + 'Render.exe'
    scene = cmds.file(q=True, sn=True)
    renderPath = nerve.Path(cmds.workspace(q=True, rootDirectory=True)) + 'renders'
    renderer = cmds.getAttr( "defaultRenderGlobals.currentRenderer" )

    renderer = 'redshift'

    if True:
        # arnold
        if renderer == "arnold":
            rendererFlags = '-r arnold -ai:ltc 1 -ai:lve 2'
        # redshift
        elif renderer == "redshift":
            rendererFlags = '-r redshift -gpu {0}'
        elif renderer == 'mayaHardware2':
            rendererFlags = '-r hw2'
        else:
            cmds.error('Current rerderer not supported ('+renderer+')')
            return False

    # Frames
    startFrame = int(cmds.playbackOptions(q=True, min=True))
    endFrame = int(cmds.playbackOptions(q=True, max=True))

    frameStr = str(startFrame) + '-' + str( endFrame )
    result = cmds.promptDialog(title='Rename Object', message='Enter Frame List:', button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel', text=frameStr)
    if result == 'OK':
        frameStr = cmds.promptDialog(query=True, text=True)
    else:
        return False

    FrameList = []
    FramePairs = frameStr.replace(' ', '').split(',')
    for pair in FramePairs:
        tmp = pair.split('-')
        if len(tmp) == 1:
            start = tmp[0]
            end = tmp[0]
        else:
            start = tmp[0]
            end = tmp[1]
        FrameList.append( [start, end] )

    cmd = ''
    for frames in FrameList:
        cmd+= '"{0}" {1} -s {2} -e {3} -b 1 -rd "{4}" "{5}"\n'.format(mayaPath, rendererFlags, frames[0], frames[1], renderPath, scene)
    print cmd

    batfilepath = os.environ["TEMP"] + '/localRender.bat'
    batfile = open(batfilepath, 'w')
    batfile.write(cmd)
    batfile.close()

    os.system('start "" '+batfilepath+'')
