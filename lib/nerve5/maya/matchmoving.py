import nerve5 as nerve
import nerve5.maya
import maya.cmds as cmds
from functools import partial

def UI():
    data = []

    data.append( { 'label':'Move Along Camera Tool', 'command':moveAlongCameraTool } )
    data.append( { 'label':'Locator to Cone', 'command':locToCone } )
    data.append( { 'label':'Parent Camera To World', 'command':parentCameraToWorld } )
    return data

def parentCameraToWorld(*args):

    # GET SELECTED CAMERA
    sel = cmds.ls(sl=True)
    if len(sel) == 0:
        raise Exception("Nothing selected")

    if cmds.nodeType(sel[0]) == "transform":
        trans = sel[0]
        shape = cmds.listRelatives(trans, s=True)[0]
        if cmds.nodeType(shape) != "camera":
            raise Exception("Selection is not a camera")
    elif cmds.nodeType(sel[0]) == "camera":
        shape = sel[0]
        trans = cmds.listRelatives(shape, p=True)[0]
    else:
        raise Exception("Selection error")

    # DUPLICATE
    dup = cmds.duplicate(trans, rr=True)

    # WORLD SPACE
    cmds.parent(dup[0], w=True)
    dup = cmds.ls(sl=True, l=True)
    dup.append(cmds.listRelatives(dup[0], s=True)[0])

    # UNLOCK
    attribs = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]
    for attr in attribs:
        cmds.setAttr(dup[0] + "." + attr, e=True, lock=False)

    if cmds.getAttr(dup[1] + ".focalLength", lock=True):
        cmds.setAttr(dup[1] + ".focalLength", lock=False)

    # SET SCALE TO 1.0
    cmds.setAttr(dup[0]+".sx", 1.0)
    cmds.setAttr(dup[0]+".sy", 1.0)
    cmds.setAttr(dup[0]+".sz", 1.0)

    # GET RANGE
    startFrame = cmds.playbackOptions(q=True, min=True)
    endFrame = cmds.playbackOptions(q=True, max=True)

    # ATTRIBUTES TO QUERY
    attribs  = ["focalLength"]

    for i in range(int(startFrame), int(endFrame)+1):
        cmds.currentTime(i, update=True)

        # COPY SHAPE ATTRIBUTES
        for attr in attribs:
            val = cmds.getAttr(shape + "." + attr)
            cmds.setAttr(dup[1] + "." + attr, val)
            cmds.setKeyframe(dup[1], attribute=attr)

        # GET TRANSFORM & ROTATION
        pos = cmds.xform(trans, q=True, ws=True, t=True)
        rot = cmds.xform(trans, q=True, ws=True, ro=True)

        # SET TRANSFORM & ROTATION
        cmds.xform(dup[0], ws=True, t=(pos[0], pos[1], pos[2]))
        cmds.xform(dup[0], ws=True, ro=(rot[0], rot[1], rot[2]))

        # SET KEYFRAMES
        cmds.setKeyframe(dup[0], attribute="translate")
        cmds.setKeyframe(dup[0], attribute="rotate")



def moveAlongCameraTool(*args):
    dragger()

def locToCone(*args):

    def cone(loc):
        pos = cmds.xform(loc, q=True, ws=True, t=True)

        cone = cmds.polyCone(r=1, h=2, sx=20, sy=1, sz=0, ax=(0,-1,0), rcp=0, cuv=3, ch=0)[0]
        cmds.xform(cone, ws=True, t=(0,1,0))
        cmds.xform(cone, ws=True, rp=(0,0,0))
        cmds.xform(cone, ws=True, sp=(0,0,0))
        cmds.makeIdentity(cone, apply=True, t=True, r=True, s=True, n=False, pn=True)

        cmds.xform(cone, ws=True, t=(pos[0], pos[1], pos[2]))
        return cone

    sel = cmds.ls(sl=True, l=True)
    cmds.select(hi=True)
    locs = cmds.ls(sl=True, type="locator")
    locators = []
    for l in locs:
        locators.append( cmds.listRelatives(l, p=True, f=True)[0] )

    cones = []
    for loc in locators:
        cones.append( cone(loc) )

    # Shader
    name = 'MMSS'
    mmssSG = name + 'SG'
    if not cmds.objExists(name):
        mmss = cmds.shadingNode("surfaceShader", asShader=True, name=name)
        cmds.setAttr(mmss + '.outColor', 1,0,0)
        cmds.sets(name=mmssSG, renderable=True, noSurfaceShader=True, empty=True)
        cmds.connectAttr(mmss + '.outColor', mmssSG + '.surfaceShader')

    cmds.sets(cones, e=True, forceElement=mmssSG)

    grp = 'Cones_grp'
    if not cmds.objExists(grp):
        cmds.group(em=True, name=grp)

    cmds.parent(cones, grp)



class dragger():
    def __init__(self):
        # point
        self.point = nerve.vector()

        # name
        self.name = 'mvAlongCameraTool'

        # Camera
        self.camShape = nerve.maya.activeCamera(True)
        self.camTrans = cmds.listRelatives(self.camShape, p=True, f=True)[0]
        self.cpos = nerve.vector( cmds.xform(self.camTrans, q=True, ws=True, t=True) )

        '''
        self.cim = nerve.matrix( cmds.getAttr(self.camShape + '.worldInverseMatrix') )
        self.hfv = cmds.camera( self.camShape, q=True, hfv=True )
        self.vfv = cmds.camera( self.camShape, q=True, vfv=True )

        screen.setX( ((point.x/(point.z*-1))/tand(self.hfv/2.0))/2.0 + 0.5 )
        screen.setY( ((point.y/(point.z*-1))/tand(self.vfv/2.0))/2.0 + 0.5 )
        '''

        # Selection
        sel = cmds.ls(sl=True)
        if len(sel) == 0:
            raise Exception("Nothing selected")
        self.obj = sel[0]
        self.ppos = nerve.vector( cmds.xform(self.obj, q=True, ws=True, t=True) )

        # Dragger Context
        args = {}
        if cmds.draggerContext(self.name, exists=True):
            args['edit'] = True
        args["pressCommand"] = partial(self.press)
        args["dragCommand"] = partial(self.drag)
        args["undoMode"] = "sequence"
        args["cursor"] = 'crossHair'
        cmds.draggerContext(self.name, **args)
        cmds.setToolTo(self.name)

    def press(self):
        self.ppos = nerve.vector( cmds.xform(self.obj, q=True, ws=True, t=True) )

    def drag(self):
        anchor = nerve.vector(cmds.draggerContext( self.name, q=True, anchorPoint=True ) )
        point = nerve.vector( cmds.draggerContext( self.name, q=True, dragPoint=True )  )
        diff = point-anchor

        ppos = nerve.vector( cmds.xform(self.obj, q=True, ws=True, t=True)  )

        t = (self.cpos - self.ppos)
        r = self.ppos + t.unit()*diff.x*0.1

        cmds.xform( self.obj, ws=True, t=tuple(r) )
