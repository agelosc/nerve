import maya.cmds as cmds

import nerve
import nerve.maya.UI
try:
    from importlib import reload
except:
    pass


def performFileDropAction(url):
    print(url)

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
            try:
                cmds.namespace(mv=[ns, ":"], force=True)
                cmds.namespace(rm=ns)
            except:
                print(ns + ' namespace could not be removed.')

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

# FBX
def convertFBXLocToGrp():
    for n in cmds.ls(type='locator'):
        t = cmds.listRelatives(n, p=True)[0]
        parent = cmds.listRelatives(t, p=True)
        args = {}
        args['em'] = True
        args['name'] = t + '_GRP'
        if parent:
            args['parent'] = parent[0]
        
        grp = cmds.group(**args)
        for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']:
            cmds.setAttr( grp + '.' + attr, cmds.getAttr(t + '.' + attr) )
        children = cmds.listRelatives(t, c=True, type='transform')
        cmds.parent(children, grp)
        cmds.delete(t)    

# Rendering
def SetLinearColorManagement():

    cmds.colorManagementPrefs(e=True, renderingSpaceName='scene-linear Rec.709-sRGB')
    cmds.evalDeferred( 'cmds.colorManagementPrefs(e=True, viewTransformName="Un-tone-mapped (sRGB)")')
    cmds.rsColorManagement(attributeChanged="workingSpaceName")

def SetACESColorManagement():
    
    cmds.colorManagementPrefs(e=True, renderingSpaceName='ACEScg')
    cmds.evalDeferred( 'cmds.colorManagementPrefs(e=True, viewTransformName="ACES 1.0 SDR-video (sRGB)")')    
    cmds.rsColorManagement(attributeChanged="workingSpaceName")

def renameMaterial():
    import maya.cmds as cmds
    name = nerve.maya.UI.Dialog.Input()
    if name:
        sel = cmds.ls(sl=True)
        mat = nerve.maya.Node.GetMaterials()
        for m in mat:
            sg = nerve.maya.Node.GetShadingEngines(m)
            cmds.rename(m, name+'_M')
            for s in sg:
                cmds.rename(s, name+'_SG')


# Modeling
def centerPivots():
    for n in cmds.ls(sl=True, l=True, type='transform'):
        cmds.xform(n, centerPivots=True)

def centerPivotAtBase():
    import maya.api.OpenMaya as om

    for n in cmds.ls(sl=True, l=True, type='transform'):
        bbox = cmds.xform(n, q=True, a=True, ws=True, boundingBox=True)
        min = om.MVector((bbox[0], bbox[1], bbox[2]))
        max = om.MVector((bbox[3], bbox[4], bbox[5]))
        height = (max.y - min.y)*0.5
        pos = om.MVector(cmds.xform(n, q=True, ws=True, t=True))
        center = min+((max-min)*0.5)
        cmds.xform(n, ws=True, piv=(center[0], center[1]-height, center[2]))    
        #offset = (center-pos)*-1
        #cmds.xform(n, ws=True, t=(offset[0], offset[1]+height, offset[2]))
        #cmds.makeIdentity(n, apply=True, t=True, r=True, s=True, n=True, pn=True)

        
def centerPivotAtBaseAndGrid():
    import maya.api.OpenMaya as om

    for n in cmds.ls(sl=True, l=True, type='transform'):
        bbox = cmds.xform(n, q=True, a=True, ws=True, boundingBox=True)
        min = om.MVector((bbox[0], bbox[1], bbox[2]))
        max = om.MVector((bbox[3], bbox[4], bbox[5]))
        height = (max.y - min.y)*0.5
        pos = om.MVector(cmds.xform(n, q=True, ws=True, t=True))
        center = min+((max-min)*0.5)
        cmds.xform(n, ws=True, piv=(center[0], center[1]-height, center[2]))    
        offset = (center-pos)*-1
        cmds.xform(n, ws=True, t=(offset[0], offset[1]+height, offset[2]))
        #cmds.makeIdentity(n, apply=True, t=True, r=True, s=True, n=True, pn=True)        

