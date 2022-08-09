import maya.cmds as cmds
import maya.mel as mel
import nerve.maya

import ftplib
import collections
import datetime

import os
import re
import pprint
import math
import glob
from functools import partial

import nerve.maya.UI

try:
    import mtoa.aovs
except Exception:
    pass
    
class menu():
    def __init__(self):
        self.ctrl = {}
        self.name = "Lego"
        
        if(cmds.menu(self.name, exists=True)):
            cmds.deleteUI(self.name)
            
        gMainWindow = mel.eval('$temp1=$gMainWindow;')
        
        self.ctrl["legoMenu"] = cmds.menu(self.name, parent=gMainWindow, tearOff=True, label=self.name)
        
        # SirlToolALot
        self.ctrl["sirltoolalot"] = cmds.menuItem(subMenu=True, label="SirlToolALot", tearOff=True )
        self.seperator(self.ctrl["legoMenu"])
        cmds.menuItem(self.ctrl["sirltoolalot"], edit=True, parent=self.ctrl["legoMenu"], postMenuCommand=partial(self.loadSirlToolALot, self.ctrl["sirltoolalot"]),  postMenuCommandOnce=True)
        
        # LEGO
        self.seperator(self.ctrl["legoMenu"])
        cmds.menuItem(subMenu=False, label="Check Rig Updates...", parent=self.ctrl["legoMenu"], command=self.checkRigUpdates)
        self.seperator(self.ctrl["legoMenu"])
        cmds.menuItem(subMenu=False, label="Convert Sequences to XML", parent=self.ctrl["legoMenu"], command=self.convertSeqToSirl)
        
        #self.ctrl["legoMenu"] = cmds.menuItem(subMenu=True, tearOff=True, label="LEGO", parent=self.ctrl["mainMenu"])
        cmds.menuItem(subMenu=False,  label="Import Alembic...", parent=self.ctrl["legoMenu"], command=abcImportAll )
        self.seperator(self.ctrl["legoMenu"])
        cmds.menuItem(subMenu=False,  label="Export Alembic...", parent=self.ctrl["legoMenu"], command=abcExport )
        cmds.menuItem(subMenu=False,  label="Export Alembic (All)", parent=self.ctrl["legoMenu"], command=abcExportAll )
        self.seperator(self.ctrl["legoMenu"])
        
        cmds.menuItem(subMenu=False,  label="Switch to High Rez", parent=self.ctrl["legoMenu"], command=partial(switchHiLow, "hi") )
        cmds.menuItem(subMenu=False,  label="Switch to Low Rez", parent=self.ctrl["legoMenu"], command=partial(switchHiLow, "low") )        
        self.seperator(self.ctrl["legoMenu"])
        
        self.ctrl["legoCleanUp"] = cmds.menuItem(subMenu=True, tearOff=True, label="Cleanup", parent=self.ctrl["legoMenu"])
        # CleanUp
        cmds.menuItem(subMenu=False,  label="Delete Curves", parent=self.ctrl["legoCleanUp"], command=cleanUp.deleteCurves )
        cmds.menuItem(subMenu=False,  label="Delete Hidden Objects", parent=self.ctrl["legoCleanUp"], command=cleanUp.deleteHiddenObjects )
        cmds.menuItem(subMenu=False,  label="Delete Empty Groups", parent=self.ctrl["legoCleanUp"], command=cleanUp.deleteEmptyGroups )
        cmds.menuItem(subMenu=False,  label="Delete Extra UV Sets", parent=self.ctrl["legoCleanUp"], command=cleanUp.deleteExtraUvSets )
        cmds.menuItem(subMenu=False,  label="Combine Parented Objects", parent=self.ctrl["legoCleanUp"], command=cleanUp.combineParentedObjects )
        cmds.menuItem(subMenu=False,  label="Merge Vertices", parent=self.ctrl["legoCleanUp"], command=cleanUp.mergeVertices )
        cmds.menuItem(subMenu=False,  label="Fix Face Assignments", parent=self.ctrl["legoCleanUp"], command=cleanUp.fixFaceAssignments )
        cmds.menuItem(subMenu=False,  label="Fix Face Assignments(Copy)", parent=self.ctrl["legoCleanUp"], command=partial(cleanUp.fixFaceAssignments, True) )
        cmds.menuItem(subMenu=False,  label="Make Name Unique", parent=self.ctrl["legoCleanUp"], command=cleanUp.makeUnique )
        cmds.menuItem(subMenu=False,  label="Set Alembic Data", parent=self.ctrl["legoCleanUp"], command=setAlembicData )
        
        # Rigging
        self.ctrl["legoRigging"] = cmds.menuItem(subMenu=True, tearOff=True, label="Rigging", parent=self.ctrl["legoMenu"])
        cmds.menuItem(subMenu=False,  label="LOD Connect", parent=self.ctrl["legoRigging"], command=LODConnect )
        
        # Shading
        self.ctrl["legoCleanUp"] = cmds.menuItem(subMenu=True, tearOff=True, label="Shading", parent=self.ctrl["legoMenu"])
        cmds.menuItem(subMenu=False,  label="Select Scene Shaders", parent=self.ctrl["legoCleanUp"], command=selectSceneShaders )
        cmds.menuItem(subMenu=False,  label="Attach Alembic Data", parent=self.ctrl["legoCleanUp"], command=abcAttachData )
        cmds.menuItem(subMenu=False,  label="Create Shaders", parent=self.ctrl["legoCleanUp"], command=createShaders )
        cmds.menuItem(subMenu=False,  label="Create AOVs", parent=self.ctrl["legoCleanUp"], command=createAOVs )
        cmds.menuItem(subMenu=False,  label="Set AOVs Override", parent=self.ctrl["legoCleanUp"], command=setAovOverride )
        cmds.menuItem(subMenu=False,  label="Fix Texture Paths", parent=self.ctrl["legoCleanUp"], command=fixTexturePaths )
        cmds.menuItem(subMenu=False,  label="Add Face Texture Attribute", parent=self.ctrl["legoCleanUp"], command=addFaceTextureAttribute )
        cmds.menuItem(subMenu=False,  label="Export Shader Library...", parent=self.ctrl["legoCleanUp"], command=exportShaders )
        cmds.menuItem(subMenu=False,  label="Import Shader Library...", parent=self.ctrl["legoCleanUp"], command=importShaders )
        cmds.menuItem(subMenu=False,  label="Propagate Alpha Settings", parent=self.ctrl["legoCleanUp"], command=propagateAlphaSettings )
        cmds.menuItem(subMenu=False,  label="Delete AOVs", parent=self.ctrl["legoCleanUp"], command=clearAOVs )
        
        self.seperator(self.ctrl["legoMenu"])
        cmds.menuItem(subMenu=False, label="Reload Lego Menu", parent=self.ctrl["legoMenu"], command=reloadLegoMenu)
        
    def checkRigUpdates(self, *args):
        sirlasset.update()
        '''
        s = sirlasset()
        s.connect()
        s.update()
        s.quit()
        '''
    def seperator(self, parent):
        cmds.menuItem(divider=True, parent=parent)        
        
    def loadSirlToolALot(self, *args):
        #cmds.menuItem(label="TEST", parent=args[0])
    
        #cmds.setParent(args[0])
        import sys
        import os
        os.environ["MAYA_SCRIPT_PATH"]+= ';R:/software/tools/sirl/SirlToolALot'
        sys.path.append('R:/software/tools/sirl/SirlToolALot/')
        mel.eval('rehash; source SirlToolALot_menu.mel; SirlToolALot_menu("'+args[0]+'");')
        
    def convertSeqToSirl(*args):
        configPath = cmds.workspace(q=True, rootDirectory=True).replace("maya/", "config/")
        if not os.path.exists(configPath):
            print "No XML files found"
            return False
            
        xmlFiles = glob.glob(configPath + "/seq_*.xml")
        for xmlFile in xmlFiles:
            xml = '<MOVIE>\n'
            seqName = xmlFile.split("\\")[-1].replace("seq_", "").replace(".xml", "")
            xml+= '\t<SEQUENCE Title="%s">\n'%seqName
            
            shotDict = {}
            seq = nerve.shot(xmlFile)
            for s in seq.ordered():
                if type(s) != type(''):
                    shotDict[int(s["order"])] = {"sf":s["startFrame"], "ef":s["endFrame"]}
            sortedShots = collections.OrderedDict(sorted(shotDict.items()))            
            
            for s in sortedShots.iteritems():
                xml+= '\t\t<SHOT Name="%s" sf="%s" ef="%s"/>\n'%('S'+str(s[0]), s[1]["sf"], s[1]["ef"])
            xml+= '\t</SEQUENCE>\n';
            xml+= '</MOVIE>\n'
        
            filename = 'sirl_' + seqName + '.xml'
            animpath = cmds.workspace(q=True, rootDirectory=True) + "/scenes/animation"
            f = open(animpath + '/' + filename, 'w')            
            f.write(xml)
            f.close()        

