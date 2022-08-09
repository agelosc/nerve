import maya.cmds as cmds
import maya.mel as mel
import maya.utils as mu

from functools import partial
import nerve5 as nerve
import os
import json

def UI():
    data = []
    data.append( {'label':'Camera', 'command':camera} )
    data.append( {'type':'seperator'} )
    data.append( {'label':'Studio Library', 'command':studioLibrary} )
    data.append( {'label':'Awe Control Picker', 'command':aweControlPicker} )
    data.append( {'label':'Tween Machine', 'command':tweenMachine} )
    data.append( {'label':'Path Anim Tool', 'command':pathAnim} )
    data.append( {'label':'Foot Locker Tool', 'command':footLocker} )
    data.append( {'type':'seperator'} )
    data.append( {'label':'Constraint', 'command':constraint} )
    data.append( {'label':'Noise Constraint', 'command':noiseConstraint} )
    data.append( {'label':'Oscillate Expression', 'command':oscillate} )
    data.append( {'label':'Set Random Value', 'command':setRandomValue} )
    data.append( {'type':'seperator'} )
    data.append( {'label':'Snap From->To', 'command':snap} )
    data.append( {'label':'Multi-Snap From->To', 'command':multisnap} )
    data.append( {'type':'seperator'} )
    data.append( {'label':'Select Scene Animation', 'command':selectAnimationCurves} )
    data.append( {'type':'seperator'} )
    data.append( {'label':'Anim Export', 'command':animExport} )
    data.append( {'label':'Anim Import', 'command':animImport} )

    return data

def footLocker(*args):
    mel.eval('source bh_footLocker.mel')
    mel.eval('bh_footLocker')

def pathAnim(*args):
    mel.eval('source bh_pathAnim');
    mel.eval('bh_pathAnim')

