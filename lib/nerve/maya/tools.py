import maya.cmds as cmds

import nerve
import nerve.maya.UI
try:
    from importlib import reload
except:
    pass
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

    print('Removed {} unknown plugins.'.format(len(unknownPlugins))),

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

def center():
    import maya.api.OpenMaya as om
    sel = cmds.ls(sl=True, l=True, type='transform')
    for n in sel:
        bbox = cmds.xform(n, q=True, a=True, ws=True, boundingBox=True)
        min = om.MVector((bbox[0], bbox[1], bbox[2]))
        max = om.MVector((bbox[3], bbox[4], bbox[5]))
        height = (max.y - min.y)*0.5
        pos = om.MVector(cmds.xform(n, q=True, ws=True, t=True))
        center = min+((max-min)*0.5)
        cmds.xform(n, ws=True, piv=(center[0], center[1]-height, center[2]))    
        offset = (center-pos)*-1
        cmds.xform(n, ws=True, t=(offset[0], offset[1]+height, offset[2]))
        cmds.makeIdentity(n, apply=True, t=True, r=True, s=True, n=True, pn=True)

def snap():
    sel = cmds.ls(sl=True, l=True)
    if len(sel) < 2:
        print('Selection error.'),
        return False

    pos = cmds.xform(sel[1], q=True, ws=True, t=True)
    rot = cmds.xform(sel[1], q=True, ws=True, ro=True)
    sca = cmds.xform(sel[1], q=True, ws=True, s=True)

    cmds.xform(sel[0], ws=True, t=(pos[0], pos[1], pos[2]))
    cmds.xform(sel[0], ws=True, ro=(rot[0], rot[1], rot[2]))
    cmds.xform(sel[0], a=True, s=(sca[0], sca[1], sca[2]))

    cmds.select(sel[0], r=True)
    print('Snapped {} to {}.'.format(sel[0], sel[1])),

def scatter(name=None):
    if not cmds.pluginInfo('MASH', q=True, l=True):
        cmds.loadPlugin('MASH')
    if not name:
        name = nerve.maya.UI.Dialog.Input(title='Scatter Name')
        if not name:
            return False

    sel = cmds.ls(sl=True, l=True)

    # Distribute Node
    dist = cmds.createNode('MASH_Distribute', name='{}_distribute'.format(name))
    # Mash Node
    mash = cmds.createNode('MASH_Waiter', name='{}_mash'.format(name))
    cmds.addAttr(mash, longName='instancerMessage', at='message', hidden=True )
    # Instancer Node
    inst = cmds.createNode('instancer', name='{}_instancer'.format(name))
    cmds.addAttr(inst, longName='instancerMessage', at='message', hidden=True )
    # ID node
    id = cmds.createNode('MASH_Id', name='{}_ID'.format(name))
    # Random Node
    rand = cmds.createNode('MASH_Random', name='{}_random'.format(name))
    data = {}
    for attr in ['position', 'rotation', 'scale']:
        for a in ['X', 'Y', 'Z']:
            data[attr+a] = 0
            cmds.setAttr(rand + '.{}{}'.format(attr, a), 0)
    data = {'absoluteScale':True, 'uniformRandom':True, 'transformationSpace':2}
    for key,val in data.items():
        cmds.setAttr(rand + '.'+key, val)

    # Connect disribute to Mash
    cmds.connectAttr(dist+'.waiterMessage', mash+'.waiterMessage', f=True)
    cmds.connectAttr(dist+'.outputPoints', mash+'.inputPoints', f=True)

    # Connect Mash To Instancer
    cmds.connectAttr(mash+'.instancerMessage', inst+'.instancerMessage', f=True)
    cmds.connectAttr(mash+'.outputPoints', inst+'.inputPoints', f=True)

    # Connect Selected Objects to Instancer
    for i in range(len(sel)):
        cmds.connectAttr(sel[i]+'.matrix', inst+'.inputHierarchy[{}]'.format(i), f=True)

    # Connect Distribute to ID
    cmds.connectAttr(dist+'.outputPoints', id+'.inputPoints', f=True)
    # Connect ID to Random
    cmds.connectAttr(id+'.outputPoints', rand+'.inputPoints', f=True)

    # Connect Random to Mash
    cmds.connectAttr(rand+'.outputPoints', mash+'.inputPoints', f=True)
    if len(sel):
        cmds.setAttr(id+'.numObjects', len(sel))

    cmds.select(inst, r=True)
    nerve.maya.UI.Scatter()

def scatterUI():
    nerve.maya.UI.Scatter()