def reloadLegoMenu(*args):
    import nerve.maya.lego
    reload(nerve.maya.lego)
    m = nerve.maya.lego.menu()

def convertVRayToArnold2(*args):

    # TRANSFER ATTR
    def transferAttr(srcPlug, destPlug):
        con = cmds.listConnections(srcPlug, p=True)
        if con is None:
            type = cmds.getAttr(srcPlug, type=True)
            value = cmds.getAttr(srcPlug)
            if type == 'float':
                cmds.setAttr(destPlug, value)    
            elif type == "float3":
                cmds.setAttr(destPlug, value[0][0], value[0][1], value[0][2])
        else:
            cmds.connectAttr(con[0], destPlug, f=True)
            
    # VRayMtl2AiStandard
    def vray2ai(mat, ai):
        pairs = {"color":"color", 'reflectionColor':'KsColor','illumColor':'emissionColor', 'hilightGlossiness':'specularRoughness' }
        for src,dest in pairs.iteritems():
            transferAttr(mat + "." + src, ai + "." + dest)
            
            # glossiness invert
            cmds.setAttr(ai + ".specularRoughness", 1-(cmds.getAttr(ai + ".specularRoughness")))
            
            # emission set
            con = cmds.listConnections(ai + ".emissionColor")
            if con is not None:
                cmds.setAttr(ai + ".emission", 1.0)
            else:
                value = cmds.getAttr(ai + ".emissionColor")
                if value[0][0] != 0 or value[0][1] != 0 or value[0][1] != 0:
                    cmds.setAttr(ai + ".emission", 1.0)
                    
        # bump
        con = cmds.listConnections(mat + '.bumpMap')
        if con is not None:
            bump = cmds.createNode("bump2d")
            cmds.connectAttr(con[0] + ".outAlpha", bump + ".bumpValue")
            cmds.connectAttr(bump + ".outNormal", ai + ".normalCamera")
            
            value = cmds.getAttr(mat + ".bumpMult")
            cmds.setAttr(bump + ".bumpDepth", value)

    
    r = []
    materials = cmds.ls(type="VRayMtl")
    for mat in materials:
        ai = cmds.createNode("aiStandard", name="M_"+mat)
        vray2ai(mat, ai)
        tmp = cmds.listConnections(mat, d=True, s=False, type="shadingEngine")
        if tmp is None:
            r.append(mat)
        else:
            cmds.connectAttr(ai + ".outColor", tmp[0] + ".surfaceShader", f=True)
        
        
    '''        
    sel = cmds.ls(sl=True, l=True)
    other = []
    valid = []
    for n in sel:
        obj = nerve.maya.MayaObject(n)
        shadingEngines = cmds.listConnections(obj["shape"], type="shadingEngine")
        shadingEngines = list(set(shadingEngines))
        shadingEngine = shadingEngines[0]
        mat = cmds.listConnections(shadingEngine + '.surfaceShader')[0]
        
        ai = cmds.createNode("aiStandard", name="M_"+mat)
        # VRayMtl
        if cmds.nodeType(mat) == "VRayMtl":
                    
            
            # ASSIGN
            cmds.connectAttr(ai + ".outColor", shadingEngine + ".surfaceShader", f=True)
        else:
            other.append(n)
    '''
    
def convertVRayToArnold(*args):
    sel = cmds.ls(sl=True, l=True)
    
    for n in sel:
        obj = nerve.maya.MayaObject(n)
        shadingEngines = cmds.listConnections(obj["shape"], type="shadingEngine")
        shadingEngines = list(set(shadingEngines))
        shadingEngine = shadingEngines[0]
        material = cmds.listConnections(shadingEngine + '.surfaceShader')[0]
        
        # VRAY
        data = {}
        if cmds.nodeType(material) == "VRayMtl":
            attribs = {'color':'color', 'bumpMap':'normalCamera', 'reflectionColor':'KsColor', 'illumColor':'emissionColor', 'hilightGlossiness':'specularRoughness'}
            for attr in attribs.keys():
                tmp = cmds.listConnections(material + '.' + attr, p=True)
                # Get Value
                if tmp is None:
                    data[attr] = cmds.getAttr(material + '.' + attr)
                # Get Connection
                else:
                    data[attr] = str(tmp[0])
            
            # aiStandard
            ais = cmds.createNode("aiStandard", name="M_" + material)
            # Defauls
            cmds.setAttr(ais + '.Ks', 0.2)
            cmds.setAttr(ais + '.Ksn', 0.05)
            cmds.setAttr(ais + '.emissionColor', 0,0,0, type='double3')
            cmds.setAttr(ais + '.emission', 0)
            
            for attr in attribs.keys():
                # Connection
                if type(data[attr]) == type(''):
                    if attr == 'bumpMap':
                        bump = cmds.createNode("bump2d")
                        #cmds.setAttr(bump + '.')
                        cmds.connectAttr(data[attr].replace('.outColor', '.outAlpha'), bump + '.bumpValue')
                        data[attr] = bump + '.outNormal'
                        
                    cmds.connectAttr(data[attr], ais + '.' + attribs[attr], f=True)
                else:
                    if attr == 'hilightGlossiness':
                        data[attr] = 1 - data[attr]
                    
                    # list
                    if type(data[attr]) == type([]):
                        cmds.setAttr(ais + '.' + attribs[attr], data[attr][0][0], data[attr][0][1], data[attr][0][2], type='double3')
                    else:
                        cmds.setAttr(ais + '.' + attribs[attr], data[attr])
                    
            cmds.connectAttr(ais + '.outColor', shadingEngine + '.surfaceShader', f=True)
            cmds.delete(material)
                    

class BrickShader():
    def __init__(self, node=None, input=None):
        nerve.maya.MayaNode.__init__(self, node, input)
        

