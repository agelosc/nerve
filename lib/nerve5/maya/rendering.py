import maya.cmds as cmds
import maya.mel as mel
import maya.utils as mu


from functools import partial
import os

def UI():
    data = []
    data.append( {'label':'Local Render', 'command':localRender} )
    data.append( {'type':'seperator'} )
    data.append( {'label':'Connect Physical Sun&Sky', 'command':ConnectSunAndSky} )
    data.append( {'type':'seperator'} )    
    data.append( {'label':'Redshift Depth Shader', 'command':redshiftDepth} )
    data.append( {'label':'Redshift Depth Shader With Transparency', 'command':redshiftDepthWithTransparency} )
    data.append( {'type':'seperator'} )
    data.append( {'label':'Disable Smooth Preview for Render', 'command':disableSmoothRender} )
    data.append( {'label':'Enable Smooth Preview for Render', 'command':enableSmoothRender} )
    data.append( {'type':'seperator'} )
    data.append( {'label':'Enable Redshift Tesselation', 'command':enableRsTesselation} )
    data.append( {'label':'Disable Redshift Tesselation', 'command':disableRsTesselation} )

    return data
    
def ConnectSunAndSky(*args):
    sel = cmds.ls(sl=True, l=True)
    if not len(sel):
        cmds.warning('Nothing selected')
        return False
        
    obj = sel[0]
    shape = None
    if cmds.nodeType(obj) == 'transform':
        shape = cmds.listRelatives(obj, s=True)[0]
    if cmds.nodeType(obj) == 'RedshiftPhysicalSun':
        shape = obj
        obj = cmds.listRelatives(shape, p=True)[0]
        
    if cmds.nodeType(shape) != 'RedshiftPhysicalSun':
        cmds.warning('Selection is not a Redshift PhysicalSun&Sky object.')
        return False
        
    rsSky = cmds.listConnections(shape, type='RedshiftPhysicalSky') or []
    if not len(rsSky):
        cmds.warning('Cannot find RedshiftPhysicalSky node. ')
        return False
    rsSky = rsSky[0]
    

    rsOptions = cmds.ls(type='RedshiftOptions') or []
    if not len(rsOptions):
        cmds.warning('RedshiftOptions not found. Check Redshift plugin is loaded and Redshift is used as the current renderer.')
        return False
        
    if not cmds.objExists(rsOptions[0]):
        cmds.warning('RedshiftOptions not found. Check Redshift plugin is loaded and Redshift is used as the current renderer.')
        return False
    
    rsOptions = rsOptions[0]
    
    rsPostEffects = cmds.ls(type='RedshiftPostEffects')
    if not len(rsPostEffects):
        cmds.warning('RedshiftPostEffects node not found. Check Redshift plugin is loaded and Redshift is used as the current renderer.')
        return False
    rsPostEffects = rsPostEffects[0]
    
    cmds.connectAttr(rsSky + '.message', rsOptions+'.physicalSky', f=True)    
    cmds.connectAttr(rsSky + '.message', rsOptions+'.environment', f=True)        
    cmds.connectAttr(rsPostEffects + '.message', rsSky + '.rsSkyExposure', f=True)        

def enableRsTesselation(*args):
    sel = cmds.ls(sl=True, l=True)
    cmds.select(hi=True)
    objects = cmds.ls(sl=True, l=True, type='shape')
    for obj in objects:
        if not cmds.attributeQuery('rsEnableSubdivision', n=obj, exists=True):
            continue
        cmds.setAttr(obj + '.rsEnableSubdivision', 1)

    cmds.select(sel, r=True)

def disableRsTesselation(*args):
    sel = cmds.ls(sl=True, l=True)
    cmds.select(hi=True)
    objects = cmds.ls(sl=True, l=True, type='shape')
    for obj in objects:
        if not cmds.attributeQuery('rsEnableSubdivision', n=obj, exists=True):
            continue
        cmds.setAttr(obj + '.rsEnableSubdivision', 0)

    cmds.select(sel, r=True)

def disableSmoothRender(*args):
    sel = cmds.ls(sl=True, l=True)
    cmds.select(hi=True)
    objects = cmds.ls(sl=True, l=True, type='shape')
    for obj in objects:
        cmds.setAttr(obj + '.useSmoothPreviewForRender', 0)
        cmds.setAttr(obj + '.renderSmoothLevel', 0)
    cmds.select(sel, r=True)

def enableSmoothRender(*args):
    sel = cmds.ls(sl=True, l=True)
    cmds.select(hi=True)
    objects = cmds.ls(sl=True, l=True, type='shape')
    for obj in objects:
        cmds.setAttr(obj + '.useSmoothPreviewForRender', 1)
        cmds.setAttr(obj + '.renderSmoothLevel', 2)
    cmds.select(sel, r=True)