def copyTransform():
    import json
    attribs = []
    for name in ['translate', 'rotate', 'scale']:
        for axis in ['X', 'Y', 'Z']:
            attribs.append( name + axis)

    sel = cmds.ls(sl=True, l=True)
    if not len(sel):
        cmds.warning('Nothing selected')
        return False
    
    if cmds.nodeType(sel[0]) != 'transform':
        cmds.warning('Selection is not a transform.')
        return False

    data = {}
    for attrib in attribs:
        data[attrib] = cmds.getAttr(sel[0] + '.' + attrib)

    filepath = nerve.Path('$TEMP/nerve/transform.json')
    with open(str(filepath), 'w') as outfile:
        json.dump(data, outfile)

def pasteTransform():
    import json
    filepath = nerve.Path('$TEMP/nerve/transform.json')
    if not filepath.Exists():
        cmds.warning('Transform not found on clipboard')
        return False

    sel = cmds.ls(sl=True, l=True)
    if not len(sel):
        cmds.warning('Nothing selected')
        return False
    
    if cmds.nodeType(sel[0]) != 'transform':
        cmds.warning('Selection is not a transform.')
        return False     

    with open(str(filepath)) as json_file:
        data = json.load(json_file)

    for key,val in data.items():
        cmds.setAttr(sel[0] + '.' + key, val)

def deinstance():

    import maya.api.OpenMaya as om

    def getInstances():
        instances = []
        iterDag = om.MItDag(om.MItDag.kBreadthFirst)
        while not iterDag.isDone():
            instanced = om.MItDag.isInstanced(iterDag)
            if instanced:
                instances.append(iterDag.fullPathName())
            iterDag.next()
        return instances   

    instances = getInstances()
    while len(instances):
        parent = cmds.listRelatives(instances[0], parent=True, fullPath=True)[0]
        cmds.duplicate(parent, renameChildren=True)
        cmds.delete(parent)
        instances = getInstances()         

# Redshift
def rsRelease():
    if not len(cmds.ls(sl=True)):
        print('Nothing selected.'),
        return False

    result = nerve.maya.UI.Dialog.Input(msg='Asset Path')
    if not result:
        return False

    asset = nerve.Asset(path=result, version=1, format='rs')
    nerve.maya.ReleaseUI(asset.GetFilePath('session'))

def rsGather():
    result = nerve.maya.UI.Dialog.Input(msg='Asset Path')
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

def rsConvertMaterial():
    materials = nerve.maya.Node.GetMaterials()
    for mat in materials:
        nerve.maya.Material().Convert('RedshiftMaterial')
        
def rsConvertOpacityToSprite():
    materials = nerve.maya.Node.GetMaterials()
    for mat in materials:
        if cmds.nodeType(mat) != 'RedshiftMaterial':
            continue

        attrdata = nerve.maya.Node.GetAttrData(mat, 'opacity_color')
        if 'node' not in attrdata.keys():
            continue
        tex = nerve.maya.Node.listHistory( mat+'.opacity_color', 'file')
        tex = cmds.listConnections(mat + '.opacity_color')
        if not tex:
            continue
        tex = tex[0]
        
        sprite = nerve.maya.Node.create('RedshiftSprite')
        nerve.maya.Node.setAttr(sprite, 'tex0', cmds.getAttr(tex + '.fileTextureName'))
        nerve.maya.Node.connectAttr(mat, 'outColor', sprite, 'input' )

        sgs = cmds.listConnections(mat + '.outColor', type='shadingEngine')
        if not sgs:
            continue

        for sg in sgs:
            nerve.maya.Node.connectAttr( sprite, 'outColor', sg, 'surfaceShader' )

        cmds.disconnectAttr(tex + '.outColor', mat + '.opacity_color')
        nerve.maya.Node.setAttr( mat, 'opacity_color', (1,1,1))

def rsConvertSpriteToOpacity():
    materials = nerve.maya.Node.GetMaterials()
    for sprite in materials:
        if cmds.nodeType(sprite) != 'RedshiftSprite':
            continue
        mat = nerve.maya.Node.listHistory(sprite + '.input', 'RedshiftMaterial')
        if not mat:
            continue

        texfile = cmds.getAttr(sprite + '.tex0')
        tex = nerve.maya.Node.create('file')
        nerve.maya.Node.setAttr(tex, 'fileTextureName', texfile)
        nerve.maya.Node.setAttr(tex, 'colorSpace', 'Raw')

        nerve.maya.Node.connectAttr( tex, 'outColor', mat, 'opacity_color')

        sgs = cmds.listConnections(sprite + '.outColor', type='shadingEngine')
        if not sgs:
            continue
        for sg in sgs:
            cmds.connectAttr(mat +'.outColor', sg + '.surfaceShader', f=True)

        cmds.delete(sprite)

        
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
    print(cmd)

    batfilepath = os.environ["TEMP"] + '/localRender.bat'
    batfile = open(batfilepath, 'w')
    batfile.write(cmd)
    batfile.close()

    os.system('start "" '+batfilepath+'')