class Brick():
    def __init__(self, dag=None, input=None):
        nerve.maya.MayaObject.__init__(self, dag, input)
        if dag is None:
            return None
        else:
            self.setData()
        
    def getShaderName(self, name):
        outName = re.sub("[0-9]*\Z", "", name)
        outname = ""
        cap = False
        for i in range(0, len(outName)):
            if outName[i] == "_":
                cap = True
                continue
            if cap:
                outname += outName[i].upper()
                cap = False
            else:
                outname += outName[i]
        
        return outname        
        
    def setData(self):
        # Name 
        self["name"] = self.cleanName(self["dag"])
        
        # Material ID
        self["materialID"] = -1
        if cmds.attributeQuery("LEGO_materialID", node=self["shape"], exists=True):
            self["materialID"] = cmds.getAttr('%s.%s'%(self["shape"],"LEGO_materialID"))
    
        # Shader Data
        #print self["shape"]
        #self["shape"] = self["shape"].replace('Orig', '')
        shadingEngines = cmds.listConnections(self["shape"], skipConversionNodes=True, type="shadingEngine")
        #print shadingEngines
        shadingEngines = list(set(shadingEngines))
        shadingEngine = shadingEngines[0]
        shader = cmds.listConnections(shadingEngine + ".surfaceShader")[0]
        
        self["color"] = (0,0,0)
        self["tr"] = False
        
        self['texture'] = {}
        self['texture']['file'] = []
        self['texture']['scaleU'] = []
        self['texture']['scaleV'] = []
        self['texture']['offsetU'] = []
        self['texture']['offsetV'] = []
        self['texture']['rotate'] = []
        
        self["label"]  = False
        self["face"]  = False
        self["material"] = self.getShaderName(shader.split(':')[-1])
        self["shader"] = shader
        
        type = cmds.nodeType(shader)
        # PHONG E
        if type == "phongE":
            self["color"] = cmds.getAttr(shader + ".color")[0]
            if cmds.getAttr(shader + ".transparencyR") != 0.0 or shader[:2] == "Tr":
                self["tr"] = True
            
            
        # BLINN
        elif type == "blinn":
            self["color"] = cmds.getAttr(shader + ".color")[0]

        # LAYERED SHADER
        elif type == "layeredShader":
            subShaders = cmds.listConnections(shader, s=True, d=False)
            subShaders = list(set(subShaders))
            
            for subShader in subShaders:
                subShaderType = cmds.nodeType(subShader)
                
                textures = cmds.listConnections(subShader, type="file")
                if textures is None:
                    # PHONG_E || LAMBERT
                    if (subShaderType == "phongE" or subShaderType == "lambert" or subShaderType == "blinn"):
                        self["color"] = cmds.getAttr(subShader + ".color")[0]
                        self["material"] = self.getShaderName(subShader)
                        if cmds.getAttr(subShader + ".transparencyR") != 0.0 and subShader[:2] == "Tr":
                            self["tr"] = True                        
                        
                    # Label
                    if subShaderType == "lambert":
                        self["label"] = True
                        self["name"] = "Label"
                # TEXTURES
                else:
                    textures = list(set(textures))
                    for tex in textures:
                        file = cmds.getAttr(tex + ".fileTextureName")
                        placement = cmds.listConnections(tex, type="place2dTexture")[0]
                        
                        scaleU = cmds.getAttr(placement + ".coverageU")
                        scaleV = cmds.getAttr(placement + ".coverageV")
                        offsetU = cmds.getAttr(placement + ".translateFrameU")
                        offsetV = cmds.getAttr(placement + ".translateFrameV")
                        rotate = cmds.getAttr(placement + ".rotateUV")
                        
                        self["texture"]["file"].append( file )
                        self["texture"]["scaleU"].append( scaleU )
                        self["texture"]["scaleV"].append( scaleV )
                        self["texture"]["offsetU"].append( offsetU )
                        self["texture"]["offsetV"].append( offsetV )
                        self["texture"]["rotate"].append( rotate )
                        
                        
            cmds.setAttr(shader + ".hardwareColorR", self["color"][0])
            cmds.setAttr(shader + ".hardwareColorG", self["color"][1])
            cmds.setAttr(shader + ".hardwareColorB", self["color"][2])
        # LAMBERT
        elif type == "lambert":
            self["color"] = cmds.getAttr(shader + ".color")[0]
            self["face"] = True

    def setAttr(self):
    
        # color
        self.setToAttr(self["shape"] + ".Cd", self['color'], attrType='color')
        self.setToAttr(self["shape"] + ".mtoa_constant_color", self['color'], attrType='color')
        
        # texture
        if self["texture"] != '':
            if(self["texture"]["file"]):
                texture = self["texture"]
        
                dataList = []
                if isinstance(texture["file"], list):
                    for i in range(0, len(self["texture"]["file"])):
                        textureList = [ texture["file"][i] , str(texture["scaleU"][i]), str(texture["scaleV"][i]), str(texture["offsetU"][i]), str(texture["offsetV"][i]), str(self["texture"]["rotate"][i]) ]
                        dataList.append( '|'.join(textureList) )
                else:
                    textureList = [ texture["file"] , str(texture["scaleU"]), str(texture["scaleV"]), str(texture["offsetU"]), str(texture["offsetV"]), self["texture"]["rotate"] ]
                    dataList.append( '|'.join(textureList) )
                textureData = ';'.join(dataList)
            else:
                textureData = ''
            
            self.setToAttr(self["shape"] + ".abcTex", textureData, attrType="string")
        else:
            self.setToAttr(self["shape"] + ".abcTex", '', attrType='string')
        
        # transparent
        self.setToAttr(self["shape"] + ".abcTr", self["tr"], attrType="bool")
        
        # label
        self.setToAttr(self["shape"] + ".abcLabel", self["label"], attrType="bool")
        
        # face
        self.setToAttr(self["shape"] + ".abcFace", self["face"], attrType="bool")
        
        # label
        self.setToAttr(self["shape"] + ".abcFace", self["face"], attrType="bool")
        
        # material
        self.setToAttr(self["shape"] + '.abcMaterial', self["material"], attrType="string")
        self.setToAttr(self["shape"] + '.abcMaterialID', self["materialID"], attrType="int")


def setAlembicData(*args):
    print '## MATERIALS ##'
    os = cmds.ls(sl=True, l=True)
    
    if not len(os):
        print "Nothing Selected",
        return False
    
    cmds.select(hi=True)
    sel = cmds.ls(sl=True, l=True, type="mesh")
    
    materials = []
    nodes = []
    for n in sel:
        brick = Brick(n)
        brick.setAttr()
        if brick["material"] not in materials:
            materials.append(brick["material"])
            nodes.append(brick["shader"])
    
    for i in range(len(materials)):
        mat = materials[i]
        node = nodes[i]
        print '\t'+ mat + '\t\t\t' + node
        
    cmds.select(os, r=True)
    

    
    
def switchHiLow(*args):
    filters = ["World_ctr", 'moveall_0_ctrl']
    attribs = ["HighLow", 'High_Low']
    for filter in filters:
        sel = cmds.ls("*%s"%filter)
        sel.extend( cmds.ls("*:*%s"%filter) )
        if len(sel):
            for n in sel:
                for attr in attribs:
                    if cmds.attributeQuery(attr, node=n, exists=True):
                        if args[0] == "hi":
                            cmds.setAttr("%s.%s"%(n,attr), 0)    
                        else:
                            cmds.setAttr("%s.%s"%(n,attr), 1)        
                    

def abcImportAll(*args):
    workspace = cmds.workspace(q=True, rd=True)
    path = workspace + "scenes/_published/alembic/"
    folders = glob.glob(path + "*")
    abcList = []
    for folder in folders:    
        abcList.append( folder.split("\\")[-1] )
        
    def doIt(*args):
        value = cmds.optionMenu(args[0], q=True, v=True)
        workspace = cmds.workspace(q=True, rd=True)
        
        path = workspace + "scenes/_published/alembic/"
        folders = ['ALL', 'camExport', 'staticMESH']
        files = []
        for folder in folders:
            tpath = path + value + "/" + folder + "/*.abc"
            files.extend( glob.glob(tpath) )

        i = []
        for f in files:
            i.append('filename='+f)

        cmds.ExocortexAlembic_import(j=i)
        cmds.layoutDialog(dismiss="OK")
            

    def ui(*args):
        form = cmds.setParent(q=True)
        cmds.formLayout(form, e=True, width=200, height=50)
        
        cmds.columnLayout(rowSpacing=50)
        cmds.columnLayout(columnOffset=["left", 20])
        ctrl = cmds.optionMenu( label='Alembics' )
        for abc in args[0]:
            cmds.menuItem( label=abc )
            
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=2)
        b1 = cmds.button( label='OK', height=30, width=100, c=partial(doIt, ctrl))
        b2 = cmds.button( label='Cancel', height=30, width=100, c='import maya.cmds as cmds;cmds.layoutDialog( dismiss="Cancel" )')
        
    cmds.layoutDialog(ui=partial(ui, abcList))    


    
    
        

def abcExportAll(*args):

    if not cmds.pluginInfo("MayaExocortexAlembic", q=True, l=True):
        cmds.loadPlugin("MayaExocortexAlembic")    

    def getObjects():
        sel  = cmds.ls(sl=True, l=True)
        objlist = []
        children = cmds.listRelatives(sel, ad=True, ni=True, f=True, type="mesh")
        for c in children:
            getParent = cmds.listRelatives(c, p=True, ni=True, f=True)[0]
            if getParent not in objlist:
                objlist.append(getParent)
                
        return objlist

    os = cmds.ls("*Render_Mesh_grp")
    for n in os:
        if "Static" in n:
            continue

        name = n.split("_")[0].split(":")[-1]
        
        objects = []
        cmds.select(n, r=True)
        objects.extend(getObjects())
    
        filename = cmds.workspace(q=True, rootDirectory=True).replace("maya/", "elements/3D/") + name
        # DATA
        bricks = Brick()
        for obj in objects:
            #print obj
            bricks.insert( Brick(obj) )
        bricks.save(filename + ".xml")
    
        ## CRATE
        args = {}
        args["filename"] = filename + ".abc"
        args["in"] = int(cmds.playbackOptions(q=True, min=True))
        args["out"] = int(cmds.playbackOptions(q=True, max=True))
        args["step"] = 1
        args["normals"] = 1
        args["uvs"] = 1
        args["facesets"] = 0
        args["purepointcache"] = 0
        args["dynamictopology"] = 1
        
        args["ogawa"] = 0
        args["objects"] = objects
        
        cmd = ""    
        for key in args.keys():
            if isinstance(args[key], list):
                cmd+= key + "="
                for l in args[key]:
                    cmd+= l + ","
                cmd+= ";"
            cmd+= key + "=" + str(args[key]) + ";"

        
        print "## CRATE EXPORT ##"
        print cmd
        cmds.ExocortexAlembic_export(j=[cmd])            
        
        
