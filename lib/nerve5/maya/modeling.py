import maya.cmds as cmds
import maya.mel as mel

from functools import partial

def UI():
    data = []
    data.append( { 'label':'Poly Unite', 'command':polyUnite } )
    data.append( { 'label':'Poly Smooth', 'command':polySmooth } )
    data.append( { 'label':'Extract Face Assignments', 'command':ExtractFaceAssignments } )
    
    return data

def ExtractFaceAssignments(*args):
    dup = False
    if len(args):
        dup = args[0]

    def getShadingEngineObjects(shadingEngine, object):
    
        objlist = []
        parent = cmds.listRelatives(object, p=True)[0]
        assigned = cmds.sets(shadingEngine, q=True)
        for ass in assigned:
            if ass.split('.')[0].split('|')[-1] == parent.split('|')[0]:
                objlist.append(ass)
            
        return objlist
        
    def assignShader(shader, object):
        cmds.scriptEditorInfo(sw=True)
        cmds.select(object, r=True)
        cmds.hyperShade(a=shader)
        cmds.scriptEditorInfo(sw=False)
        
        return True
        
    def getShadingEngines(obj):
        shadingEngines = cmds.listConnections(obj, type="shadingEngine")
        shadingEngines = list(set(shadingEngines))
        if 'initialShadingGroup' in shadingEngines:
            shadingEngines.remove('initialShadingGroup')    

        return shadingEngines

    def mostPopular(data):
        if len(data) == 0:
            return -1
            
        return max(set(data), key=data.count)
                

    msg = []
    osn = []
    os = cmds.ls(sl=True, l=True)
    if not len(os):
        print "Nothing Selected."
        return False
    
    cmds.select(hi=True)
    sel = cmds.ls(sl=True, l=True, type="mesh")
    
    for n in sel:
            
        shadingEngines = getShadingEngines(n)
        if len(shadingEngines) <= 1:
            # Check for face assignment
            for shadingEngine in shadingEngines:
                objects = getShadingEngineObjects(shadingEngine, n)
                if len(objects):
                    if '.f[' in objects[0]:
                        a = cmds.listConnections(shadingEngine)
                        shader = cmds.listConnections(shadingEngine + ".surfaceShader")[0]
                        
                        #shader = cmds.ls(cmds.listConnections(shadingEngine), materials=True)[-1]
                        
                        cmds.select(objects[0].split('.')[0], r=True)
                        assignShader(shader, n)
                        msg.append("Re assigning shader " + shader + " to " + n)
            continue
        

        if dup:
            cmds.duplicate(rr=True)[0]
            n = cmds.ls(sl=True, l=True)[0]
            n  = cmds.listRelatives(n, s=True, f=True)[0]
        
        parent = cmds.listRelatives(n, p=True)[0]
        parentPath = cmds.listRelatives(n, p=True, f=True)[0]
        msg.append("Separating Object: " + parent)
        
        for shadingEngine in shadingEngines:
            objlist = getShadingEngineObjects(shadingEngine, n)
            cmds.polyChipOff(objlist, ch=False, keepFacesTogether=True, duplicate=False, offset=False)
            
        # Seperate
        nodes = cmds.polySeparate(n, ch=False, object=True, n=parent + '_SHS_1')
        
        # Sort by shading Engine
        nodePerShadingEngine = {}
        for node in nodes:
            obj = cmds.listRelatives(node, s=True, type="mesh", fullPath=True)
            if obj is None:
                continue
            obj = obj[0]
            
            shadingEngines = getShadingEngines(obj)
            key = shadingEngines[0]
            if key not in nodePerShadingEngine.keys():
                nodePerShadingEngine[key] = []
            nodePerShadingEngine[key].append(obj)
            
            
        # for every shading group
        for se in nodePerShadingEngine.keys():
            o = nodePerShadingEngine[se][0]
            
            # Unite if more than one object
            if len(nodePerShadingEngine[se]) > 1:
                unite = cmds.polyUnite(nodePerShadingEngine[se], ch=False, mergeUVSets=True, n=parent + '_SHS_1')
                cmds.parent(unite, parentPath)
                o = cmds.ls(sl=True, l=True)[0]
                o = cmds.listRelatives(o, s=True, f=True)[0]

            # Assign Shader
            shader = cmds.ls(cmds.listConnections(se), materials=True)[-1]
            assignShader(shader,o)
            assigned = cmds.sets(se, q=True)
            
            # Get Matarial ID
            materialIdList = []
            for ass in assigned:
                if ass == o or '.f[' in ass or cmds.nodeType(ass) != "mesh":
                    continue

            osn.append(o)
            
    if len(osn):
        cmds.select(osn, r=True)
    else:
        cmds.select(os, r=True)    
    