def setRandomValue(*args):

    def setRange(value, oldMin, oldMax, min, max):
        #OutValue = Min + (((Value-OldMin)/(OldMax-OldMin)) * (Max-Min))
        return (min + (((value-oldMin)/(oldMax-oldMin)) * (max-min)))

    sel = cmds.ls(sl=True, l=True)
    if not len(sel):
        cmds.confirm('No objects selected. Quiting...')
        return False

    attributes = mel.eval('selectedChannelBoxAttributes')
    if not len(attributes):
        nerve.maya.confirm( 'No channels selected. Quiting...' )
        return False

    result = cmds.promptDialog(title='Min Value', message='Min Value:', button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel')
    if result == 'OK':
        min = cmds.promptDialog(query=True, text=True)
    else:
        return False

    result = cmds.promptDialog(title='Max Value', message='Max Value:', button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel')
    if result == 'OK':
        max = cmds.promptDialog(query=True, text=True)
    else:
        return False

    for n in sel:
        for attr in attributes:
            if not cmds.attributeQuery(attr, n=n, exists=True):
                cmds.warning( n + '.' + attr + ': does not exist. Skipping...' )
                continue

            value = setRange( mel.eval('rand(1)'), 0, 1, float(min), float(max) )
            cmds.setAttr(n + '.' + attr, value)

def oscillate(*args):
    def selectedChannels():
        import maya.mel as mel
        channelBox = mel.eval('global string $gChannelBoxName; $temp=$gChannelBoxName;')
        attr = cmds.channelBox( channelBox, q=True, sma=True )
        if not attr:
            return []
        return attr

    asel = selectedChannels()
    if not len(asel):
        cmds.error('No attributes selected on channel box')

    sel = cmds.ls(sl=True, l=True)
    offset = 0
    for n in sel:
        # attributes
        attribs = ['oscFreq', 'oscAmp', 'oscOffset']
        # Osc Frequency
        if not cmds.attributeQuery('oscFrequency', exists=True, n=n):
            cmds.addAttr(n, ln='oscFrequency', at='double', dv=2, min=0, k=True)
        # Osc Offset
        if not cmds.attributeQuery('oscOffset', exists=True, n=n):
            cmds.addAttr(n, ln='oscOffset', at='double', dv=0, k=True)
            cmds.setAttr( n + '.oscOffset', offset)
        # Osc Global Amplitude
        if not cmds.attributeQuery('oscGlobalAmplitude', exists=True, n=n):
            cmds.addAttr(n, ln='oscGlobalAmplitude', at='double', dv=1, min=0, k=True)
        # Osc Translate Amplitude
        if not cmds.attributeQuery('oscTranslateAmp', exists=True, n=n):
            cmds.addAttr(n, ln='oscTranslateAmp', at='double', dv=1, min=0, k=True)
        # Osc Rotate Amplitude
        if not cmds.attributeQuery('oscRotateAmp', exists=True, n=n):
            cmds.addAttr(n, ln='oscRotateAmp', at='double', dv=.2, min=0, k=True)
        # Osc Scale Amplitude
        if not cmds.attributeQuery('oscScaleAmp', exists=True, n=n):
            cmds.addAttr(n, ln='oscScaleAmp', at='double', dv=1, min=0, k=True)

        offset-=0.1;


        expr = '// Oscilation Expression\n'
        for an in asel:
            if an == 'tx' or an == 'ty' or an == 'tz':
                expr+= '%s.%s = sin( time * %s.oscFrequency + %s.oscOffset ) * %s.oscGlobalAmplitude * %s.oscTranslateAmp;\n'%( n, an, n, n, n, n )
            elif an == 'rx' or an == 'ry' or an == 'rz':
                expr+= '%s.%s = sin( time * %s.oscFrequency + %s.oscOffset ) * %s.oscGlobalAmplitude * %s.oscRotateAmp;\n'%( n, an, n, n, n, n )
            elif an == 'sx' or an == 'sy' or an == 'sz':
                expr+= '%s.%s = (sin( time * %s.oscFrequency + %s.oscOffset )+1.1) * %s.oscGlobalAmplitude * %s.oscScaleAmp;\n'%( n, an, n, n, n, n )
            else:
                expr+= '%s.%s = sin( time * %s.oscFrequency + %s.oscOffset ) * %s.oscGlobalAmplitude ;\n'%( n, an, n, n, n, n )

        cmds.expression(s=expr )


def multisnap(*args):
    sel = cmds.ls(sl=True, l=True, exactType="transform")

    skip = []
    for n in sel:
        clean = n.split('|')[-1].split(":")[-1]
        if n in skip:
            continue

        # Skip
        for t in sel:

            if t == n:
                continue

            if t in skip:
                continue

            if clean == t.split('|')[-1].split(":")[-1]:

                print n
                print t
                print ''

                cmds.select( [n, t], r=True )
                snap([])
                skip.append( t )

    cmds.select(sel, r=True)


def snap(*args):
    sel = cmds.ls(sl=True, l=True)
    if len(sel) != 2:
        cmds.error("Selection Error.")

    s = sel[0]
    d = sel[1]

    if cmds.nodeType(s) != 'transform' or cmds.nodeType(d) != 'transform':
        cmds.error("Selection Error.")

    pos = nerve.vector( cmds.xform(d, q=True, ws=True, t=True) )
    rot = nerve.vector( cmds.xform(d, q=True, ws=True, ro=True) )
    sca = nerve.vector( cmds.xform(d, q=True, ws=True, s=True) )

    cmds.xform(s, ws=True, t=tuple(pos))
    cmds.xform(s, ws=True, ro=tuple(rot))
    cmds.xform(s, ws=True, s=tuple(sca))


def animExport(self, *args):
    ac = nerve.maya.animation.animCurves()
    objects = cmds.ls(sl=True, l=True)
    if objects is None:
        print "No Objects Selected",
        return False

    ac.release(objects)

def animImport(self, *args):
    result = cmds.promptDialog(title='Min Frame', message='Min Frame:', button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel')
    if result == 'OK':
        min = cmds.promptDialog(q=True, text=True)
        if min == '':
            min = None
        else:
            min = float(min)
    else:
        return False

    result = cmds.promptDialog(title='Max Frame', message='Max Frame:', button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel')
    if result == 'OK':
        max = cmds.promptDialog(q=True, text=True)
        if max == '':
            max = None
        else:
            max = float(max)
    else:
        return False

    ac = nerve.maya.animation.animCurves()
    ac.gather(min=min, max=max)


def camera(*args):
    cmds.file("R:/jobs/Mascista/build/build/elements/3D/CamRigMascista_2018.ma", r=True, namespace='RenderCam', type='mayaAscii', options='v=0', mergeNamespacesOnClash=False, returnNewNodes=True)

def studioLibrary(*args):
    import studiolibrary
    library = cmds.workspace(q=True, o=True) + '/studiolibrary'
    studiolibrary.main(name="Global", path=library)

def aweControlPicker(*args):
    mel.eval("source aweControlPicker.mel; aweControlPicker;")

def tweenMachine(*args):
    import tweenMachine
    tweenMachine.start()

def constraint(*args):
    # parent attr
    def addParentAttr(sel, name):
        if cmds.attributeQuery("parent", n=sel, exists=True):
            enumString = cmds.attributeQuery("parent", n=sel, listEnum=True)[0]
            enums = enumString.split(":")
            c = 1
            while name in enums:
                name = name.rstrip('1234567890') + str(c)
                c=c+1
            cmds.addAttr(sel+".parent", e=True, enumName=enumString+":"+name)
            return len(enums)
        else:
            cmds.addAttr(sel, ln="parent", at="enum", k=True, en="None:"+name)
            return 1

    def rebuildConstraint(src):
        cc = cmds.listConnections(src, type="parentConstraint")[0]
        #targetList = cmds.parentConstraint(cc, q=True, targetList=True)
        targetAttrList = cmds.listAttr(cc, ud=True)

        length = cmds.getAttr(cc + ".target", size=True)
        targetList = []
        for i in range(length):
            attr = '%s.target[%s].targetParentMatrix'%(cc, str(i))
            tmp = cmds.listConnections(attr, d=False, s=True)[0]
            targetList.append( tmp )

        # plugs
        plugs = []
        for i in range(len(targetList)):
            fromPlug = '%s.%s'%(cc, targetAttrList[i])
            toPlug = cmds.listConnections(fromPlug, p=True)[0]
            node = cmds.listConnections('%s.%s'%(cc, targetAttrList[i]))[0]

            translate = cmds.getAttr('%s.target[%s].%s'%(cc, str(i), "targetTranslate"))
            rot = cmds.getAttr('%s.target[%s].%s'%(cc, str(i), "targetRotate"))

            cmds.lockNode(node, l=True)
            plugs.append( [fromPlug, toPlug, node] )

        # offsets
        offsetAttributes = ["targetOffsetTranslateX", "targetOffsetTranslateY", "targetOffsetTranslateZ", "targetOffsetRotateX", "targetOffsetRotateY", "targetOffsetRotateZ"]
        offset = []
        for i in range(len(targetList)):
            tmp = {}
            for offsetAttr in offsetAttributes:
                value = cmds.getAttr('%s.target[%s].%s'%(cc, str(i), offsetAttr))
                tmp[offsetAttr] = value
            offset.append(tmp)


        cmds.delete(cc)
        # create
        for target in targetList:
            pc = cmds.parentConstraint(target, src, w=1.0, mo=True)[0]

        # plug
        for plug in plugs:
            cmds.connectAttr(plug[1], plug[0], f=True)
            cmds.lockNode(plug[2], l=False)

        # offsets
        for i in range(len(offset)):
            for key in offset[i].keys():
                value = offset[i][key]
                plug = '%s.target[%s].%s'%(pc, str(i), key)
                if isinstance(value, float):
                    cmds.setAttr(plug, value)

        return pc

    # add constraint
    def addConstraint(sel, src, tar, name):
        try:
            constraint = cmds.parentConstraint(tar, src, mo=True, w=1.0)[0]
        except RuntimeError:
            result = cmds.confirmDialog( title='Confirm', message='Constraint needs to be rebuild. Proceed?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
            if result == 'No':
                print "Save scene and try again",
                return False

            rebuildConstraint( src )
            constraint = cmds.parentConstraint(tar, src, mo=True, w=1.0)[0]

        value = addParentAttr(sel, name)

        condition = cmds.createNode("condition")
        cmds.connectAttr(sel + ".parent", condition + ".firstTerm", f=True)
        cmds.setAttr(condition + ".secondTerm", value)
        cmds.setAttr(condition + ".colorIfTrueR", 1.0)
        cmds.setAttr(condition + ".colorIfFalseR", 0.0)

        targetList = cmds.parentConstraint(constraint, q=True, targetList=True)
        targetWeightList = cmds.parentConstraint(constraint, q=True, weightAliasList=True)

        attr = None
        for i in range(len(targetList)):
            if targetList[i] == tar.split("|")[-1]:
                attr = targetWeightList[i]
                break

        cmds.connectAttr(condition + ".outColorR", constraint + "." + attr, f=True)
        return True

    def cleanName(str):
        com = str.split(":")[-1].split("|")[-1].split("_")
        return (com[0] + "".join( x.title() for x in com[1:] )).rstrip('1234567890')

    sel = cmds.ls(sl=True, l=True)

    if "Validate":
        if len(sel) == 0:
            cmds.confirmDialog( title='Constraint', message='Nothing selected', button=['OK'], defaultButton='OK' )
            cmds.select(sel, r=True)
            return False

        if len(sel) > 2:
            cmds.confirmDialog( title='Constraint', message='More than two objects selected', button=['OK'], defaultButton='OK' )
            cmds.select(sel, r=True)
            return False

    # WORLD
    if len(sel) == 1:
        src = cmds.listRelatives(sel[0], path=True, p=True)[0]
        if not len(src):
            cmds.confirmDialog( title='Constraint', message='Child node needs to have parents or be grouped', button=['OK'], defaultButton='OK' )
            return False

        bb = 1.0

        piv = cmds.xform(sel[0], q=True, ws=True, piv=True)
        rot = cmds.xform(sel[0], q=True, ws=True, ro=True)

        ctrl = cmds.circle(c=(0,0,0), nr=(0, 1, 0), sw=360, r=bb, d=3, ut=0, tol=0, s=8, ch=0, name=cleanName(sel[0]) + "_World")[0]
        cmds.setAttr(ctrl + ".overrideEnabled", 1)
        cmds.setAttr(ctrl + ".overrideColor", 18)

        cmds.xform(ctrl, ws=True, t=(piv[0], piv[1], piv[2]))
        cmds.xform(ctrl, ws=True, ro=(rot[0], rot[1], rot[2]))

        addConstraint(sel[0], src, ctrl, "World")

        cmds.select(sel, r=True)

        return ctrl

    # TOGETHER
    if len(sel) == 2:
        src = cmds.listRelatives(sel[1], path=True, p=True)[0]
        if not len(src):
            cmds.confirmDialog( title='Constraint', message='Child node needs to have parents or be grouped', button=['OK'], defaultButton='OK' )
            return False

        result = addConstraint(sel[1], src, sel[0], cleanName(sel[0]))
        if result:
            cmds.select(sel[1], r=True)

def noiseConstraint(*args):
    sel = cmds.ls(sl=True, l=True)
    for s in sel:
        cmds.select(s, r=True)
        n = nerve.maya.animation.constraint()
        grp = cmds.group(em=True)
        pos = cmds.xform(n, q=True, ws=True, t=True)
        rot = cmds.xform(n, q=True, ws=True, ro=True)
        cmds.xform(grp, ws=True, t=(pos[0], pos[1], pos[2]))
        cmds.xform(grp, ws=True, ro=(rot[0], rot[1], rot[2]))

        # ADD ATTRIBUTES
        cmds.addAttr(n, ln="target", at="enum", en="Rotation:Translation:Both", k=True)

        cmds.addAttr(n, ln="Low", at="enum", en="___", k=True)
        cmds.setAttr(n + ".Low", l=True)

        cmds.addAttr(n, ln="LowFrequency", at="double", k=True)
        cmds.setAttr(n + ".LowFrequency", 0.1)
        cmds.addAttr(n, ln="LowPhase", at="double", k=True)
        cmds.setAttr(n + ".LowPhase", 0.5)
        cmds.addAttr(n, ln="LowAmplitude", at="double", k=True)
        cmds.setAttr(n + ".LowAmplitude", 25.0)

        cmds.addAttr(n, ln="Mid", at="enum", en="___", k=True)
        cmds.setAttr(n + ".Mid", l=True)

        cmds.addAttr(n, ln="MidFrequency", at="double", k=True)
        cmds.setAttr(n + ".MidFrequency", 1.0)
        cmds.addAttr(n, ln="MidPhase", at="double", k=True)
        cmds.setAttr(n + ".MidPhase", 1.0)
        cmds.addAttr(n, ln="MidAmplitude", at="double", k=True)
        cmds.setAttr(n + ".MidAmplitude", 5)

        cmds.addAttr(n, ln="High", at="enum", en="___", k=True)
        cmds.setAttr(n + ".High", l=True)

        cmds.addAttr(n, ln="HighFrequency", at="double", k=True)
        cmds.setAttr(n + ".HighFrequency", 1.0)
        cmds.addAttr(n, ln="HighPhase", at="double", k=True)
        cmds.setAttr(n + ".HighPhase", 1.0)
        cmds.addAttr(n, ln="HighAmplitude", at="double", k=True)
        cmds.setAttr(n + ".HighAmplitude", 5)

        cmds.addAttr(n, ln="Global", at="enum", en="___", k=True)
        cmds.setAttr(n + ".Global", l=True)

        cmds.addAttr(n, ln="Amplitude", at="double", k=True)
        cmds.setAttr(n + ".Amplitude", 1.0)

        pos = cmds.xform(n, q=True, ws=True, piv=True)
        e = '//LOW'
        e+= 'seed(0);\n'
        e+= 'float $LowFreq = %s.LowFrequency;\n'%n
        e+= 'float $LowPhase = %s.LowPhase;\n'%n
        e+= 'float $LowAmp = %s.LowAmplitude;\n'%n

        e+= 'vector $pos = <<'+str(pos[0])+', '+str(pos[1])+', '+str(pos[2])+'>>;\n'
        e+= 'vector $seed = unit($pos)*$LowFreq + <<time*$LowPhase+rand(10), time*$LowPhase+rand(20), time*$LowPhase+rand(30)>>;\n'
        e+= 'vector $shakeLow = dnoise($seed) * $LowAmp;\n'

        e+= '// MID\n'
        e+= 'seed(1);\n'
        e+= 'float $MidFreq = %s.MidFrequency;\n'%n
        e+= 'float $MidPhase = %s.MidPhase;\n'%n
        e+= 'float $MidAmp = %s.MidAmplitude;\n'%n

        e+= 'vector $pos = <<'+str(pos[0])+', '+str(pos[1])+', '+str(pos[2])+'>>;\n'
        e+= 'vector $seed = unit($pos)*$MidFreq + <<time*$MidPhase+rand(10), time*$MidPhase+rand(20), time*$MidPhase+rand(30)>>;\n'
        e+= 'vector $shakeMid = dnoise($seed) * $MidAmp;\n'

        e+= '// HIGH\n'
        e+= 'seed(2);\n'
        e+= 'float $HighFreq = %s.HighFrequency;\n'%n
        e+= 'float $HighPhase = %s.HighPhase;\n'%n
        e+= 'float $HighAmp = %s.HighAmplitude;\n'%n

        e+= 'vector $pos = <<'+str(pos[0])+', '+str(pos[1])+', '+str(pos[2])+'>>;\n'
        e+= 'vector $seed = unit($pos)*$HighFreq + <<time*$HighPhase+rand(10), time*$HighPhase+rand(20), time*$HighPhase+rand(30)>>;\n'
        e+= 'vector $shakeHigh = dnoise($seed) * $HighAmp;\n'

        e+= '// TARGET\n'
        e+= 'int $target = %s.target;\n'%n
        e+= 'float $translate = 0.0;\n'
        e+= 'float $rotate = 0.0;\n'
        e+= 'if($target == 0)\n'
        e+= '{\n'
        e+= '\t$translate = 0.0;\n'
        e+= '\t$rotate = 1.0;\n'
        e+= '}\n'

        e+= 'if($target == 1)\n'
        e+= '{\n'
        e+= '\t$translate = 1.0;\n'
        e+= '\t$rotate = 0.0;\n'
        e+= '}\n'
        e+= 'if($target == 2)\n'
        e+= '{\n'
        e+= '    $translate = 1.0;\n'
        e+= '    $rotate = 1.0;\n'
        e+= '}\n'


        e+= 'vector $t = ($shakeLow + $shakeMid + $shakeHigh) * $translate * %s.Amplitude;\n'%n

        e+= '// TRANSLATE\n'
        e+= '%s.translateX = $t.x;\n'%n
        e+= '%s.translateY = $t.y;\n'%n
        e+= '%s.translateZ = $t.z;\n'%n

        e+= 'vector $r = ($shakeLow + $shakeMid + $shakeHigh) * $rotate * %s.Amplitude;\n'%n

        e+= '// ROTATE\n'
        e+= '%s.rotateX = $r.x;\n'%n
        e+= '%s.rotateY = $r.y;\n'%n
        e+= '%s.rotateZ = $r.z;\n'%n

        cmds.expression(s=e)
        cmds.parent(n, grp)
    cmds.select(sel, r=True)

def selectAnimationCurves(*args):
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

class animCurves():
    def __init__(self):
        pass

    def convertAttrType(self, type):
        if type == "doubleLinear":
            return float
        if type == "bool":
            return int

        return float

    def getInfinityValue(self, enum):
        if enum == 0:
            return "constant"
        if enum == 1:
            return "linear"
        if enum == 2:
            return "constant"
        if enum == 3:
            return "cycle"
        if enum == 4:
            return "cycleRelative"
        if enum == 5:
            return "oscillate"

        return False


    def release(self, objects):
        data = {}
        data["nodes"] = []
        for obj in objects:
            channels = cmds.listAnimatable(obj)
            # Pair Blend
            if cmds.nodeType(obj) == 'pairBlend':
                pairAttribs = ['inTranslateX1', 'inTranslateY1', 'inTranslateZ1', 'inRotateX1', 'inRotateY1', 'inRotateZ1']
                for pairAttr in pairAttribs:
                    channels.append(obj + '.' + pairAttr)

            if channels is None:
                channels = []

            data["nodes"].append( {} )

            name = cmds.ls(obj, sl=True)
            data['nodes'][-1]['name'] = name
            data["nodes"][-1]["longname"] = obj
            data['nodes'][-1]['attributes'] = []

            for channel in channels:
                data['nodes'][-1]['attributes'].append( {} )

                buffer = channel.split('.')
                attributeName = '.'.join(buffer[1:])
                data['nodes'][-1]['attributes'][-1]['name'] = str(attributeName)

                isAnimated = cmds.listConnections(channel, type="animCurve", d=False, s=True)
                # ANIMATED
                if isAnimated is not None:
                    data["nodes"][-1]['attributes'][-1]['state'] = str('animated')
                    data["nodes"][-1]['attributes'][-1]['keys'] = []

                    connects = cmds.listConnections(channel, p=True)
                    curAttr = connects[-1]
                    buffer = curAttr.split(".")

                    animNode = buffer[0]
                    animAttr = buffer[1]

                    # preInfinity
                    preInfinity = self.getInfinityValue(cmds.getAttr(animNode + ".preInfinity"))
                    data["nodes"][-1]["attributes"][-1]["preInfinity"] = str(preInfinity)

                    # postInfinity
                    postInfinity = self.getInfinityValue(cmds.getAttr(animNode + ".postInfinity"))
                    data["nodes"][-1]["attributes"][-1]["postInfinity"] = str(postInfinity)

                    # weighted
                    weighted = cmds.getAttr(animNode + ".weightedTangents")
                    data["nodes"][-1]["attributes"][-1]["weighted"] = str(weighted)

                    keys = cmds.keyframe(animNode, query=True)
                    values = cmds.keyframe(animNode, query=True, vc=True)
                    inTan = cmds.keyTangent(animNode, query=True, itt=True)
                    outTan = cmds.keyTangent(animNode, query=True, ott=True)
                    tanLock = cmds.keyTangent(animNode, query=True, lock=True)
                    weightLock = cmds.keyTangent(animNode, query=True, weightLock=True)
                    breakDown = cmds.keyframe(animNode, query=True, breakdown=True)
                    inAngle = cmds.keyTangent(animNode, query=True, inAngle=True)
                    outAngle = cmds.keyTangent(animNode, query=True, outAngle=True)
                    inWeight = cmds.keyTangent(animNode, query=True, inWeight=True)
                    outWeight = cmds.keyTangent(animNode, query=True, outWeight=True)

                    if keys is None:
                        keys = []
                    for i in range(0, len(keys)):
                        data["nodes"][-1]["attributes"][-1]["keys"].append({})

                        bd = 0
                        if breakDown is None:
                            breakDown = []
                        for bd_item in breakDown:
                            if bd_item == keys[i]:
                                bd = 1

                        data["nodes"][-1]["attributes"][-1]["keys"][-1]["time"] = str(keys[i])
                        data["nodes"][-1]["attributes"][-1]["keys"][-1]["value"] = str(values[i])
                        data["nodes"][-1]["attributes"][-1]["keys"][-1]["inTangent"] = str(inTan[i])
                        data["nodes"][-1]["attributes"][-1]["keys"][-1]["outTangent"] = str(outTan[i])
                        data["nodes"][-1]["attributes"][-1]["keys"][-1]["tangentLock"] = str(tanLock[i])
                        data["nodes"][-1]["attributes"][-1]["keys"][-1]["weightLock"] = str(weightLock[i])
                        data["nodes"][-1]["attributes"][-1]["keys"][-1]["breakDown"] = str(bd)
                        if inTan[i] == "fixed":
                            data["nodes"][-1]["attributes"][-1]["keys"][-1]["inAngle"] = str(inAngle[i])
                            data["nodes"][-1]["attributes"][-1]["keys"][-1]["inWeight"] = str(inWeight[i])
                        if outTan[i] == "fixed":
                            data["nodes"][-1]["attributes"][-1]["keys"][-1]["outAngle"] = str(outAngle[i])
                            data["nodes"][-1]["attributes"][-1]["keys"][-1]["outWeight"] = str(outWeight[i])
                # STATIC
                else:
                    data["nodes"][-1]["attributes"][-1]["state"] = str("static")
                    data["nodes"][-1]["attributes"][-1]["value"] = str(cmds.getAttr(channel))


        # WRITE DATA FILE
        datafile = os.environ['TEMP'] + '/animCurves.json';
        with open(datafile, 'w') as df:
            json.dump(data, df)


    def gather(self, min=None, max=None):
        datafile = os.environ["TEMP"] + '/animCurves.json'
        with open(datafile) as f:
            data = json.load(f)

        for node in data["nodes"]:
            obj = node['longname']
            if not cmds.objExists(obj):
                print '[Obj does not exist] %s'%obj
                continue

            for attr in node['attributes']:
                plug = obj + '.' + attr['name']
                if cmds.attributeQuery(attr['name'], node=obj, exists=True) is False:
                    print '[Attribuite does not exist]%s'%plug
                    continue
                if not cmds.getAttr(plug, settable=True):
                    print '[is not settable]%s'%plug
                    continue

                # ANIMATION
                if attr['state'] == 'animated':
                    for key in attr["keys"]:
                        if min is not None:
                            if float(key['time']) < float(min):
                                continue

                        if max is not None:
                            if float(key['time']) > float(max):
                                continue

                        cmds.setKeyframe(plug, time=key["time"], value=float(key["value"]), breakdown=int(key["breakDown"]))
                        cmds.keyTangent(plug, lock=bool(key["tangentLock"]), time=(float(key["time"]), float(key["time"])))
                        # weighted
                        if attr["weighted"] == "True":
                            if key["weightLock"] is True:
                                key["weightLock"] = 1
                            else:
                                key["weightLock"] = 0
                            cmds.keyTangent(plug, edit=True, weightedTangents=True)
                            cmds.keyTangent(plug, time=(float(key["time"]), float(key["time"])), weightLock=key["weightLock"])
                        # non fixed tangents
                        if key["inTangent"] != "fixed" and key["outTangent"] != "fixed":
                            cmds.keyTangent(plug, edit=True, a=True, time=(float(key["time"]), float(key["time"])), itt=key["inTangent"], ott=key["outTangent"])
                        # in fixed
                        if key["inTangent"] == "fixed" and key["outTangent"] != "fixed":
                            cmds.keyTangent(plug, edit=True, a=True, time=(float(key["time"]), float(key["time"])), inAngle=key["inAngle"], inWeight=float(key["inWeight"]), itt=key["inTangent"], ott=key["outTangent"])
                        # out fixed
                        if key["inTangent"] != "fixed" and key["outTangent"] == "fixed":
                            cmds.keyTangent(plug, edit=True, a=True, time=(float(key["time"]), float(key["time"])), outAngle=key["outAngle"], outWeight=float(key["outWeight"]), itt=key["inTangent"], ott=key["outTangent"])
                        if key["inTangent"] == "fixed" and key["outTangent"] == "fixed":
                            cmds.keyTangent(plug, edit=True, a=True, time=(float(key["time"]), float(key["time"])), inAngle=key["inAngle"], inWeight=float(key["inWeight"]), outAngle=key["outAngle"], outWeight=float(key["outWeight"]),  itt=key["inTangent"], ott=key["outTangent"])
                    cmds.setInfinity(plug, poi=attr["postInfinity"], pri=attr["preInfinity"])

                # STATIC
                if attr["state"] == "static":
                    connected = cmds.listConnections(plug, d=False)
                    #print plug
                    if cmds.getAttr(plug, l=True) is False and connected is None:
                        attrType = self.convertAttrType(cmds.getAttr(plug, type=True))
                        value = attr["value"]
                        if value == "True":
                            value = 1
                        elif value == "False":
                            value = 0
                        cmds.setAttr(plug, attrType(value))
                    else:
                        print '[cannot be set to its static value]%s'%plug