def abcExport(*args):

    if not cmds.pluginInfo("MayaExocortexAlembic", q=True, l=True):
        cmds.loadPlugin("MayaExocortexAlembic")    


    os = cmds.ls(sl=True, l=True)
    if not len(os):
        print "Nothing Selected.",
        return False
    
    name = os[0].split("|")[1].split("_")[0].split(":")[-1]
    
    result = cmds.promptDialog(
        title='Alembic Name',
        message='Enter Name:',
        button=['OK', 'Cancel'],
        defaultButton='OK',
        cancelButton='Cancel',
        dismissString='Cancel',
        text=name)
        
    if result == 'OK':
        name = cmds.promptDialog(query=True, text=True)
        
    if result == 'Cancel':
        print "Canceled.",
        return False
        
    def getObjects():
        sel  = cmds.ls(sl=True, l=True)
        objlist = []
        children = cmds.listRelatives(sel, ad=True, ni=True, f=True, type="mesh")
        for c in children:
            getParent = cmds.listRelatives(c, p=True, ni=True, f=True)[0]
            if getParent not in objlist:
                objlist.append(getParent)
                
        return objlist
        
    objects = []
    sel = cmds.ls(sl=True, l=True)
    for n in sel:
        cmds.select(n, r=True)
        objects.extend(getObjects())
    
    filename = cmds.workspace(q=True, rootDirectory=True).replace("maya/", "elements/3D/") + name
    # DATA
    bricks = Brick()
    for obj in objects:
        #print obj
        bricks.insert( Brick(obj) )
        
    bricks.save(filename + ".xml")
    
    ## CRATE
    args = {}
    args["filename"] = filename + ".abc"
    args["in"] = int(cmds.playbackOptions(q=True, min=True))
    args["out"] = int(cmds.playbackOptions(q=True, max=True))
    args["step"] = 1
    args["normals"] = 1
    args["uvs"] = 1
    args["facesets"] = 0
    args["purepointcache"] = 0
    args["dynamictopology"] = 1
    
    args["ogawa"] = 0
    args["objects"] = objects
    
    cmd = ""    
    for key in args.keys():
        if isinstance(args[key], list):
            cmd+= key + "="
            for l in args[key]:
                cmd+= l + ","
            cmd+= ";"
        cmd+= key + "=" + str(args[key]) + ";"

    
    print "## CRATE EXPORT ##"
    print cmd
    cmds.ExocortexAlembic_export(j=[cmd])    
    
def abcAttachData(*args):
    sel = cmds.ls(sl=True, l=True)
    for n in sel:
        tmp = cmds.listConnections(n, type="ExocortexAlembicXform")
        if tmp is None:
            continue
        tmp = cmds.listConnections(tmp[0], type="ExocortexAlembicFile")[0]
        
        filename = cmds.getAttr(tmp + ".fileName").replace(".abc", ".xml")
        brick = Brick(dag=None, input=filename)
        for b in brick.database:
            if cmds.objExists(b["dag"]):
                b.setAttr()
                