def polyUnite(*args):
    # SELECTION
    sel = cmds.ls(sl=True, l=True)
    for i in range(0, len(sel)):
        if cmds.nodeType(sel[i]) == "transform":
            tmp = cmds.listRelatives(sel[i], s=True, f=True)
            sel[i] = tmp[0]
            
    unite = cmds.createNode("polyUnite")
    for i in range(0, len(sel)):
        cmds.connectAttr(sel[i] + ".outMesh", unite + ".inputPoly["+str(i)+"]", force=True)
        cmds.connectAttr(sel[i] + ".worldMatrix[0]", unite + ".inputMat["+str(i)+"]", force=True)

    mesh = cmds.createNode("mesh")
    cmds.connectAttr(unite + ".output", mesh + ".inMesh", force=True)

    return mesh        
    
def polySmooth(*args):
    sel = cmds.ls(sl=True, l=True)
    for n in sel:
        obj = n
        if cmds.nodeType( obj ) == 'transform':
            obj = cmds.listRelatives(obj, s=True, pa=True, ni=True)[0]

        if cmds.nodeType(obj) != 'mesh':
            continue

        con = cmds.duplicate( n, rr=True)[0]
        #cmds.move(0,0,2, con, r=True, os=True, wd=True)
        conShape = cmds.listRelatives(con, s=True, pa=True, ni=True)[0]
        
        args = {}
        args['method'] = 0
        args['subdivisionType'] = 2
        args['osdVertBoundary'] = 1
        args['osdFvarBoundary'] = 3
        args['osdFvarPropagateCorners'] = 0
        args['osdSmoothTriangles'] = 0
        args['osdCreaseMethod'] = 0
        args['divisions'] = 1
        args['continuity'] = 1
        args['keepBorder'] = 1
        args['keepSelectionBorder'] = 1
        args['keepHardEdge'] = 1
        args['keepTessellation'] = 1
        args['keepMapBorders'] = 1
        args['smoothUVs'] = 1
        args['keepBorder'] = 1
        args['propagateEdgeHardness'] = 0
        args['subdivisionLevels'] = 1
        args['divisionsPerEdge'] = 1
        args['pushStrength'] = 0.1
        args['roundness'] = 1
        args['constructionHistory'] = 1
    
        #smoothTmp = cmds.polySmooth(obj, **args)[0]
        smooth = cmds.polySmooth(conShape, **args)[0]
        cmds.connectAttr( obj + '.outMesh', smooth + '.inputPolymesh', f=True)
        
        #transferShaders(n.split('|')[-1], con)
        
        con = cmds.rename( con, obj.split('|')[-1] + '_highRez' )
        try:
            cmds.parent(con, w=True)
        except:
            pass
        
def transferShaders(src, des):
    shape = src
    if cmds.nodeType(shape) == 'transform':
        shape = cmds.listRelatives(shape, s=True, f=True, ni=True)[0]
    
    shadingEngines = cmds.listConnections(shape, type='shadingEngine')
    if shadingEngines is None:
        shadingEngines = []
        
    shadingEngines = list(set(shadingEngines))
    for shadingEngine in shadingEngines:
        members = cmds.sets(shadingEngine, q=True)
        if members is None:
            continue
        for member in members:
            print src
            print des
            print ''
            target = member.replace( src, des )
            
            print target
            cmds.sets(target, fe=shadingEngine)
    
    
    