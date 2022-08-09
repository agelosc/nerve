import maya.cmds as cmds
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
        if con is None:
            return data
        
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
    shape = cmds.listRelatives( obj, s=True, f=True, ni=True)[0]
    shadingEngines = cmds.listConnections(shape, type='shadingEngine')
    
    # Error Check
    if shadingEngines is None:
        nerve.maya.confirm("Object has no shading engine. Check SE for details.")
        print shape
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

print '#####'
import pprint
pp = pprint.PrettyPrinter()
pp.pprint(shadingData)  