def createShaders(*args):
    os = cmds.ls(sl=True, l=True)
    cmds.select(hi=True)
    sel = cmds.ls(sl=True, l=True, type="mesh")
    
    def getDefaults():
        lib = \
        {
            "opaque":
            {
                "colorR": 0,
                "colorG": 0,
                "colorB": 0,
                "Kd": 0.8,                        
                "Ks": 0.05,                        
                "specularRoughness": 0.560,        
                "specularFresnel": 1,            
                "Ksn": 0.800                
            },
            "label":
            {
                "colorR": 0,
                "colorG": 0,
                "colorB": 0,
                "Kd": 0.8,                        
                "Ks": 0.05,                        
                "specularRoughness": 0.560,        
                "specularFresnel": 1,            
                "Ksn": 0.800                
            },            
            "Tr":
            {
                "colorR": 0,
                "colorG": 0,
                "colorB": 0,
                "Kd":0.0,
                "Ks":0.0,
                "specularRoughness":0.0,
                "specularFresnel":True,
                "Kr":1.0,
                "enableInternalReflections":False,
                "Fresnel":True,
                "Kt": 1.0,
                "IOR":1.5,
                "transmittanceR":0,
                "transmittanceG":0,
                "transmittanceB":0                
            }
        }
        return lib
        
    
    def getData(s):
        data = {}
        
        data["color"] = cmds.getAttr(s + ".Cd")[0]
        data["Tr"] = cmds.getAttr(s + ".abcTr")
        data["label"] = cmds.getAttr(s + ".abcLabel")
        data["material"] = cmds.getAttr(s + ".abcMaterial")
        data["materialID"] = cmds.getAttr(s + ".abcMaterialID")
        data["face"] = cmds.getAttr(s + ".abcFace")
        data["textures"] = []
        
        tex = cmds.getAttr(s + ".abcTex")
        if tex == '' or tex == unicode(''):
            return data
            
        tmp = str(tex).split(";")
        data["textures"] = tmp
        
        return data
        
    
    for n in sel:
        obj = nerve.maya.MayaObject(n)
        data = getData(obj["shape"])
        obj.update(data)

        
        shader = 'M_' + obj["material"]
        if obj["face"]:
            shader = 'M_Face'
            
        if not cmds.objExists(shader):
            shader = cmds.createNode('aiStandard', name=shader)
            cmds.addAttr(shader, ln="materialID", at="long", k=True)
            cmds.setAttr(shader + ".materialID", obj["materialID"])
            
            cmds.addAttr(shader, ln="aov", at="bool", k=True)
            cmds.setAttr(shader + ".aov", False)
            
            if obj["face"]:
                ud = cmds.createNode("aiUserDataColor")
                cmds.setAttr(ud + ".colorAttrName", "color", type="string")
                cmds.connectAttr(ud + ".outColor", shader + ".color", f=True)            
        
        # Transparent
        if obj["Tr"] and obj["material"] != "TransparentLabel":
            cmds.setAttr(obj["shape"] + ".aiOpaque", False)
            attributes = getDefaults()["Tr"]
            
            attributes["colorR"] = obj["color"][0]
            attributes["colorG"] = obj["color"][1]
            attributes["colorB"] = obj["color"][2]
            
            attributes["transmittanceR"] = obj["color"][0]
            attributes["transmittanceG"] = obj["color"][1]
            attributes["transmittanceB"] = obj["color"][2]
            
            for attr in attributes.keys():
                cmds.setAttr(shader + "." + attr, attributes[attr])
        # FACE
        elif obj["face"]:
            pass
        
        # Label
        elif obj["label"] or obj["material"] == "TransparentLabel":
            cmds.setAttr(obj["shape"] + ".aiOpaque", False)
            cmds.setAttr(obj["shape"] + ".castsShadows", False)
            attributes = getDefaults()["label"]
            
            attributes["colorR"] = obj["color"][0]
            attributes["colorG"] = obj["color"][1]
            attributes["colorB"] = obj["color"][2]
            
            for attr in attributes.keys():
                cmds.setAttr(shader + "." + attr, attributes[attr])
        # Opaque
        else:
            attributes = getDefaults()["opaque"]
            
            attributes["colorR"] = obj["color"][0]
            attributes["colorG"] = obj["color"][1]
            attributes["colorB"] = obj["color"][2]
            
            for attr in attributes.keys():
                cmds.setAttr(shader + "." + attr, attributes[attr])
                
        
        # Textures
        if len(obj["textures"]):
            outShader = cmds.createNode('aiStandard', name=shader.replace("M_", "Msub_") + "_1")
            
            fileTextures = []
            for texture in obj["textures"]:
                tmp = texture.split('|')
                # place2dTexture
                placement = cmds.createNode("place2dTexture")
                cmds.setAttr(placement + ".coverageU", float(tmp[1]) )
                cmds.setAttr(placement + ".coverageV", float(tmp[2]) )
                cmds.setAttr(placement + ".translateFrameU", float(tmp[3]) )
                cmds.setAttr(placement + ".translateFrameV", float(tmp[4]) )
                cmds.setAttr(placement + ".rotateUV", float(tmp[5]) )
                cmds.setAttr(placement + ".wrapU", 0)
                cmds.setAttr(placement + ".wrapV", 0)
                
                # file
                fileNode = cmds.createNode("file")
                fileTextures.append(fileNode)
                cmds.setAttr(fileNode + ".fileTextureName",tmp[0], type="string")
                cmds.setAttr(fileNode + ".defaultColor", 0, 0, 0)
                
                # make connections
                con = ['rotateUV', 'offset', 'noiseUV', 'vertexCameraOne', 'vertexUvThree', 'vertexUvTwo', 'vertexUvOne', 'repeatUV', 'wrapV', 'wrapU', 'stagger', 'mirrorV', 'mirrorU', 'rotateFrame', 'translateFrame', 'coverage']
                cmds.connectAttr(placement + ".outUV", fileNode + '.uvCoord', f=True)
                cmds.connectAttr(placement + ".outUvFilterSize", fileNode + '.uvFilterSize', f=True)
                for c in con:
                    cmds.connectAttr(placement + '.' + c, fileNode + '.' + c, f=True)
                
            lt = cmds.createNode("layeredTexture")
            for i in range(len(fileTextures)):
                cmds.connectAttr(fileTextures[i] + ".outColor", lt + ".inputs["+str(i)+"].color", f=True)
                cmds.connectAttr(fileTextures[i] + ".outAlpha", lt + ".inputs["+str(i)+"].alpha", f=True)
                
            # condition
            condition = cmds.createNode("condition", name="IF_premultSwitch_1")
            cmds.setAttr(condition + '.secondTerm', 1.0)
            cmds.setAttr(condition + '.secondTerm', 1.0)
            cmds.setAttr(condition + ".colorIfFalse", 1.0, 1.0, 1.0)
            cmds.connectAttr(lt + ".outAlpha", condition + ".colorIfTrueR", f=True)
            cmds.connectAttr(lt + ".outAlpha", condition + ".colorIfTrueG", f=True)
            cmds.connectAttr(lt + ".outAlpha", condition + ".colorIfTrueB", f=True)

            # premult
            premult = cmds.createNode("multiplyDivide", name="MD_premult_1")
            cmds.connectAttr(lt + ".outColor", premult + ".input1", f=True)
            cmds.connectAttr(condition + ".outColor", premult + ".input2", f=True)
            
            # Diffuse
            dif = cmds.createNode("layeredTexture", name="LT_diffuse_1")
            cmds.connectAttr(premult + ".output", dif + ".inputs[0].color", f=True )
            cmds.connectAttr(lt + ".outAlpha", dif + ".inputs[0].alpha", f=True)
            if obj["Tr"]:
                cmds.setAttr(dif + ".inputs[1].color", 0,0,0)
            else:
                cmds.connectAttr(shader + ".color", dif + ".inputs[1].color", f=True)
            cmds.connectAttr(dif + ".outColor", outShader + ".color", f=True)
            
            # Specular & Reflection
            spec = cmds.createNode("layeredTexture", name="LT_spec_1")
            cmds.connectAttr(lt + ".outAlpha", spec + ".inputs[0].alpha", f=True)
            
            if not cmds.attributeQuery("texSpecularMult", node=shader, exists=True):
                cmds.addAttr(shader, ln="texSpecularMult", at="double", min=0.0, max=1.0, dv=0.25, k=True)
            cmds.setAttr(shader + ".texSpecularMult", 0.250)
            
            cmds.connectAttr(shader + ".texSpecularMult", spec + ".inputs[0].colorR", f=True)
            cmds.connectAttr(shader + ".texSpecularMult", spec + ".inputs[0].colorG", f=True)
            cmds.connectAttr(shader + ".texSpecularMult", spec + ".inputs[0].colorB", f=True)
            
            cmds.setAttr(spec + ".inputs[1].colorR", 1)
            cmds.setAttr(spec + ".inputs[1].colorG", 1)
            cmds.setAttr(spec + ".inputs[1].colorB", 1)
            cmds.setAttr(spec + ".inputs[1].alpha", 1)
            
            cmds.connectAttr(spec + ".outColor", outShader + ".KsColor", f=True)
            cmds.connectAttr(spec + ".outColor", outShader + ".KrColor", f=True)
            
            
            if obj["Tr"] and obj["material"] != "TransparentLabel":
                # Refraction
                refr = cmds.createNode("layeredTexture", name="LT_refr_1")
                cmds.connectAttr(lt + ".outAlpha", refr + ".inputs[0].alpha", f=True)
                
                cmds.setAttr(refr + ".inputs[0].colorR", 0)
                cmds.setAttr(refr + ".inputs[0].colorG", 0)
                cmds.setAttr(refr + ".inputs[0].colorB", 0)
                
                cmds.setAttr(refr + ".inputs[1].colorR", 1.0)
                cmds.setAttr(refr + ".inputs[1].colorG", 1.0)
                cmds.setAttr(refr + ".inputs[1].colorB", 1.0)
                cmds.setAttr(refr + ".inputs[1].alpha", 1.0)
                
                cmds.connectAttr(refr + ".outColor", outShader + ".KtColor", f=True)
            
                # EMIT
                emit = cmds.createNode("layeredTexture", name="LT_emit_1")
                cmds.connectAttr(lt + ".outAlpha", emit + ".inputs[0].alpha", f=True)
                cmds.setAttr(emit + ".inputs[0].colorR", 1.0)
                cmds.setAttr(emit + ".inputs[0].colorG", 1.0)
                cmds.setAttr(emit + ".inputs[0].colorB", 1.0)
                
                cmds.setAttr(emit + ".inputs[1].colorR", 0.1)
                cmds.setAttr(emit + ".inputs[1].colorG", 0.1)
                cmds.setAttr(emit + ".inputs[1].colorB", 0.1)
                cmds.setAttr(emit + ".inputs[1].alpha", 1.0)
                
                cmds.connectAttr(emit + ".outColor", outShader + ".emissionColor", f=True)
                
            elif obj["label"] or obj["material"] == "TransparentLabel":
                opac = cmds.createNode("layeredTexture", name="LT_opac_1" )
                cmds.connectAttr(lt + ".outAlpha", opac + ".inputs[0].alpha", f=True)
                cmds.setAttr(opac + ".inputs[0].colorR", 1.0)
                cmds.setAttr(opac + ".inputs[0].colorG", 1.0)
                cmds.setAttr(opac + ".inputs[0].colorB", 1.0)
                
                cmds.setAttr(opac + ".inputs[1].colorR", 0.0)
                cmds.setAttr(opac + ".inputs[1].colorG", 0.0)
                cmds.setAttr(opac + ".inputs[1].colorB", 0.0)
                cmds.setAttr(opac + ".inputs[1].alpha", 1.0)
                
                cmds.connectAttr(opac + ".outColor", outShader + ".opacity", f=True)
                
                
            
            # ID
            id = cmds.createNode("layeredTexture", name="LT_id_1")
            cmds.connectAttr(lt + ".outAlpha", id + ".inputs[0].alpha", f=True)
            cmds.setAttr(id + ".inputs[0].colorR", 0.0)
            cmds.setAttr(id + ".inputs[0].colorG", 1.0)
            cmds.setAttr(id + ".inputs[0].colorB", 1.0)
            
            cmds.setAttr(id + ".inputs[1].colorR", 1.0)
            cmds.setAttr(id + ".inputs[1].colorG", 0.0)
            cmds.setAttr(id + ".inputs[1].colorB", 1.0)
            cmds.setAttr(id + ".inputs[1].alpha", 1.0)
            
            # Label
            if obj["label"]:
                cmds.connectAttr(lt + ".outAlpha", outShader + ".opacityR", f=True)
                cmds.connectAttr(lt + ".outAlpha", outShader + ".opacityG", f=True)
                cmds.connectAttr(lt + ".outAlpha", outShader + ".opacityB", f=True)
            
            # Connect to main Shader
            attributes = cmds.listAttr(shader, c=True, lf=True, s=True)
            attributes.append("transmittance")
            for attr in attributes:
                # exists
                if cmds.attributeQuery(attr, node=outShader, exists=True):
                    # is already connected
                    tmp = cmds.listConnections(outShader + "." + attr)
                    # has parent
                    parent = cmds.attributeQuery(attr, node=outShader, listParent=True)
                    if tmp is None and parent is None:
                        cmds.connectAttr(shader + "." + attr, outShader + "." + attr, f=True)
                    
            
            
            if obj["Tr"]:
                cmds.disconnectAttr(shader + ".Kd", outShader + ".Kd")
                cmds.setAttr(outShader + ".Kd", getDefaults()["opaque"]["Kd"])
                
            shader = outShader
            
            
        # ID
        tmp = cmds.listConnections(shader + ".nodeState", type="aiUtility")
        if tmp is None:
            util = cmds.createNode("aiUtility")
            cmds.setAttr(util + ".shadeMode", 2)
            cmds.addAttr(util, ln="AOV", dt="string", k=True)
            cmds.setAttr(util + ".AOV", obj["material"], type="string")
            
            
            cmds.connectAttr(shader + ".nodeState", util + ".nodeState", f=True)
            if len(obj["textures"]):
                cmds.connectAttr(id + ".outColor", util + ".color", f=True)
            else:
                cmds.setAttr(util + ".colorR", 1.0)
                cmds.setAttr(util + ".colorG", 0.0)
                cmds.setAttr(util + ".colorB", 0.0)
        else:
            util = tmp[0]
            
        # ASSIGN
        cmds.select(obj["shape"], r=True)
        cmds.hyperShade(a=shader)
                
                
    cmds.select(sel, r=True)