def freezePivot():
    cmds.xform(ws=True, piv=(0,0,0))

def freezeTransforms():
    #makeIdentity -apply true -t 1 -r 1 -s 1 -n 0 -pn 1;
    for n in cmds.ls(sl=True, l=True, type='transform'):
        cmds.makeIdentity(n, apply=True, t=True, r=True, s=True, n=False, preserveNormals=True )

def freezeTransformsNoScale():
    #makeIdentity -apply true -t 1 -r 1 -s 1 -n 0 -pn 1;
    for n in cmds.ls(sl=True, l=True, type='transform'):
        cmds.makeIdentity(n, apply=True, t=True, r=True, s=False, n=False, preserveNormals=True )


def mergeVertices():
    sel = cmds.ls(sl=True)
    oldcount = cmds.polyEvaluate(sel, v=True)
    for n in cmds.ls(sl=True, l=True, type='transform'):
        #polyMergeVertex  -d 0.001 -am 1 -ch 1 pCube2;
        cmds.polyMergeVertex(n, d=0.001, am=True, ch=True)

    cmds.select(sel, r=True)
    newcount = cmds.polyEvaluate(sel, v=True)
    msg = str(oldcount-newcount) + ' pairs of vertices were merged.'
    nerve.maya.UI.Dialog.Confirm(msg)

def extrude():
    import maya.mel as mel
    mel.eval('performPolyExtrude 0')

def edgeLoop():
    import maya.mel as mel
    mel.eval('SplitEdgeRingTool')

def flattenUVSets():
    sel = cmds.ls(sl=True, l=True)
    for n in sel:
        t,s = nerve.maya.Node.GetDagTuple(n)
        # To query the current uv set.
        uvSets = cmds.polyUVSet(s,q=True, allUVSets=True)
        if 'map1' not in uvSets:
            cmds.polyUVSet(s, create=True, uvSet='map1' )
        for uvSet in uvSets:
            if uvSet == 'map1':
                continue
            cmds.polyCopyUV(s, uvSetNameInput=uvSet, uvSetName='map1', ch=False)
    #        cmds.polyUVSet(s, copy=True, nuv='map1', uvSet=uvSet )
            cmds.polyUVSet(s, delete=True, uvSet=uvSet)    

def bevel():
    #sel = cmds.ls(sl=True, l=True)
    bevels = []
    for n in cmds.ls(sl=True, l=True):
        bevel = cmds.polyBevel3(n, offset=0.5, offsetAsFraction=True, autoFit=True, segments=1, worldSpace=True, smoothingAngle=30, depth=1, mitering=0, miterAlong=0, chamfer=True, subdivideNgons=True, mergeVertices=True, mergeVertexTolerance=0.0001, miteringAngle=180, angleTolerance=180)
        bevels+=bevel
    cmds.select(bevels, r=True)

def resetNormals():
    sel = cmds.ls(sl=True, l=True)
    import maya.mel as mel
    mel.eval('UnlockNormals;expandPolyGroupSelection;polySetToFaceNormal;polyPerformAction "polySoftEdge -a 30" e 0;')
    cmds.select(sel, r=True)

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
        cmds.select(mat, r=True)
        rsMats = nerve.maya.Material().Convert('RedshiftMaterial')
       
def rsConvertOpacityToSprite():
    materials = nerve.maya.Node.GetMaterials()
    for mat in materials:
        if cmds.nodeType(mat) != 'RedshiftMaterial':
            continue

        attrdata = nerve.maya.Node.GetAttrData(mat, 'opacity_color')
        if 'node' not in attrdata.keys():
            continue
        tex = nerve.maya.Node.findHistory( mat+'.opacity_color', 'file')
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
        mat = nerve.maya.Node.findHistory(sprite + '.input', 'RedshiftMaterial')
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

