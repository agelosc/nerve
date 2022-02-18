import maya.cmds as cmds
import maya.mel as mel
import maya.utils as mu

from functools import partial

import nerve5 as nerve
import os

def UI():
    data = []

    data.append( {'label':'Rig Template', 'command':RigTemplate} )
    #data.append( {'label':'Remap Textures...', 'command':remapTexturesUI} )
    data.append( {'label':'Copy Textures To sourceimages', 'command':copySceneTexturesToProject} )

    data.append( {'type':'seperator'} )

    data.append( {'label':'Add Vis Attribute', 'command':addVizAttrib} )
    data.append( {'label':'Make Pivot Keyable', 'command':makePivotKeyable} )
    data.append( {'label':'Ctrl Selected', 'command':ctrlSelected} )
    data.append( {'type':'seperator'} )

    data.append( {'label':'Deactivate Selected Skin Clusters', 'command':deactivateSkinCluster} )
    data.append( {'label':'Activate Selected Skin Cluster', 'command':activateSkinCluster} )
    data.append( {'type':'seperator'} )

    data.append( {'label':'Deactivate All Skin Clusters ', 'command':activateMoveJointsALL} )
    data.append( {'label':'Active All Skin Clusters', 'command':deactivateMoveJointsALL} )
    data.append( {'type':'seperator'} )

    data.append( {'label':'Import Handles', 'command':importHandles} )
    data.append( {'type':'seperator'} )

    data.append( {'ctrl':'color', 'type':'submenu', 'label':'Color'} )
    data.append( {'label':'Red', 'command':partial(setColor, 'red'), 'parent':'color'} )
    data.append( {'label':'Blue', 'command':partial(setColor, 'blue'), 'parent':'color'} )
    data.append( {'label':'Purple', 'command':partial(setColor, 'purple'), 'parent':'color'} )
    data.append( {'label':'Green', 'command':partial(setColor, 'green'), 'parent':'color'} )
    data.append( {'label':'Yellow', 'command':partial(setColor, 'yellow'), 'parent':'color'} )
    data.append( {'label':'Light Blue', 'command':partial(setColor, 'lightBlue'), 'parent':'color'} )
    data.append( {'label':'Light Green', 'command':partial(setColor, 'lightGreen'), 'parent':'color'} )
    data.append( {'label':'Pink', 'command':partial(setColor, 'pink'), 'parent':'color'} )
    data.append( {'label':'White', 'command':partial(setColor, 'white'), 'parent':'color'} )

    return data

def remapTexturesUI(*args):
    def UI(*args):
        parent = cmds.setParent(q=True)

        cmds.rowColumnLayout()

        textures = cmds.ls(type='file')
        for texture in textures:
            ftn = cmds.getAttr(texture+'.fileTextureName')
            cmds.rowLayout()
            if True:
                rows = cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1,50), (2,600)], columnAttach=[(1,'right', 10), (2,'left', 10)])
                cmds.textField(text=texture, editable=False, parent=rows, width=600)
                cmds.textField(text=ftn, editable=False, parent=rows, width=600)
                cmds.setParent('..')
            cmds.setParent('..')

    cmds.layoutDialog(ui=UI)