def clearAOVs(*args):
    sel = cmds.ls(type="aiAOV")
    d = []
    for n in sel:
        name = cmds.getAttr(n + ".name")
        tmp = cmds.listConnections(n + ".enabled", type="aiStandard")
        if 'ID_' in name and tmp is not None:
            d.append(n)
            
    cmds.delete(d)
    
    
def createAOVs(*args):

    def removeAOVs():
        aovs = cmds.ls(type="aiAOV")
        for aov in aovs:
            if cmds.getAttr(aov + ".name")[:3] == "ID_":
                cmds.delete(aov)
    removeAOVs()

    tmp = cmds.ls(type="aiUtility")
    shaders = []
    for t in tmp:
        if cmds.attributeQuery("AOV", node=t, exists=True):
            shaders.append(t)
    
                
    def getAOVNames():
        names = []
        aovs = cmds.ls(type="aiAOV")
        for aov in aovs:
            names.append(cmds.getAttr(aov + ".name"))
            
        return names
        
    aovInterface = mtoa.aovs.AOVInterface()
    
    for shader in shaders:
        # name
        name = "ID_" + cmds.getAttr(shader + ".AOV")
        name = name[:29]
        if name not in getAOVNames():
            aiAOV = aovInterface.addAOV(name)
            mat = 'M_' + cmds.getAttr(shader + ".AOV")
            if cmds.objExists(mat) and cmds.attributeQuery("aov", node=mat, exists=True):
                cmds.connectAttr(mat + ".aov", aiAOV._node + ".enabled")
            
        material = cmds.listConnections(shader + ".nodeState", type="aiStandard")[0]
        shadingEngine = cmds.listConnections(material + ".outColor", type="shadingEngine")[0]
        
        idx = cmds.getAttr(shadingEngine + ".aovs", multiIndices=True)
        for i in idx:
            aovname = cmds.getAttr(shadingEngine + ".aovs[" + str(i) + "].aov_name")
            if aovname == name:
                #print shader
                #print shadingEngine
                try:
                    cmds.connectAttr(shader + ".outColor", shadingEngine + ".aovs["+str(i)+"].aov_input", f=True)
                except:
                    pass
        

def setAovOverride(*args):

    shaders = getSceneShaders()
    renderLayer = cmds.editRenderLayerGlobals(q=True, currentRenderLayer=True)    
    for n in shaders:
        cmds.setAttr(n + ".aov", False)
        cmds.editRenderLayerAdjustment(n + ".aov", layer=renderLayer)
        cmds.setAttr(n + ".aov", True)    
        
        
def exportShaders(*args):

    shaders = []
    
    tmp = cmds.ls("M_*", type="aiStandard")
    for t in tmp:
        if cmds.attributeQuery("materialID", node=t, exists=True):
            shaders.append(t)
            
    shaderLibrary = BrickShader()
    for shader in shaders:
        bs = BrickShader(shader)
        
        # get attributes
        attributes = []
        tmp = cmds.listAttr(shader, visible=True, output=True, settable=True)
        for t in tmp:
            children = cmds.attributeQuery(t, node=shader, listChildren=True)
            if children is None:
                attributes.append(t)
            
        bs["attributes"] = []            
        for attr in attributes:
            data = {}
            data["name"] = attr
            data["value"] = cmds.getAttr(bs["node"] + "." + attr)
            data["type"] = cmds.getAttr(bs["node"] + "." + attr, type=True)
            bs["attributes"].append( data )
            
        shaderLibrary.insert(bs)
    
    filename = cmds.workspace(q=True, rootDirectory=True) + "data/shaders.xml"
    shaderLibrary.save(filename)

def importShaders(*args):
    filename = cmds.workspace(q=True, rootDirectory=True) + "data/shaders.xml"
    shaderLibrary = BrickShader(input=filename)
    for shader in shaderLibrary.database:
        if cmds.objExists(shader["node"]):
            for data in shader["attributes"]:
            
                attr = data["name"]
                if not cmds.attributeQuery(attr, node=shader["node"], exists=True):
                    continue
                    
                value = data["value"]
                atype = data["type"]
                
                if value == "False":
                    value = False
                if value == "True":
                    value = True
                
                if atype == "long" or atype == "enum":
                    value = int(value)
                if atype == "float" or atype == "double":
                    value = float(value)
                if atype == "string":
                    value = str(value)
                
                if atype == "string":
                    cmds.setAttr(shader["node"] + "." + attr, value, type="string")
                else:
                    cmds.setAttr(shader["node"] + "." + attr, value)
                
    
def getSceneShaders():
    shaders = []
    tmp = cmds.ls("M_*", type="aiStandard")
    for t in tmp:
        if cmds.attributeQuery("materialID", node=t, exists=True):
            shaders.append(t)
    return shaders

def selectSceneShaders(*args):
    cmds.select(getSceneShaders(), r=True)
    
def propagateAlphaSettings(*args):

    shaders = getSceneShaders()
        
    renderLayer = cmds.editRenderLayerGlobals(q=True, currentRenderLayer=True)
    for shader in shaders:
        cmds.editRenderLayerAdjustment(shader + ".transmittance", shader + ".emission", layer=renderLayer)
        
        if cmds.getAttr(shader + ".Kt") > 0.0:
            cmds.setAttr(shader + ".transmittance", 1.0, 1.0, 1.0)
            
            tmp = cmds.listConnections(shader + ".emissionColor")
            if tmp is None:
                cmds.setAttr(shader + ".emission", 0.1)
            else:
                
                cmds.setAttr(shader + ".emission", 1.0)
        else:
            cmds.setAttr(shader + ".emission", 1.0)
    

def switchHiLowRez(*args):

    sel = cmds.ls("*World_ctr")
    sel.extend( cmds.ls("*:*World_ctr") )
    if len(sel):
        for n in sel:
            if cmds.attributeQuery("HighLow", node=n, exists=True):
                #print "OK"
                v = cmds.getAttr(n+".HighLow")
                cmds.setAttr(n + ".HighLow", (1-v))
                
def fixTexturePaths(*args):
    workspace = cmds.workspace(q=True, rootDirectory=True) + "sourceimages/"
    os.listdir(workspace)

    folders = [workspace]
    dirs = os.listdir(workspace)
    for dir in dirs:
        folders.append( workspace + dir  + "/")


    sel = cmds.ls(type="file")
    for n in sel:
        f = cmds.getAttr(n + ".fileTextureName")
        if os.path.isfile(f):
            continue
        else:
            success = False
            for folder in folders:
                newfiles = []
                newfile = folder + f.split("/")[-1]
                newfiles.append(newfile)
                newfiles.append( newfile.split(".")[0] + ".png" )
                newfiles.append( newfile.split(".")[0] + ".tga" )
                '''
                if os.path.isfile(newfile):
                    success = True
                    cmds.setAttr(n + ".fileTextureName", newfile, type="string")
                '''
                for nf in newfiles:
                    if os.path.isfile(nf):
                        success = True
                        cmds.setAttr(n + ".fileTextureName", nf, type="string")
            
            if success is False:
                print n
                print f
                print ""    
def addFaceTextureAttribute(*args):
    import maya.cmds as cmds
    import glob

    sel = cmds.ls(sl=True)
    namespace = sel[0].split(":")[0]
    head = namespace + ":L_Head"
    ctrl = namespace + ":head_ctrl"

    if cmds.objExists(head):
        # Head Shape
        headShape = cmds.listRelatives(head, s=True)[0]
        
        # get product name
        filename = cmds.referenceQuery(sel[0], f=True)
        product = filename.split("/")[-2].split("_")[0]
        
        # get texture
        shadingEngine = cmds.listConnections(headShape, type="shadingEngine")[0]
        shader = cmds.listConnections(shadingEngine, type="layeredShader")[0]
        phong = cmds.listConnections(shader, type="phongE")[0]
        texture = cmds.listConnections(phong, type="file")[0]
        
        cmds.setAttr(texture + ".useFrameExtension", True)
        currentTexture = cmds.getAttr(texture  + ".fileTextureName").split("/")[-1].split(".tga")[0]
        
        #get file list
        dir = cmds.workspace(q=True, o=True)
        dir+= "/sourceimages/Faces/" + product + "/"
        textures = glob.glob(dir + currentTexture + "*.*")
        
        cmds.setAttr(texture + ".fileTextureName", textures[0], type="string")
        
        if not cmds.attributeQuery("texture", node=ctrl, exists=True):
            cmds.addAttr(ctrl, ln="texture", at="long", k=True)
            cmds.setAttr(ctrl + ".texture", 1)
            
        cmds.connectAttr( ctrl + ".texture", texture + ".frameExtension", f=True)
    

    