def substanceToRsMaterial():
    sel = cmds.ls(sl=True)
    if len(sel) and cmds.nodeType(sel[0]) == 'RedshiftMaterial':
        mat = sel[0]
    else:
        mat = nerve.maya.Node.create('RedshiftMaterial')

    files = nerve.maya.UI.Dialog.File(4)
    if not files:
        return False
    
    for filepath in files:
        filepath = nerve.Path(filepath)
        if '_Color' in filepath.GetName():
            tex = nerve.maya.Node.create('file')
            cmds.setAttr(tex + '.fileTextureName', filepath.AsString(), type='string')
            cmds.connectAttr(tex + '.outColor', mat + '.diffuse_color', f=True)
            continue
        if '_Metalness' in filepath.GetName():
            tex = nerve.maya.Node.create('file')
            cmds.setAttr(tex + '.fileTextureName', filepath.AsString(), type='string')
            cmds.setAttr(tex + '.colorSpace', 'Raw', type='string')
            cmds.setAttr(tex + '.alphaIsLuminance', True)
            cmds.setAttr(tex + '.ignoreColorSpaceFileRules', True)
            cmds.setAttr(mat + '.refl_fresnel_mode', 2)
            cmds.connectAttr(tex + '.outAlpha', mat + '.refl_metalness', f=True)
            continue        
        if '_Roughness' in filepath.GetName():
            tex = nerve.maya.Node.create('file')
            cmds.setAttr(tex + '.fileTextureName', filepath.AsString(), type='string')
            cmds.setAttr(tex + '.colorSpace', 'Raw', type='string')
            cmds.setAttr(tex + '.alphaIsLuminance', True)
            cmds.setAttr(tex + '.ignoreColorSpaceFileRules', True)
            cmds.connectAttr(tex + '.outAlpha', mat + '.refl_roughness', f=True)
            continue
        if '_Normal' in filepath.GetName():
            tex = nerve.maya.Node.create('RedshiftNormalMap')
            cmds.setAttr(tex + '.tex0', filepath.AsString(), type='string')
            cmds.connectAttr(tex + '.outDisplacementVector', mat + '.bump_input', f=True)
            continue
        if '_DisplaceHeightField' in filepath.GetName():
            disp = nerve.maya.Node.create('RedshiftDisplacement')
            cmds.setAttr(disp + '.newrange_min', -0.5)
            cmds.setAttr(disp + '.newrange_max', 0.5)
            cmds.setAttr(disp + '.scale', 0.05)
            tex = nerve.maya.Node.create('file')
            cmds.setAttr(tex + '.fileTextureName', filepath.AsString(), type='string')
            cmds.setAttr(tex + '.colorSpace', 'Raw', type='string')
            cmds.setAttr(tex + '.ignoreColorSpaceFileRules', True)
            cmds.connectAttr(tex + '.outColor', disp + '.texMap', f=True)
            sg = nerve.maya.Node.GetShadingEngines(mat)
            if sg:
                cmds.connectAttr(disp + '.out', sg[0] + '.displacementShader', f=True)
            continue

def connectCameraToOutlines():
    sel = cmds.ls(sl=True, l=True)
    if not len(sel):
        cmds.warning('Nothing selected')
        return False

    if nerve.maya.Node.GetType(sel[0]) != 'camera':
        cmds.warning('selection is not a camera')
        return False
    
    if cmds.nodeType(sel[0]) == 'transform':
        cam = sel[0]
    if cmds.nodeType(sel[0]) == 'camera':
        cam = cmds.listRelatives(sel[0], p=True)[0]

    for n in cmds.ls(type='pfxToon'):
        cmds.connectAttr(cam + '.translate', n +'.cameraPoint', f=True)