def copySceneTexturesToProject(*args):
    from shutil import copyfile

    workspace = cmds.workspace(q=True, o=True)
    result = cmds.promptDialog( title='Folder', message='Enter Folder Name: ', button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel' )
    if result == 'OK':
        folder = cmds.promptDialog(q=True, text=True)
    else:
        return False

    path = workspace + '/sourceimages/' + folder

    sel = cmds.ls(type='file')
    textures = []
    missing = {}

    for n in sel:
        ftn = cmds.getAttr(n + '.fileTextureName')
        ftn.replace('\\', '/')
        basename = ftn.split('/')[-1]

        if not os.path.isfile(ftn):
            if os.path.exists(path+'/'+basename):
                cmds.setAttr(n + '.fileTextureName', path+'/'+basename, type='string')
                continue

            missing[n] = ftn


        if not os.path.isdir(path):
            os.makedirs(path)

        print 'Copying %s -> %s'%( ftn, path+'/'+basename )

        copyfile(ftn, path+'/'+basename)
        cmds.setAttr(n + '.fileTextureName', path+'/'+basename, type='string')

        if len(missing.keys()):
            cmds.confirmDialog( title='Missing Textures', message='Some textures were not found. Check script editor for details.', button=['Yes'], defaultButton='Yes')
            for m in missing.keys():
                print 'Texture Node: ' + m
                print 'Path: ' + missing[m]
                print ''


def importHandles(*args):
    cmds.file( 'R:/jobs/Mascista/build/build/maya/scenes/ctrls/Handles.mb', i=True, type="mayaBinary", ra=True, mergeNamespacesOnClash=True, namespace=':', options='v=0', pr=True )

def ctrlSelected(*args):
    result = cmds.promptDialog(title="Rename Control", message="Enter Name:", button=["OK", "Cancel"], defaultButton='OK', dismissString='Cancel')
    if result != 'OK':
        print "Canceled...",
        return False

    sel = cmds.ls(sl=True)
    target = sel[0]

    if len(sel)>1:
        dup = cmds.duplicate(sel[1], rr=True)[0]
        cmds.parent(dup, w=True)
        ctrl = cmds.ls(sl=True)[-1]
    else:
        ctrl = cmds.circle( c=(0,0,0), nr=(0,1,0), sw=360, r=1, d=3, ut=0, tol=0.0001, s=8, ch=True )[0]

    pos = cmds.xform(target, q=True, ws=True, piv=True)
    rot = cmds.xform(target, q=True, ws=True, ro=True)

    text = cmds.promptDialog(query=True, text=True)
    if text == '':
        text = '_'.join(sel[0].split('_')[:-1])


    null = cmds.group(em=True, name=text + "_null")
    grp = cmds.group(em=True, name=text + "_grp")

    cmds.xform(null, ws=True, t=(pos[0], pos[1], pos[2]))
    cmds.xform(null, ws=True, ro=(rot[0], rot[1], rot[2]))

    cmds.xform(grp, ws=True, t=(pos[0], pos[1], pos[2]))
    cmds.xform(grp, ws=True, ro=(rot[0], rot[1], rot[2]))

    cmds.xform(ctrl, ws=True, t=(pos[0], pos[1], pos[2]))
    cmds.xform(ctrl, ws=True, ro=(rot[0], rot[1], rot[2]))

    cmds.pointConstraint(ctrl, target, mo=True, weight=1.0)
    cmds.orientConstraint(ctrl, target, mo=True, weight=1.0)

    cmds.rename(ctrl, text+"_ctrl")
    cmds.parent(text+"_ctrl", grp)
    cmds.parent(grp, null)


def deactivateMoveJointsALL(*args):
    sel = cmds.ls(type="skinCluster")
    for sc in sel:
        cmds.skinCluster(sc, e=True, moveJointsMode=0)

def activateMoveJointsALL(*args):
    sel = cmds.ls(type="skinCluster")
    for sc in sel:
        cmds.skinCluster(sc, e=True, moveJointsMode=1)


def makePivotKeyable(*args):

    sel = cmds.ls(sl=True)

    for n in sel:
        attribs = ['rotatePivotTranslateX', 'rotatePivotTranslateY', 'rotatePivotTranslateZ', 'rotatePivotX', 'rotatePivotY', 'rotatePivotZ']
        for attr in attribs:
            cmds.setAttr(n + '.' + attr, k=True)

        #?Is Selection a controller?
        con = cmds.listConnections(n, type="constraint", d=True, s=False)
        if con is None:
            continue
        con = con[0]
        target = cmds.listConnections( con + '.constraintParentInverseMatrix' )[0]


        minus = cmds.createNode('plusMinusAverage')
        cmds.setAttr(minus + '.operation', 2)
        cmds.connectAttr( target + '.rotatePivot', minus + '.input3D[0]', f=True)
        cmds.disconnectAttr( target + '.rotatePivot', minus + '.input3D[0]')
        cmds.connectAttr( n + '.rotatePivot', minus + '.input3D[1]', f=True)
        cmds.disconnectAttr( n + '.rotatePivot', minus + '.input3D[1]')

        plus = cmds.createNode('plusMinusAverage')
        cmds.connectAttr( minus + '.output3D', plus + '.input3D[0]', f=True)
        cmds.connectAttr( n + '.rotatePivot', plus + '.input3D[1]', f=True)

        cmds.connectAttr( plus + '.output3D', target + '.rotatePivot', f=True)
        cmds.connectAttr(n + '.rotatePivotTranslate', target + '.rotatePivotTranslate', f=True)


def makePivotKeyableOLD(*args):
    sel = cmds.ls(sl=True, l=True)

    for n in sel:

        # Maintain Offset with plus Node
        plus = cmds.createNode('plusMinusAverage')
        cmds.connectAttr( n + '.rotatePivot', plus + '.input3D[0]', f=True )
        cmds.disconnectAttr( n + '.rotatePivot', plus + '.input3D[0]')


        # Move To Actual Pivot
        pos = cmds.xform(n, q=True, ws=True, piv=True)
        cmds.xform(loc, ws=True, t=(pos[0], pos[1], pos[2]))
        # Parent to Object
        loc = cmds.parent(loc, n)[0]
        # Reset Transforms
        cmds.makeIdentity(loc, apply=True, t=True, r=True, s=True)
        # Connect Attributes
        cmds.connectAttr(loc + '.translate', plus+'.input3D[1]', f=True)
        cmds.connectAttr( plus + '.output3D', n + '.rotatePivot', f=True)


        '''
        attribs = ['rotatePivotTranslateX', 'rotatePivotTranslateY', 'rotatePivotTranslateZ', 'rotatePivotX', 'rotatePivotY', 'rotatePivotZ']
        for attr in attribs:
            cmds.setAttr(n + '.' + attr, k=True)
        '''
        # Is Selection a Controller ?
        con = cmds.listConnections(n, type="constraint", d=True, s=False)
        if con is None:
            continue
        con = con[0]
        target = cmds.listConnections( con + '.constraintParentInverseMatrix' )[0]
        pplus = cmds.createNode('plusMinusAverage')
        cmds.connectAttr( target + '.rotatePivot', pplus + '.input3D[0]', f=True)
        cmds.disconnectAttr( target + '.rotatePivot', pplus + '.input3D[0]')
        cmds.connectAttr(loc + '.translate', pplus + '.input3D[1]', f=True)
        cmds.connectAttr(pplus + '.output3D', target  + '.rotatePivot', f=True)


def activateSkinCluster(*args):
    sel = cmds.ls(sl=True, l=True)
    for n in sel:
        if cmds.nodeType(n) == "transform":
            n = cmds.listRelatives(n, s=True)[0]

        skinClusters = cmds.listConnections(n, type="skinCluster")
        for sc in skinClusters:
            cmds.skinCluster(sc, e=True, moveJointsMode=1)

def deactivateSkinCluster(*args):
    sel = cmds.ls(sl=True, l=True)
    for n in sel:
        if cmds.nodeType(n) == "transform":
            n = cmds.listRelatives(n, s=True)[0]

        skinClusters = cmds.listConnections(n, type="skinCluster")
        for sc in skinClusters:
            cmds.skinCluster(sc, e=True, moveJointsMode=0)

def addVizAttrib(*args):
    sel = cmds.ls(sl=True, l=True)
    if len(sel) < 2:
        cmds.error("Invalid selection")

    if not cmds.attributeQuery("vis", node=sel[0], exists=True):
        cmds.addAttr(sel[0], ln="vis", at="bool", k=True )
    cmds.setAttr(sel[0] + ".vis", True)

    cmds.connectAttr(sel[0] + ".vis", sel[1] + ".v", f=True)

def setColor(*args):
    c = args[0]
    sel = cmds.ls(sl=True, l=True)
    for n in sel:
        color(n, c)

def color(obj, c):
    idx = {"red": 13, "blue": 6, "purple": 9, "green": 14, "yellow": 17, "lightBlue": 18, "lightGreen": 19, "pink": 20, "white":16}
    cmds.setAttr(obj + ".overrideEnabled", 1)
    cmds.setAttr(obj + ".overrideColor", idx[c])

def createCtrl(name, radius=1.0):
    name += '_'
    ctrl = cmds.circle(nr=(0,1,0), ch=True, name=name+'ctrl')
    cmds.setAttr(ctrl[1] + ".radius", radius)

    null = cmds.group(em=True, name=name+'null')
    grp = cmds.group(em=True, name=name+'grp')
    ctrl = cmds.parent(ctrl, grp)[0]
    grp = cmds.parent(grp, null)[0]

    return [null, grp, ctrl]

def RigTemplate(*args):
    result = cmds.promptDialog(title='Rig Name', message='Enter Name:', button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel')
    if result == 'OK':
        name = cmds.promptDialog(q=True, text=True).capitalize()
    else:
        return False

    # Groups
    grp = cmds.group(em=True)
    meshGrp = cmds.group(em=True, parent=grp, name=name+'_Mesh_Top_grp')
    rigGrp = cmds.group(em=True, parent=grp, name=name+'_Rig_Top_grp')
    ctrlGrp = cmds.group(em=True, parent=rigGrp, name=name+'_Control_Top_grp')

    # Controllers
    mctrl = createCtrl( name + '_Main', 3 )
    color(mctrl[2], 'yellow')
    wctrl = createCtrl(name+'_World', 5)
    color(wctrl[2], 'red')

    # Visibility Attribute
    cmds.addAttr(wctrl[2], ln='viz', at='bool', k=True, dv=True)
    cmds.connectAttr( wctrl[2] + '.viz', meshGrp + '.v', f=True )

    # Parent
    mctrl[0] = cmds.parent(mctrl[0], wctrl[2])[0]
    wctrl[0] = cmds.parent(wctrl[0], ctrlGrp)[0]

    cmds.parentConstraint(mctrl[2], meshGrp, mo=True, w=1.0)
    cmds.scaleConstraint(mctrl[2], meshGrp, mo=True, w=1.0)

    cmds.rename(grp, name)