def LODConnect(*args):
    attributes = ["translate", "rotate", "v"]
    
    osel = cmds.ls(sl=True, l=True)
    if len(osel) != 2:
        raise Exception("Selection error. Select FROM -> TO objects.")
    search = osel[0]
    replace = osel[1]
    
    cmds.select(hi=True)
    
    sel = cmds.ls(sl=True, l=True, type="transform")
    for n in sel:
        if 'Constraint' in n:
            continue
            
        target = n.replace(search, replace)
        if cmds.objExists(target):
            for attr in attributes:
                try:
                    srcPlug = '%s.%s' % (n, attr)
                    tarPlug = '%s.%s' % (target, attr)
                    cmds.connectAttr(srcPlug, tarPlug, f=True)
                except RuntimeError:
                    pass
        else:
            print "Could not find object: "
            print '\t '+ target+'\n'
            
        cmds.select(osel, r=True)

        

class cleanUp:
    def __init__(self):
        pass
        
    @staticmethod
    def header(msg):
        length = len(msg)+6
        print ''.ljust(length, '#')
        print '## %s ##' % (msg)
        print ''.ljust(length, '#')
        print ''
        
        
    @staticmethod
    def deleteCurves(*args):
        cleanUp.header("Deleting Curves")
        os = cmds.ls(sl=True, l=True)
        if not len(os):
            print "Nothing Selected."
            return False
        
        cmds.select(hi=True)
        sel = cmds.ls(sl=True, l=True, type="nurbsCurve")
        if not len(sel):
            print "No curves found."
            cmds.select(os, r=True)
            return False
            
        for n in sel:
            ct = cmds.listRelatives(n, p=True, pa=True)[0]
            print "Deleting Curve: " + ct.split("|")[-1]
            cmds.delete(ct)
            
        cmds.select(os, r=True)
            
    @staticmethod
    def deleteHiddenObjects(*args):
        cleanUp.header("Deleting Hidden Objects")
        os = cmds.ls(sl=True, l=True)
        if not len(os):
            print "Nothing Selected."
            return False
        
        cmds.select(hi=True)
        sel = cmds.ls(sl=True, l=True, type="transform", iv=True)
        if not len(sel):
            print "No hidden objects found."
            cmds.select(os, r=True)
            return False
            
        for n in sel:
            print "Deleting Hidden object: " + n.split("|")[-1]
            cmds.delete(n)
    
        
        cmds.select(os, r=True)
        
    @staticmethod
    def deleteEmptyGroups(*args):
        cleanUp.header("Deleting Empty Groups")
        os = cmds.ls(sl=True, l=True)
        if not len(os):
            print "Nothing Selected."
            return False
        
        cmds.select(hi=True)
        sel = cmds.ls(sl=True, l=True, type="transform")
            
        notFound = True
        for n in sel:
            if not cmds.listRelatives(n, c=True):
                if 'Constraint' in cmds.nodeType(n):
                    continue
                else:
                    notFound = False
                    print "Deleting Empty Group: " + n.split('|')[-1]
                    cmds.delete(n)
        
        if notFound:
            print "No empty groups found."
            
        cmds.select(os, r=True)
        
    @staticmethod
    def deleteExtraUvSets(*args):
        cleanUp.header("Deleting Extra UV Sets")
        os = cmds.ls(sl=True, l=True)
        if not len(os):
            print "Nothing Selected."
            return False
        
        cmds.select(hi=True)
        sel = cmds.ls(sl=True, l=True, type="mesh")
        notFound = True
        for n in sel:
            cmds.select(n, r=True)
            uvsets = cmds.polyUVSet(q=True, auv=True)
            for uvset in uvsets:
                if 'map1' not in uvset:
                    notFound = False
                    print 'Deleting extra UV set from object: ' + n.split('|')[-1] + ' -> ' + uvset
                    cmds.polyUVSet(currentUVSet=True, uvSet="map1")
                    cmds.polyUVSet(delete=True, uvSet=uvset)

        if notFound:
            print "No extra UV sets found."
                    
        cmds.select(os, r=True)
        
    @staticmethod
    def combineParentedObjects(*args):

        def getAttributeData(obj, extraAttributes = []):
        
            validTypes = ['long', 'string', 'bool', 'double3']
        
            data = []
            attributes = cmds.listAttr(obj, userDefined=True)
            attributes.extend(extraAttributes)
            
            for attr in attributes:
                
                if cmds.getAttr(obj + '.' + attr, type=True) not in validTypes:
                    continue 
                    
                data.append( {} )
                plug = '%s.%s' % (obj, attr)
                
                
                data[-1]["name"] = str(attr)
                data[-1]["value"] = cmds.getAttr(plug)
                data[-1]["type"] = str(cmds.getAttr(plug, type=True))
                data[-1]["locked"] = cmds.getAttr(plug, l=True)
                data[-1]["keyable"] = cmds.getAttr(plug, k=True)
                data[-1]["connected"] = False
                data[-1]["plug"] = None
                tmp = cmds.listConnections(plug, p=True)
                if tmp is not None:
                    data[-1]["connected"] = True
                    data[-1]["plug"] = tmp[0]
                
            return data
            
        def setAttributeData(obj, attributeData, debug=False):
            for attr in attributeData:

                # add attribute
                if not cmds.attributeQuery(attr["name"], node=obj, exists=True):
                    if attr["type"] == "string":
                        cmds.addAttr(obj, ln=attr["name"], dt=attr["type"], k=attr["keyable"])
                    else:
                        cmds.addAttr(obj, ln=attr["name"], at=attr["type"], k=attr["keyable"])
                        
                # set values
                plug = obj + "." + attr["name"]
                if attr["type"] == "double3":
                    cmds.setAttr(plug, attr["value"][0][0], attr["value"][0][1], attr["value"][0][2] )
                elif attr["type"] == "string":
                    cmds.setAttr(plug, attr["value"], type="string")
                else:
                    cmds.setAttr(plug, attr["value"])

                # make connections
                if attr["connected"]:
                    cmds.connectAttr(attr["plug"], plug, f=True)
                    
                # lock
                if attr["locked"]:
                    cmds.setAttr(plug, l=True)                    
            
        cleanUp.header("Combine Parent Objects")
        os = cmds.ls(sl=True, l=True)    
        
        if not len(os):
            print "Nothing Selected."
            return False
        
        cmds.select(hi=True)
        objects = reversed(cmds.ls(sl=True, l=True, type="transform"))
        for obj in objects:
            # is mesh not group
            mesh = cmds.listRelatives(obj, s=True, pa=True)
            if mesh is None:
                continue
                
            # CHILDREN
            children = cmds.listRelatives(obj, c=True, type="transform", pa=True, ad=True)
            if children is None:
                continue
            
            # get only mesh children
            merge = []
            for child in children:
                if cmds.listRelatives(child, s=True):
                    merge.append(child)
            
            if not len(merge):
                continue
                
            # MERGE
            merge.append(mesh[0])
            
            meshAttributes = getAttributeData(mesh[0])
            
            # make restore transform prep
            piv = cmds.xform(obj, q=True, ws=True, piv=True)
            
            grp = cmds.group(em=True, name=obj.split('|')[-1] + "_GRP")
            parent = cmds.listRelatives(obj, p=True, pa=True)
            cmds.select(grp, r=True)
            cmds.parent(grp, parent)
            grp = cmds.ls(sl=True, l=True)[0]
            
            attributes = ["translate", "rotate", "v"]
            for attr in attributes:
                if cmds.listConnections(obj + "." + attr, p=True) is not None:
                    con = cmds.listConnections(obj + "." + attr, p=True)[0]
                    cmds.connectAttr(con, grp + "." + attr, f=True)
                    cmds.disconnectAttr(con, obj + "." + attr)
                
            '''
            if True:
                # get attribute data
                objAttributes = getAttributeData(obj, ["translate", "rotate", "scale", "v"])
                meshAttributes = getAttributeData(mesh[0])
                
                # get parent
                parent = None
                tmp = cmds.listRelatives(obj, p=True, pa=True)
                if tmp:
                    parent = tmp[0]
                    
                attributes = ["translate", "rotate"]
                for attr in attributes:
                    tmp = cmds.listConnections(obj + "." + attr, p=True)
                    if tmp is not None:
                        cmds.disconnectAttr(tmp[0], obj + "." + attr)

                # reset position
                if parent is not None:
                    cmds.select(obj, r=True)
                    cmds.parent(obj, w=True)
                    obj = cmds.ls(sl=True, l=True)[0]
                        
                cmds.setAttr(obj + ".translate", 0,0,0 )
                cmds.setAttr(obj + ".rotate", 0,0,0 )
                
                
                # Fix Pivot
                piv = cmds.xform(obj, q=True, ws=True, piv=True)
                rpt = cmds.getAttr(obj + ".rotatePivotTranslate")[0]
                rp = cmds.getAttr(obj + ".rotatePivot")[0]
                
                cmds.setAttr(obj + ".rotatePivotTranslate", 0,0,0)
                #cmds.setAttr(obj + ".rotatePivot", 0,0,0)
                cmds.setAttr(obj + ".translate", rpt[0], rpt[1], rpt[2])
                cmds.makeIdentity(obj, apply=True, pn=True, n=False, t=True, r=True)
                
                if parent is not None:
                    cmds.select(obj, r=True)
                    cmds.parent(obj, parent)
                    obj = cmds.ls(sl=True, l=True)[0]
            
                # DO MERGE
            
            '''
            print "Merging: " + obj.split('|')[-1]
            merge.append( cmds.listRelatives(obj, s=True, pa=True)[0] )
            cleanName = obj.split("|")[-1].split(":")[-1]
            cmds.select(merge, r=True)
            mergedObj = cmds.polyUnite(merge, ch=False, n=cleanName)[0]
            
            #cmds.xform(mergedObj, ws=True, piv=(piv[0], piv[1], piv[2]))
            #cmds.xform(mergedObj, ws=True, t=(pos[0], pos[1], pos[2]))
            #cmds.xform(mergedObj, ws=True, ro=(rot[0], rot[1], rot[2]))
            
            #cmds.setAttr(mergedObj + ".translate", piv[0], piv[1], piv[2])
            #cmds.makeIdentity(mergedObj, apply=True, pn=True, n=False, t=True, r=True)
                        
            #cmds.parent(mergedObj, parent)
            
            cmds.parent(mergedObj, grp)
            mergedObj = cmds.ls(sl=True, l=True)[-1]
            cmds.xform(mergedObj, ws=True, piv=(piv[0], piv[1], piv[2]))
            
            mergedMesh = cmds.listRelatives(mergedObj, s=True, pa=True)[0]
            
            # set attribute data
            #setAttributeData(mergedObj, objAttributes)
            setAttributeData(mergedMesh, meshAttributes, True)
            
            # RESTORE
            cmds.makeIdentity(mergedObj, apply=True, t=True, r=True, s=False, n=False, pn=True)
            cmds.delete(mergedMesh, ch=True)
            
            cmds.parent(mergedObj, parent)
            mergedObj = cmds.ls(sl=True, l=True)[0]
            for attr in attributes:
                if cmds.listConnections(grp + "." + attr, p=True) is not None:
                    con = cmds.listConnections(grp + "." + attr, p=True)[0]
                    cmds.connectAttr(con, mergedObj + "." + attr, f=True)    
            cmds.delete(grp)
            
        cmds.select(os, r=True)
            
            
    @staticmethod
    def mergeVertices(*args):
        #cleanUp.header("Merging Vertices")
        os = cmds.ls(sl=True, l=True)
        if not len(os):
            print "Nothing Selected."
            return False
        
        cmds.select(hi=True)
        sel = cmds.ls(sl=True, l=True, type="mesh")

        gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
        cmds.progressBar(gMainProgressBar, edit=True, beginProgress=True, isInterruptable=True, status="Merging Vertices...", maxValue=len(sel))
        for n in sel:
            if cmds.progressBar(gMainProgressBar, query=True, isCancelled=True):
                print "Interrupted"
                break
            
            cmds.select(n, r=True)
            cmds.polyMergeVertex(d=0.0001, ch=False)
            cmds.progressBar(gMainProgressBar, edit=True, step=1)
        cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
            
        print "Done."
        cmds.select(os, r=True)
    
    @staticmethod
    def fixFaceAssignments(*args):
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
            attr  = "LEGO_materialID"
            materialId = -1
            if cmds.attributeQuery(attr, node=n, exists=True):
                materialId = cmds.getAttr(n + "." + attr)
                
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

                    if cmds.attributeQuery(attr, node=ass, exists=True):
                        t = cmds.getAttr(ass + "." + attr)
                        materialIdList.append( t )
                
                # Set Material ID
                cmds.addAttr(o, ln=attr, at="long", k=True)
                cmds.setAttr(o + '.' + attr, mostPopular(materialIdList))
                osn.append(o)
                
        if len(osn):
            cmds.select(osn, r=True)
        else:
            cmds.select(os, r=True)
        
        cleanUp.header("Seperate Meshes with Multi-Shaders")
        for m in msg:
            print m
        print "Done."
        
    @staticmethod
    def makeUnique(*args):
        cleanUp.header("Making Name Unique")
        os = cmds.ls(sl=True, l=True)
        if not len(os):
            print "Nothing Selected."
            return False
        
        cmds.select(hi=True)
        sel = cmds.ls(sl=True, l=True, type="mesh")
        
        pad = len(str(len(sel))) + 1
        c = 0
        for n in sel:
            tmp = cmds.listRelatives(n, p=True, f=True)[0]
            source = tmp
            name =  tmp.split("|")[-1]
            if '_id_' in name:
                name = re.sub('_id_[0-9]*$', '', name)
            target = name + "_id_" + str(c).zfill(pad)
            
            cmds.rename(source, target)
            c+=1

                    
        cmds.select(os, r=True)        
        