def rsConnectColorCorrect():
    sel = cmds.ls(sl=True)
    for n in sel:
        plugs = cmds.listConnections(n, s=False, d=True, plugs=True, c=True, skipConversionNodes=True)
        for i in range(0, len(plugs), 2):
            src = plugs[i]
            tar = plugs[i+1]
            srcnode = src.split('.')[0]
            tarnode = tar.split('.')[0]
            srcattr = '.'.join( src.split('.')[1:] )
            tarattr = '.'.join( tar.split('.')[1:] )        
                
            ntype = cmds.nodeType(tarnode)
            if not (cmds.getClassification(ntype, satisfies='shader') or cmds.getClassification(ntype, satisfies='texture') or cmds.getClassification(ntype, satisfies='utility')):
                continue

            cc = nerve.maya.Node.create('RedshiftColorCorrection', name=srcnode + '_CC')
            attrdata = nerve.maya.Node.GetAttrData(srcnode, srcattr)
            if attrdata['type'] == 'vector':
                print(srcnode + '.' + srcattr, cc + '.input')
                cmds.connectAttr(srcnode + '.' + srcattr, cc + '.input', f=True )
                print(cc + '.outColor', tarnode + '.' + tarattr)            
                cmds.connectAttr(cc + '.outColor', tarnode + '.' + tarattr, f=True)
            else:
                print(srcnode + '.' + srcattr, cc + '.inputR')            
                cmds.connectAttr(srcnode + '.' + srcattr, cc + '.inputR', f=True)
                print(cc + '.outColorR', tarnode + '.' + tarattr)            
                cmds.connectAttr(cc + '.outColorR', tarnode + '.' + tarattr, f=True)            

def importRsProxy():
    root  = cmds.ls('|*', type='transform')
    
    sel = cmds.ls(sl=True, l=True)
    for n in sel:
        if nerve.maya.Node.GetType(n) == 'mesh':
            obj = nerve.maya.Node.GetDagTuple(n)
            proxy = cmds.listConnections(obj[1], type='RedshiftProxyMesh')
            if proxy:
                proxy = proxy[0]
                path = cmds.getAttr(proxy + '.fileName')
                if 'nerve/assets' not in path:
                    cmds.warning(n + ' is not a nerve asset.')
                    continue
                assetpath = nerve.Path(path.split('nerve/assets/')[1]).GetParent()
                version = nerve.Path(path).GetVersion()
                asset = nerve.maya.asset(path=assetpath, version=version, format='mb')
                if asset.Exists():
                    nodes = asset.Gather()
                    if len(nodes) > 1:
                        cmds.warning('Asset is not grouped and cannot be moved to proxy position.')
                        continue
                        
                    cmds.select([nodes[0], obj[0]], r=True)
                    nerve.maya.tools.snap()
                    attr = 'nerve'
                    if not cmds.attributeQuery(attr, node=nodes[0], exists=True):
                        cmds.addAttr(nodes[0], ln=attr, dt="string")
                    cmds.setAttr(nodes[0] + '.nerve', asset.GetFilePath('session').AsString(), type='string')
                        
    cmds.select(sel, r=True)

def releaseMayaToProxy():
    sel = cmds.ls(sl=True, l=True)
    for n in sel:
        attr = 'nerve'
        if not cmds.attributeQuery(attr, n=n, exists=True):
            cmds.warning(n + ' was not imported from proxy. Do not know which asset it is.')
            continue
        path = cmds.getAttr(n + '.nerve')
        if 'nerve/assets' not in path:
            cmds.warning(n + ' is not a nerve asset.')
            continue
            
        assetpath = nerve.Path(path.split('nerve/assets/')[1]).GetParent()
        version = nerve.Path(path).GetVersion()
        asset = nerve.maya.asset(path=assetpath, version=version, format='mb')
        for a in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
            cmds.setAttr(n + '.' + a, 0)
        for a in ['sx', 'sy', 'sz']:
            cmds.setAttr(n + '.' + a, 1)
        cmds.select(n, r=True)
        asset.Release()
        asset = nerve.maya.asset(path=assetpath, version=version, format='rs')        
        cmds.select(n, r=True)
        asset.Release()

        nerve.maya.UI.Dialog.Confirm('Asset re-released')

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

