import maya.cmds as cmds
import maya.mel as mel
import os

def deadlineRender(*args):
    mel.eval('DeadlineMayaClient();SubmitJobToDeadline;')

def localRender(*args):
    # PATH
    c = {}
    paths = ['D:/Program Files/Autodesk/Maya2020/bin/', 'C:/Program Files/Autodesk/Maya2020/bin/']
    path = ''
    for p in paths:
        if os.path.exists(p):
            path = p

    c["render"] = '"%sRender.exe"'%path

    # SCENE
    scene = cmds.file(q=True, sn=True)
    # RENDER PATH
    renderPath = cmds.workspace(q=True, rootDirectory=True) + "renders"
    # RENDERER
    renderer = cmds.getAttr( "defaultRenderGlobals.currentRenderer" )

    if True:
        # arnold
        if renderer == "arnold":
            rendererFlags = '-r arnold -ai:ltc 1 -ai:lve 2'
        # REDSHIFT
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

    FrameStr = str(startFrame) + '-' + str( endFrame )

    result = cmds.promptDialog(title='Rename Object', message='Enter Frame List:', button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel', text=FrameStr)

    if result == 'OK':
        FrameStr = cmds.promptDialog(query=True, text=True)
    else:
        return False

    FrameList = []
    FramePairs = FrameStr.replace(' ', '').split(',')
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
        cmd+= c["render"] + ' '+rendererFlags+' -s '+str(frames[0])+' -e '+str(frames[1])+' -b 1 -rd "' + renderPath + '" "' + scene + '"\n'
    print(cmd)

    batfilepath = os.environ["TEMP"] + '/localRender.bat'
    batfile = open(batfilepath, 'w')
    batfile.write(cmd)
    batfile.close()

    os.system('start "" '+batfilepath+'')

def GetObjectTuple(obj):
    trans = None
    shape = None
    if cmds.nodeType(obj) == 'transform':
        trans = obj
        if cmds.listRelatives(obj, s=True):
            shape = cmds.listRelatives(obj, s=True)[0]
    else:
        shape = obj
        if cmds.listRelatives(obj, p=True):
            trans = cmds.listRelatives(obj, p=True)[0]

    return (trans, shape)

def Snap(obj, dest, pos=True, rot=True, scale=True):
    if cmds.nodeType(obj) != 'transform' or cmds.nodeType(dest) != 'transform':
        cmds.warning("Selection Error.")
        return False

    vpos = cmds.xform(dest, q=True, ws=True, t=True)
    vrot = cmds.xform(dest, q=True, ws=True, ro=True)
    vsca = cmds.xform(dest, q=True, ws=True, s=True)

    if pos:
        cmds.xform(obj, ws=True, t=(vpos[0], vpos[1], vpos[2]))
    if rot:
        cmds.xform(obj, ws=True, ro=(vrot[0], vrot[1], vrot[2]))
    if scale:
        cmds.xform(obj, ws=True, s=(vsca[0], vsca[1], vsca[2]))

def Explore(self, *args):
    path = cmds.workspace(query=True, rootDirectory=True).replace('/', '\\')
    os.system('start explorer "{}"'.format(path))

if True: # Utilities
    def ClearNamespaces(self, *args):
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

    def ImportReference(*args):

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

    def RemoveReference(*args):
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

    def DuplicateReference(*args):
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

    def LocatorToPivot(self, *args):
        sel = cmds.ls(sl=True, l=True)
        for n in sel:
            name = n.split("|")[-1].split(":")[-1]
            pos = cmds.xform(n, q=True, ws=True, piv=True)
            rot = cmds.xform(n, q=True, ws=True, ro=True)

            loc = cmds.spaceLocator(p=(0, 0, 0))
            cmds.xform(loc[0], ws=True, t=(pos[0], pos[1], pos[2]))
            cmds.xform(loc[0], ws=True, ro=(rot[0], rot[1], rot[2]))
            cmds.rename(loc[0], name)

    def LocatorToAverage(self, *args):
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

    def RemoveUnknownNodes(*args):
        nodes = cmds.ls(type='unknown')
        for n in nodes:
            print('Deleting: '+n)

        if len(nodes):
            cmds.delete(nodes)
        else:
            print('No unknown nodes found.',)

    def RemoveUnknownPlugins(*args):
        unknownPlugins = cmds.unknownPlugin(q=True, list=True)
        if unknownPlugins is None:
            print('No unknown plugins found.',)
            unknownPlugins = []
        for up in unknownPlugins:
            print('Deleting: '+up)
            cmds.unknownPlugin(up, remove=True)

    def RemoveTurtle(*args):
        nodes = ['TurtleDefaultBakeLayer', 'TurtleRenderOptions', 'TurtleUIOptions', 'TurtleBakeLayerManager']
        for node in nodes:
            if cmds.objExists(node):
                cmds.lockNode(node, l=False)
                cmds.delete(node)
        cmds.unloadPlugin("Turtle.mll",f=True)

if True: # Animation
    def CameraRig(*args):
        sel = cmds.ls(sl=True, l=True)

        nodes = cmds.file(os.environ['NERVE_LOCAL_PATH'] + '/apps/maya/assets/CameraRig.ma', r=True, namespace='CameraRig', type='mayaAscii', options='v=0', mergeNamespacesOnClash=False, returnNewNodes=True)
        camera = 'CameraRig:CameraRig'
        cameraMain = 'CameraRig:CameraRig_world_ctrl'

        if len(sel):
            obj = GetObjectTuple(sel[0])
            if obj[1] and cmds.nodeType(obj[1]) == 'camera':
                Snap(cameraMain, obj[0], scale=False)
                cmds.parentConstraint(camera, obj[0], mo=True, w=1)
                cmds.setAttr(obj[0] + '.locatorScale', 0.1)
                cmds.select(obj[0], r=True)

    def SnapFromTo(*args):
        sel = cmds.ls(sl=True, l=True)
        if len(sel) != 2:
            cmds.warning('Selection error. Skipping...')
            return False
        Snap(sel[0], sel[1])

    def CreateDOFCtrl(*args):
        sel = cmds.ls(sl=True, l=True)
        if not sel:
            cmds.warning('Nothing selected...')
            return False

        transform = sel[0]
        shape = sel[0]
        if cmds.nodeType(transform) == 'transform':
            shape = cmds.listRelatives(transform, s=True)
            if shape is None:
                cmds.warning('Selected object is not a camera.')
                return False
            shape = shape[0]
            if cmds.nodeType(shape) != 'camera':
                cmds.warning('Selected object is not a camera.')
                return False
        else:
            if cmds.nodeType(transform) != 'camera':
                cmds.warning('Selected object is not a camera.')
                return False

            shape = transform
            transform = cmds.listRelatives(shape, p=True)[0]

        name = transform.split('|')[-1]
        group = cmds.group(em=True, name=name+'_DOF_grp')
        loc = cmds.spaceLocator(p=(0,0,0), name=name+'_DOF')

        loc = cmds.parent(loc, group)
        cmds.parentConstraint(transform, group, mo=False, w=1)
        for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
            cmds.setAttr(group+'.'+attr, lock=True)

        for attr in ['tx', 'ty', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
            cmds.setAttr(loc[0]+'.'+attr, lock=True)

        inv = cmds.createNode('multiplyDivide', name=name+'_inv')
        cmds.setAttr(inv+'.input2X', -1)
        cmds.setAttr(inv+'.input2Y', -1)
        cmds.setAttr(inv+'.input2Z', -1)

        cmds.connectAttr(loc[0] + '.tz', inv+'.input1Z', f=True)
        cmds.connectAttr(inv + '.outputZ', shape+'.focusDistance', f=True)

        cmds.setAttr(loc[0] + '.tz', -2)

    def SelectSceneAnimation(*args):
        # SCALE & VISIBILITY
        animCurves = cmds.ls(type="animCurveTU")
        # ROTATION
        animCurves.extend( cmds.ls(type="animCurveTA") )
        # TRANSLATE
        animCurves.extend( cmds.ls(type="animCurveTL") )

        objects = []
        for n in animCurves:
            if not cmds.referenceQuery(n, isNodeReferenced=True):
                tmp = cmds.listConnections(n + ".output")
                if tmp is not None:
                    tmp = list(set(tmp))
                    objects.extend(tmp)

        cmds.select(objects,r=True)

    def StudioLibrary(*args):
        import studiolibrary
        library = cmds.workspace(q=True, o=True) + '/studiolibrary'
        studiolibrary.main(name="Global", path=library)