class sirlasset():
    def __init__(self):
        self.ftp = None
        self.contents = []
        self.gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
        
    def connect(self):
        self.ftp = ftplib.FTP("155.4.21.131")
        self.ftp.login("mascista", "these2020!")
        print self.ftp.getwelcome()

    def getRemoteDirectoryContents(self, directory):
        self.ftp.cwd("/From_Sirlancelot")
        try:
            self.ftp.cwd(directory)
        except:
            return False
        
        self.contents = []
        self.ftp.retrlines("MLSD", self.callback )
        return self.contents
        
    def callback(self, result):
        self.contents.append(  self.content(result) )
        
    def transferCallback(self, result):
        print result
        
    def content(self, result):
        data = {}
        pairs = result.split(";")
        for pair in pairs:
            if '=' in pair:
                varval = pair.split('=')
                data[varval[0]] = varval[1]
            else:
                data["name"] = pair.strip()
        return data
    
    def getLocalFileStats(self, filename):
        data = {}
        data["modify"] = datetime.datetime.fromtimestamp( int( os.path.getmtime(filename)) ).strftime('%Y%m%d%H%M%S')
        data["size"] = int(os.path.getsize(filename))
        data["basename"] = filename.split("/")[-1]
        data["path"] = filename.replace(data["basename"], "")
        data["relativePath"] = '/'.join( filename.split("/")[-3:-1] )
        data["filename"] = filename
        
        return data
        
    def matchContents(self, contents, basename):
        if basename in [d["name"] for d in contents]:
            for content in contents:
                if basename == content["name"]:
                    return content
        else:
            return False
            
    @staticmethod    
    def update():
        # get references
        references = cmds.file(q=True, r=True)
        
        if len(references):
            asset = sirlasset()
            asset.connect()
            
        for ref in references:
            node = cmds.referenceQuery(ref, referenceNode=True)
            namespace = node[:-2]
            filename = cmds.referenceQuery(node, filename=True, unresolvedName=True)
            filedata = asset.getLocalFileStats(filename)
            
            # get remote file
            remotePath = "Batman/--assets--/" + filedata["relativePath"]
            contents = asset.getRemoteDirectoryContents(remotePath)
            if contents is False:
                continue
                
            content = asset.matchContents(contents, filedata["basename"])
            if content is False:
                print '%s not found on ftp.'%namespace
                continue

            # validate update
            size = (int(content["size"]) == int(filedata["size"]))
            date = (int(content["modify"]) < int(filedata["modify"]))

            '''
            print 'Size:'+str(size)
            print 'Date:'+str(date)
            '''
            
            if size and date:                
                print '%s is up to date.'%namespace
                continue

            # update
            currentDirectory = os.getcwd()
            os.chdir( filedata["path"] )
            
            cmds.progressBar( asset.gMainProgressBar, edit=True, beginProgress=True, isInterruptable=True, status='Downloading %s'%node[:-2], maxValue=int(content["size"]) )
            with open(filedata["filename"], 'wb') as f:
                def callback(data):
                    f.write(data)
                    cmds.progressBar(asset.gMainProgressBar, edit=True, step=1)
                    
                asset.ftp.retrbinary('RETR %s'%filedata["basename"], callback)
            cmds.progressBar(asset.gMainProgressBar, edit=True, endProgress=True)
            
            print '#################'
            print '%s is downloaded.'%namespace
            
            # reload reference
            cmds.file(filename, loadReference=node)                    
            os.chdir(currentDirectory)
            
            print '%s is updated.'%namespace
            print '#################\n\n'
            
        if len(references):
            asset.quit()

        print "Finished checking for rig updates.",
            
    def quit(self):
        self.ftp.quit()