def localRender(renderLayer=False, run=True):
    print(renderLayer)
    import os
    mayaPath = nerve.Path(os.environ['MAYA_LOCATION']) + 'bin' + 'Render.exe'
    scene = cmds.file(q=True, sn=True)
    renderPath = nerve.Path(cmds.workspace(q=True, rootDirectory=True)) + 'renders'
    renderer = cmds.getAttr( "defaultRenderGlobals.currentRenderer" )

    #renderer = 'redshift'

    # arnold
    if renderer == "arnold":
        rendererFlags = '-r arnold -ai:ltc 1 -ai:lve 2'
    # redshift
    elif renderer == "redshift":
        rendererFlags = '-r redshift -gpu {0}'
    # maya hardware
    elif renderer == 'mayaHardware2':
        rendererFlags = '-r hw2'
    else:
        cmds.error('Current rerderer not supported ('+renderer+')')
        return False

    if renderLayer:
        rendererFlags+= ' -rl {}'.format(cmds.editRenderLayerGlobals(q=True,currentRenderLayer=True))

    # Frames
    startFrame = int(cmds.playbackOptions(q=True, min=True))
    endFrame = int(cmds.playbackOptions(q=True, max=True))

    frameStr = str(startFrame) + '-' + str( endFrame )
    result = cmds.promptDialog(title='Frames', message='Enter Frame List:', button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel', text=frameStr)
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

    print(cmd),

    if run:
        batfilepath = os.environ["TEMP"] + '/localRender.bat'
        batfile = open(batfilepath, 'w')
        batfile.write('set MAYA_ENABLE_LEGACY_RENDER_LAYERS=1\n'+cmd)
        batfile.close()

        os.system('start "" '+batfilepath+'')


def repathTextures():
    targetPath = 'N:/jobs/dallas/krotiri/maya/assets/plants/Maxtree - Plant Models Vol. 23olea\MT_PM_V23_Maps/'
    filenames = []
    for f in nerve.Path.Glob(targetPath + '/*.*'):
        f = nerve.Path(f)
        filenames.append(f.GetHead())

    nodetypes = {'file':'fileTextureName', 'RedshiftNormalMap':'tex0', 'RedshiftSprite':'tex0'}
    for ntype, attr in nodetypes.items():
        for n in cmds.ls(type=ntype):
            inpath = nerve.Path( cmds.getAttr(n + '.'+attr) )
            filename = inpath.GetHead()
            if filename in filenames:
                cmds.setAttr(n + '.' + attr, targetPath+'/'+filename, type='string')
            else:
                print('{} not found.'.format(filename))

            
                

def createQuickLightSetup():

    
    cmds.file("N:/library/input/QuickLightSetup.mb", i=True, type='MayaBinary', ignoreVersion=True, ra=True, mergeNamespacesOnClash=False, namespace='QLS', pr=True)

    '''
    dome = nerve.maya.Node.create('RedshiftDomeLight', 'DOME')
    dome = nerve.maya.Node.GetDagTuple(dome)
    cmds.setAttr(dome[1] + '.tex0', 'N:\library\input\hdri\3_3DCollective - Real Light 24HDRi Pro Pack 03\4K\3DCollective_HDRi_093_1746_4K.hdr', type='string')
    cmds.setAttr(dome[1] + '.background_enable', False)

    area = nerve.maya.Node.create('RedshiftPhysicalLight', 'AREA')
    area = nerve.maya.Node.GetDagTuple(area)
    
    cmds.setAttr(area[0] + '.tz', 500)
    cmds.setAttr(area[0] + '.sx', 100)
    cmds.setAttr(area[0] + '.sy', 100)    
    cmds.setAttr(area[0] + '.sz', 100)
    
    cmds.setAttr(area[1] + '.areaVisibleInRender', False)
    cmds.setAttr(area[1] + '.intensity', 10)
    
    grp = cmds.group(em=True, n='Area_grp')
    area = cmds.parent(area[0], grp)
    
    cmds.setAttr(grp + '.rx', -27)
    cmds.setAttr(grp + '.ry', 45)    
    '''