def redshiftDepth(*args):
    cmds.file( 'R:/jobs/Mascista/build/build/maya/scenes/shaders/RedshiftDepthShader.mb', i=True, type="mayaBinary", ra=True, mergeNamespacesOnClash=True, namespace=':', options='v=0', pr=True )

def redshiftDepthWithTransparency(*args):
    sel = cmds.ls(sl=True, l=True)

    # Original Depth Shader
    dctrl = 'DepthShader_camPos'
    if not cmds.objExists(dctrl):
        redshiftDepth()
    '''
    if not cmds.attributeQuery( 'blendDepth', exists=True, n=dctrl ):
        cmds.addAttr(dctrl, ln='blendDepth', at='double', min=0, max=1, dv=1, k=True)
    '''
    setRange = cmds.listConnections( dctrl, type="setRange" )[0]

    for n in sel:
        if cmds.nodeType(n) == 'transform':
            n = cmds.listRelatives(n, s=True, type="mesh", f=True)
            if n is None:
                continue
            else:
                n = n[0]

        sgs = cmds.listConnections(n, type="shadingEngine")
        if sgs is None:
            continue

        for sg in sgs:
            shader = cmds.listConnections(sg + ".surfaceShader")[0]
            if cmds.attributeQuery('depthMessage', exists=True, n=shader):
                print 'Depth Shader already connected'
                continue

            depth = cmds.listConnections(setRange, type="surfaceShader")[0]

            textures = None
            # SHADER TYPES
            if cmds.nodeType(shader) == 'surfaceShader':
                # Surface Shader
                textures = cmds.listConnections(shader + '.outMatteOpacity', p=True)
                if textures is None:
                    textures = cmds.listConnections(shader + '.outMatteOpacityR', p=True)
            elif cmds.nodeType(shader) == 'RedshiftMaterial':
                # Redshift Material
                textures = cmds.listConnections(shader + '.opacity_color', p=True)
                if textures is None:
                    textures = cmds.listConnections(shader + '.opacity_colorR', p=True)
            else:
                cmds.warning("Unsupported Shader Type: " + cmds.nodeType(shader))
                continue

            if textures is None:
                # Default Depth Shader
                cmds.connectAttr(depth + '.outColor', sg + '.surfaceShader', f=True)
                if not cmds.attributeQuery('depthMessage', exists=True, n=depth):
                    cmds.addAttr(depth, ln='depthMessage', at='bool', dv=1, k=False)
            else:
                # Custom Depth Shader
                texture = textures[0]
                css = cmds.createNode("surfaceShader")
                cmds.addAttr(css, ln='depthMessage', at='bool', dv=1, k=False)

                mult = cmds.createNode("multiplyDivide")

                # Color
                cmds.connectAttr( setRange + '.outValue', mult + '.input1', f=True )
                if cmds.attributeQuery(texture.split('.')[-1], at=True, n=texture.split('.')[0]) == 'float3':
                    cmds.connectAttr(texture, mult + '.input2', f=True)
                else:
                    cmds.connectAttr(texture, mult + '.input2X', f=True)
                    cmds.connectAttr(texture, mult + '.input2Y', f=True)
                    cmds.connectAttr(texture, mult + '.input2Z', f=True)
                cmds.connectAttr(mult + '.output', css + '.outColor', f=True)

                # Out Transparency
                reverse = cmds.listConnections(texture, type="reverse")
                if reverse is None:
                    reverse = cmds.createNode('reverse')
                    if cmds.attributeQuery(texture.split('.')[-1], at=True, n=texture.split('.')[0]) == 'float3':
                        cmds.connectAttr(texture, reverse + '.input', f=True)
                    else:
                        cmds.connectAttr(texture, reverse + '.inputX', f=True)
                        cmds.connectAttr(texture, reverse + '.inputY', f=True)
                        cmds.connectAttr(texture, reverse + '.inputZ', f=True)
                else:
                    reverse = reverse[0]
                cmds.connectAttr( reverse + '.output', css + '.outTransparency', f=True )

                # Out Matte Opacity
                if cmds.attributeQuery(texture.split('.')[-1], at=True, n=texture.split('.')[0]) == 'float3':
                    cmds.connectAttr(texture, css + '.outMatteOpacity', f=True)
                else:
                    cmds.connectAttr(texture, css + '.outMatteOpacityR', f=True)
                    cmds.connectAttr(texture, css + '.outMatteOpacityG', f=True)
                    cmds.connectAttr(texture, css + '.outMatteOpacityB', f=True)


                # Connect Shader To ShadingEngine
                cmds.connectAttr(css + '.outColor', sg + '.surfaceShader', f=True)



def localRender(*args):
    # PATH
    c = {}
    paths = ['D:/Program Files/Autodesk/Maya2022/bin/', 'C:/Program Files/Autodesk/Maya2022/bin/']
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
    print cmd

    batfilepath = os.environ["TEMP"] + '/localRender.bat'
    batfile = open(batfilepath, 'w')
    batfile.write(cmd)
    batfile.close()

    os.system('start "" '+batfilepath+'')
