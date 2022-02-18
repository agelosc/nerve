import maya.cmds as cmds
import glob
import nerve
import os
import json


def autoExport(shots):
    for shot in shots.keys():
        path = 'R:/jobs/WiseMonkeys/Nounou/BillyDux/maya/scenes/layout/'
        files = glob.glob(path + '/BillyDux_Layoyt_shot_'+shot+'*.mb')
        mayaFile = sorted(files)[-1]
        
        cmds.file(mayaFile, open=True, f=True)
        import hub.utils.asset
        hub.utils.asset.checkVersions()
        
        ui = nerve.maya.alembic.ui()
        for asset in shots[shot]:
            cmds.textScrollList(ui.ctrl["assets"], e=True, selectItem=asset)
        ui.doIt()


class ui:
    def __init__(self):
        self.ctrl = {}
        self.name = "Alembic"
        self.title = "Make Alembics"
        
        self.sequences = []
        self.shots = []
        
        frameWidth = 300
        scrollListWidth = frameWidth-23
        buttonWidth = (frameWidth-5)/2
        buttonHeight = 40
        
        if cmds.window(self.name, q=True, exists=True):
            cmds.deleteUI(self.name)
            
        self.window = cmds.window(self.name, width=frameWidth, title=self.title, menuBar=False, iconName=self.name, sizeable=False, toolbox=False, maximizeButton=False)
        self.ctrl["parent"] = cmds.columnLayout()
        # Sequence
        if True:
            cmds.frameLayout(label="Sequence/Shot", collapsable=False, width=frameWidth )
            cmds.columnLayout(numberOfChildren=3)
            if True:
                self.ctrl["seq"] = cmds.optionMenuGrp(label="Sequence", columnWidth=[1,75])
                
                ## POPULATE SEQ
                path = cmds.workspace(q=True, rootDirectory=True).replace("maya/", '') + 'config'
                seqfiles = glob.glob(path + '/seq_*.json')
                for seqfile in seqfiles:        
                    name = seqfile.split('seq_')[-1].replace('.json', '')
                    cmds.menuItem(label=name)
                    data = json.load( open( seqfile ) )
                    self.sequences.append( data["shots"] )
                    
                self.ctrl["shot"] = cmds.optionMenuGrp(label="Shot", columnWidth=[1,75])
                
                ## POPULATE SHOTS
                self.populateShots()
            cmds.setParent("..")
        cmds.setParent("..")
        
        # CAMERA
        if True:
            
            cmds.frameLayout(label="Camera", collapsable=False, width=frameWidth )
            if False:
                self.ctrl["cam"] = cmds.optionMenuGrp(label="Camera", columnWidth=[1,75])
                # POPULATE CAM
                cmds.menuItem(label="None", parent=self.ctrl["cam"] + '|OptionMenu')
                for cam in self.getCameras():
                    cmds.menuItem(label=cam, parent=self.ctrl["cam"] + '|OptionMenu')
                    #cmds.optionMenuGrp(self.ctrl["cam"], e=True, value=cam)
                
            if len(cmds.ls('*:RenderCam2D_grp')):
                # FIX REFERENCE PATH
                self.ctrl["2dcam"] = cmds.checkBoxGrp( numberOfCheckBoxes=1, label='Camera2D', columnWidth=[1,75], value1=True )
                
            cmds.setParent('..')
            
        if False:
            cmds.frameLayout(label="Assets", collapsable=False, width=frameWidth, height=200 )
            numrows = len(cmds.file(q=True, r=True))
            if numrows == 0:
                numrows = 1
            self.ctrl["assets"] = cmds.textScrollList(numberOfRows=numrows, allowMultiSelection=True, width=scrollListWidth)
            
            ## POPULATE ASSETS
            references = cmds.file(q=True, r=True)
            for ref in references:
                refNode = cmds.file(ref, q=True, rfn=True)
                if cmds.referenceQuery(refNode, isLoaded=True):
                    namespace = cmds.referenceQuery(refNode, namespace=True).split(":")[-1]
                    if 'RenderCam' in namespace:
                        continue
                    if 'CAMERA' in namespace:
                        continue
                    cmds.textScrollList(self.ctrl["assets"], edit=True, append=namespace)
            
            cmds.setParent("..")
        
        cmds.rowLayout(numberOfColumns=2)
        cmds.button(label="Exoport", width=buttonWidth, height=buttonHeight, command=self.doIt)
        cmds.button(label="Cancel", width=buttonWidth, height=buttonHeight, command=self.cancel)
        cmds.setParent('..')
        
        cmds.showWindow(self.window)
        
        cmds.window(self.window, e=True, width=frameWidth+2, resizeToFitChildren=True)

    def doIt(self, *args):
    
        if not cmds.pluginInfo('MayaExocortexAlembic', q=True, l=True):
            cmds.loadPlugin('MayaExocortexAlembic')
    
        def getObjects(namespace):
        
            sel = cmds.ls(namespace + ':*', type="transform", l=True)[0]
            
            # Find Root
            c = 0
            for n in sel.split('|'):
                if namespace in n:
                    root = '|'.join( sel.split('|')[:c+1] )
                    break
                c = c+1
                
            #root = '|' + sel.split("|")[1]
            #print root
            
            objlist = []
            children = cmds.listRelatives(root, ad=True, ni=True, f=True, type="mesh")
            for c in children:
                getParent = cmds.listRelatives(c, p=True, ni=True, f=True)[0]
                if 'geo_grp' in getParent or '_Mesh_Top_grp' in getParent:
                    if getParent not in objlist:
                        objlist.append(getParent)
            return objlist    
            
        # Sequence
        sel = cmds.optionMenuGrp(self.ctrl["seq"], q=True, select=True)
        seqName = cmds.optionMenuGrp(self.ctrl["seq"], q=True, value=True)
        seq = self.sequences[sel-1]
        
        # Shot
        sel = cmds.optionMenuGrp(self.ctrl["shot"], q=True, select=True)
        if sel == 1:
            cmds.error('Shot not selected')
        
        shotName = cmds.optionMenuGrp(self.ctrl["shot"], q=True, value=True)
        shot = self.shots[sel-2]
        
        # Camera
        if False:
            selCamIdx = cmds.optionMenuGrp(self.ctrl["cam"], q=True, select=True)
            if selCamIdx == 1:
                cam = None
            else:
                cam = cmds.optionMenuGrp(self.ctrl["cam"], q=True, value=True)
            
            # Assets
            assets = cmds.textScrollList(self.ctrl["assets"], q=True, selectItem=True)
            if assets is None:
                assets = []
            
        # PATH
        path = cmds.workspace(q=True, rootDirectory=True).replace("maya/", 'elements/3D/ABC/%s/%s/'%(seqName, 'S'+str(shot["order"]).zfill(3)))
        if not os.path.exists(path):
            os.makedirs(path)
            
        def isFileInUse(filename):
            if os.path.exists(filename):
                try:
                    os.rename(filename, filename)
                except OSError as e:
                    msg = 'File is being used: "' + filename + '"! \n' + str(e)
                    cmds.error(msg)
                    return True
                    
            return False
            
        def ExportCamera(filename, object):
            if isFileInUse(filename):
                return False
                
            # Camera Arguments
            args = []
            args.append( 'filename=%s'%filename )
            args.append( 'objects=%s'%object )
            args.append( 'in=%s'%str(shot["startFrame"]) )
            args.append( 'out=%s'%str(shot["endFrame"]) )
            args.append( 'uvs=0;ogawa=1;step=1;purepointcache=0' )
            args.append( 'dynamictopology=0;normals=1;facesets=0;globalspace=0;withouthierarchy=0;transformcache=0' )        
            command = ';'.join(args)
            
            cmds.ExocortexAlembic_export(j=[command])

        def ExportObjects(filename, objList):
            if isFileInUse(filename):
                return False
                
            cmds.select(objList, r=True)
            objects = ','.join( objList )
            
            args = []
            args.append( 'filename=%s'%filename )
            args.append( 'in=%s'%str(shot["startFrame"]) )
            args.append( 'out=%s'%str(shot["endFrame"]) )
            args.append( 'uvs=1;ogawa=0;step=1;purepointcache=0' )
            args.append( 'objects=%s'%objects )
            args.append( 'dynamictopology=1;normals=1;facesets=1' )
            
            command = ';'.join(args)
            cmds.ExocortexAlembic_export(j=[command])
            
        # Cache 2D Camera
        if cmds.checkBoxGrp(self.ctrl["2dcam"], q=True, value1=True):
            print "Exportting Camera ANIM..."
            ExportCamera(path + '/camera_ANIM.abc', cmds.ls('*:Camera_ANIMATION', l=True)[0])    
            print "Exporting Camera STATIC..."
            ExportCamera(path + '/camera_STATIC.abc', cmds.ls('*:Camera_STATIC', l=True)[0])
            print "Exporting Objects for Houdini..."
            ExportObjects(path + '/mayaToHou.abc', cmds.ls('*:mayaToHou*', type="transform"))
            
            
            print "Baking AE Camera..."
            aecam = cmds.ls('*:Camera_toAE', l=True)[0]
            dup = cmds.duplicate(aecam, rr=True)[0]
            for i in range(shot['startFrame'], shot['endFrame']+1):
                cmds.currentTime(i, u=False)
                attribs = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']
                for attr in attribs:
                    val = cmds.getAttr(aecam+'.'+attr, t=i)
                    cmds.setKeyframe(dup, v=val, at=attr)
                    
            cmds.select(dup, r=True)
            cmds.parent(dup, w=True)
            sel = cmds.ls(sl=True, l=True)
            attribs = ['sx', 'sy', 'sz', 'v']
            for attr in attribs:
                cmds.setAttr(sel[0] + '.' + attr, 1)
                
            print "Exporting Camera AE..."
            cmds.currentTime(shot["startFrame"], u=True)            
            filename = path + '/cameraToAE.ma'    
            cmds.file(filename, exportSelected=True, type='mayaAscii', f=True)
            cmds.delete(dup)
        
        #return False
            
            
        # Cache Camera
        if cam is not None:
            object = cmds.listRelatives(cmds.ls(cam, l=True)[0], parent=True, f=True)[0]
            filename = path + '/camera.abc'
            ExportCamera(filename, object)
        
        # Cache Assets
        for asset in assets:
            filename = path + '/' + asset + '.abc'
            datafile = path + '/' + asset + '.json'
            
            # Check if file is being used:
            if os.path.exists(filename):
                try:
                    os.rename(filename, filename)
                except OSError as e:
                    msg = 'Access-error on file "' + filename + '"! \n' + str(e)
                    cmds.error(msg)
                    return False            
            
            objList = getObjects(asset)
            cmds.select(objList, r=True)
            
            # get and write color & texture data
            data = colorAndTexture()
            with open(datafile, 'w') as df:
                json.dump(data, df)
            
            objects = ','.join( objList )
            
            args = []
            args.append( 'filename=%s'%filename )
            args.append( 'in=%s'%str(shot["startFrame"]) )
            args.append( 'out=%s'%str(shot["endFrame"]) )
            args.append( 'uvs=1;ogawa=0;step=1;purepointcache=0' )
            args.append( 'objects=%s'%objects )
            args.append( 'dynamictopology=1;normals=1;facesets=1' )
            
            command = ';'.join(args)
            print command
            cmds.ExocortexAlembic_export(j=[command])    


        #self.cancel()
        cmds.deleteUI(self.window)
        
        
    def cancel(self, *args):
        cmds.deleteUI(self.window)
        
    def populateShots(self, *args):
        items = cmds.optionMenuGrp(self.ctrl["shot"], q=True, itemListLong=True)
        if items is None:
            items = []
        for item in items:
            cmds.deleteUI(item)
            
        sf = cmds.playbackOptions(q=True, min=True)
        ef = cmds.playbackOptions(q=True, max=True)
        
        sel = cmds.optionMenuGrp(self.ctrl["seq"], q=True, select=True)
        seq = self.sequences[sel-1]
        
        cmds.menuItem(label="None", parent=self.ctrl["shot"] + "|OptionMenu")
        
        c = 2
        idx = None
        for shot in seq:
            self.shots.append(shot)
            
            label = 'S%s - [%s - %s]'%(str(shot["order"]).ljust(4), str(shot["startFrame"]), str(shot["endFrame"]))
            cmds.menuItem(label=label, parent=self.ctrl["shot"] + "|OptionMenu")
            if sf == shot["startFrame"] and ef == shot["endFrame"]:
                idx = c
            c = c + 1
            
        if idx is not None:
            cmds.optionMenuGrp(self.ctrl["shot"], e=True, select=idx)
    
    def getCameras(self):
        camlist = cmds.ls(type="camera")
        camlist.remove('frontShape')
        camlist.remove('perspShape')
        camlist.remove('sideShape')
        camlist.remove('topShape')
        
        return camlist
            
def colorAndTexture():
    data = {}
    
    sel = cmds.ls(sl=True, l=True)
    cmds.select(hi=True)
    shapes = cmds.ls(sl=True, type="mesh")
    cmds.select(sel, r=True)
    
    for shape in shapes:
        shadingEngines = cmds.listConnections(shape, type="shadingEngine")
        if shadingEngines is None:
            continue
        for shadingEngine in shadingEngines:
            if shadingEngine is None:
                continue
            data[shadingEngine] = {}
            if cmds.listConnections(shadingEngine + ".surfaceShader") is None:
                continue 
            shader = cmds.listConnections(shadingEngine + ".surfaceShader")[0]
            
            
            shaderTypes = { 'lambert':'color', 'surfaceShader':'outColor', 'rampShader':'color[0].color_Color', 'phong':'color' }
            shaderType = cmds.nodeType(shader)
            if shaderType in shaderTypes.keys():
                conn = cmds.listConnections(shader + "." + shaderTypes[shaderType], s=True, d=False)
                if conn is None:
                    color = cmds.getAttr(shader + "." + shaderTypes[shaderType])
                    data[shadingEngine]["color"] = color[0]
                else:
                    color = cmds.getAttr(conn[0] + ".defaultColor")
                    data[shadingEngine]["color"] = color[0]
                    
                    tex = cmds.getAttr(conn[0] + ".fileTextureName")
                    data[shadingEngine]["texture"] = tex
            else:
                print 'Shader Type "%s" not in list'%shaderType
                
    return data
            
        
        

class uiOLD:
    def __init__(self):
        self.ctrl = {}
        self.name = "Alembic"
        self.title = "Make Alembics"
        
        self.sequences = []
        self.shots = []
        
        frameWidth = 400
        scrollListWidth = frameWidth-23
        buttonWidth = (frameWidth-5)/2
        buttonHeight = 40
        
        if cmds.window(self.name, q=True, exists=True):
            cmds.deleteUI(self.name)
            
        self.window = cmds.window(self.name, width=frameWidth, title=self.title, menuBar=False, iconName=self.name, sizeable=False, toolbox=False, maximizeButton=False)
        self.ctrl["parent"] = cmds.columnLayout()
        if True:
            cmds.frameLayout(label="Sequence/Shot", collapsable=False, width=frameWidth )
            cmds.columnLayout(numberOfChildren=3)
            if True:
                self.ctrl["seq"] = cmds.optionMenuGrp(label="Sequence", columnWidth=[1,75])
                
                ## POPULATE SEQ
                path = cmds.workspace(q=True, rootDirectory=True).replace("maya/", '') + 'config'
                seqfiles = glob.glob(path + '/seq_*.json')
                for seqfile in seqfiles:        
                    name = seqfile.split('seq_')[-1].replace('.json', '')
                    cmds.menuItem(label=name)
                    data = json.load( open( seqfile ) )
                    self.sequences.append( data["shots"] )
                    
                self.ctrl["shot"] = cmds.optionMenuGrp(label="Shot", columnWidth=[1,75])
                
                ## POPULATE SHOTS
                self.populateShots()
            cmds.setParent("..")
        cmds.setParent("..")
        
        # CAMERA
        if True:
            cmds.frameLayout(label="Camera", collapsable=False, width=frameWidth )
            self.ctrl["cam"] = cmds.optionMenuGrp(label="Camera", columnWidth=[1,75])
            # POPULATE CAM
            cmds.menuItem(label="None", parent=self.ctrl["cam"] + '|OptionMenu')
            for cam in self.getCameras():
                cmds.menuItem(label=cam, parent=self.ctrl["cam"] + '|OptionMenu')
                #cmds.optionMenuGrp(self.ctrl["cam"], e=True, value=cam)
                
            if len(cmds.ls('*:RenderCam2D_grp')):
                # FIX REFERENCE PATH
                self.ctrl["2dcam"] = cmds.checkBoxGrp( numberOfCheckBoxes=1, label='Camera2D', columnWidth=[1,75], value1=True )
                
            
        cmds.setParent('..')
        if True:
            cmds.frameLayout(label="Assets", collapsable=False, width=frameWidth, height=200 )
            numrows = len(cmds.file(q=True, r=True))
            if numrows == 0:
                numrows = 1
            self.ctrl["assets"] = cmds.textScrollList(numberOfRows=numrows, allowMultiSelection=True, width=scrollListWidth)
            
            ## POPULATE ASSETS
            references = cmds.file(q=True, r=True)
            for ref in references:
                refNode = cmds.file(ref, q=True, rfn=True)
                if cmds.referenceQuery(refNode, isLoaded=True):
                    namespace = cmds.referenceQuery(refNode, namespace=True).split(":")[-1]
                    if 'RenderCam' in namespace:
                        continue
                    if 'CAMERA' in namespace:
                        continue
                    cmds.textScrollList(self.ctrl["assets"], edit=True, append=namespace)
            
        cmds.setParent("..")
        
        cmds.rowLayout(numberOfColumns=2)
        cmds.button(label="Exoport", width=buttonWidth, height=buttonHeight, command=self.doIt)
        cmds.button(label="Cancel", width=buttonWidth, height=buttonHeight, command=self.cancel)
        cmds.setParent('..')
        
        cmds.showWindow(self.window)
        
        cmds.window(self.window, e=True, width=frameWidth+2, resizeToFitChildren=True)

    def doIt(self, *args):
    
        if not cmds.pluginInfo('MayaExocortexAlembic', q=True, l=True):
            cmds.loadPlugin('MayaExocortexAlembic')
    
        def getObjects(namespace):
        
            sel = cmds.ls(namespace + ':*', type="transform", l=True)[0]
            
            # Find Root
            c = 0
            for n in sel.split('|'):
                if namespace in n:
                    root = '|'.join( sel.split('|')[:c+1] )
                    break
                c = c+1
                
            #root = '|' + sel.split("|")[1]
            #print root
            
            objlist = []
            children = cmds.listRelatives(root, ad=True, ni=True, f=True, type="mesh")
            for c in children:
                getParent = cmds.listRelatives(c, p=True, ni=True, f=True)[0]
                if 'geo_grp' in getParent or '_Mesh_Top_grp' in getParent:
                    if getParent not in objlist:
                        objlist.append(getParent)
            return objlist    
            
        # Sequence
        sel = cmds.optionMenuGrp(self.ctrl["seq"], q=True, select=True)
        seqName = cmds.optionMenuGrp(self.ctrl["seq"], q=True, value=True)
        seq = self.sequences[sel-1]
        
        # Shot
        sel = cmds.optionMenuGrp(self.ctrl["shot"], q=True, select=True)
        if sel == 1:
            cmds.error('Shot not selected')
        
        shotName = cmds.optionMenuGrp(self.ctrl["shot"], q=True, value=True)
        shot = self.shots[sel-2]
        
        # Camera
        selCamIdx = cmds.optionMenuGrp(self.ctrl["cam"], q=True, select=True)
        if selCamIdx == 1:
            cam = None
        else:
            cam = cmds.optionMenuGrp(self.ctrl["cam"], q=True, value=True)
            
        # Assets
        assets = cmds.textScrollList(self.ctrl["assets"], q=True, selectItem=True)
        if assets is None:
            assets = []
            
        # PATH
        path = cmds.workspace(q=True, rootDirectory=True).replace("maya/", 'elements/3D/ABC/%s/%s/'%(seqName, 'S'+str(shot["order"]).zfill(3)))
        if not os.path.exists(path):
            os.makedirs(path)
            
        def isFileInUse(filename):
            if os.path.exists(filename):
                try:
                    os.rename(filename, filename)
                except OSError as e:
                    msg = 'File is being used: "' + filename + '"! \n' + str(e)
                    cmds.error(msg)
                    return True
                    
            return False
            
        def ExportCamera(filename, object):
            if isFileInUse(filename):
                return False
                
            # Camera Arguments
            args = []
            args.append( 'filename=%s'%filename )
            args.append( 'objects=%s'%object )
            args.append( 'in=%s'%str(shot["startFrame"]) )
            args.append( 'out=%s'%str(shot["endFrame"]) )
            args.append( 'uvs=0;ogawa=1;step=1;purepointcache=0' )
            args.append( 'dynamictopology=0;normals=1;facesets=0;globalspace=0;withouthierarchy=0;transformcache=0' )        
            command = ';'.join(args)
            
            cmds.ExocortexAlembic_export(j=[command])

        def ExportObjects(filename, objList):
            if isFileInUse(filename):
                return False
                
            cmds.select(objList, r=True)
            objects = ','.join( objList )
            
            args = []
            args.append( 'filename=%s'%filename )
            args.append( 'in=%s'%str(shot["startFrame"]) )
            args.append( 'out=%s'%str(shot["endFrame"]) )
            args.append( 'uvs=1;ogawa=0;step=1;purepointcache=0' )
            args.append( 'objects=%s'%objects )
            args.append( 'dynamictopology=1;normals=1;facesets=1' )
            
            command = ';'.join(args)
            cmds.ExocortexAlembic_export(j=[command])
            
        # Cache 2D Camera
        if cmds.checkBoxGrp(self.ctrl["2dcam"], q=True, value1=True):
            print "Exportting Camera ANIM..."
            ExportCamera(path + '/camera_ANIM.abc', cmds.ls('*:Camera_ANIMATION', l=True)[0])    
            print "Exporting Camera STATIC..."
            ExportCamera(path + '/camera_STATIC.abc', cmds.ls('*:Camera_STATIC', l=True)[0])
            print "Exporting Objects for Houdini..."
            ExportObjects(path + '/mayaToHou.abc', cmds.ls('*:mayaToHou*', type="transform"))
            
            
            print "Baking AE Camera..."
            aecam = cmds.ls('*:Camera_toAE', l=True)[0]
            dup = cmds.duplicate(aecam, rr=True)[0]
            for i in range(shot['startFrame'], shot['endFrame']+1):
                cmds.currentTime(i, u=False)
                attribs = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']
                for attr in attribs:
                    val = cmds.getAttr(aecam+'.'+attr, t=i)
                    cmds.setKeyframe(dup, v=val, at=attr)
                    
            cmds.select(dup, r=True)
            cmds.parent(dup, w=True)
            sel = cmds.ls(sl=True, l=True)
            attribs = ['sx', 'sy', 'sz', 'v']
            for attr in attribs:
                cmds.setAttr(sel[0] + '.' + attr, 1)
                
            print "Exporting Camera AE..."
            cmds.currentTime(shot["startFrame"], u=True)            
            filename = path + '/cameraToAE.ma'    
            cmds.file(filename, exportSelected=True, type='mayaAscii', f=True)
            cmds.delete(dup)
        
        #return False
            
            
        # Cache Camera
        if cam is not None:
            object = cmds.listRelatives(cmds.ls(cam, l=True)[0], parent=True, f=True)[0]
            filename = path + '/camera.abc'
            ExportCamera(filename, object)
        
        # Cache Assets
        for asset in assets:
            filename = path + '/' + asset + '.abc'
            datafile = path + '/' + asset + '.json'
            
            # Check if file is being used:
            if os.path.exists(filename):
                try:
                    os.rename(filename, filename)
                except OSError as e:
                    msg = 'Access-error on file "' + filename + '"! \n' + str(e)
                    cmds.error(msg)
                    return False            
            
            objList = getObjects(asset)
            cmds.select(objList, r=True)
            
            # get and write color & texture data
            data = colorAndTexture()
            with open(datafile, 'w') as df:
                json.dump(data, df)
            
            objects = ','.join( objList )
            
            args = []
            args.append( 'filename=%s'%filename )
            args.append( 'in=%s'%str(shot["startFrame"]) )
            args.append( 'out=%s'%str(shot["endFrame"]) )
            args.append( 'uvs=1;ogawa=0;step=1;purepointcache=0' )
            args.append( 'objects=%s'%objects )
            args.append( 'dynamictopology=1;normals=1;facesets=1' )
            
            command = ';'.join(args)
            print command
            cmds.ExocortexAlembic_export(j=[command])    


        #self.cancel()
        cmds.deleteUI(self.window)
        
        
    def cancel(self, *args):
        cmds.deleteUI(self.window)
        
    def populateShots(self, *args):
        items = cmds.optionMenuGrp(self.ctrl["shot"], q=True, itemListLong=True)
        if items is None:
            items = []
        for item in items:
            cmds.deleteUI(item)
            
        sf = cmds.playbackOptions(q=True, min=True)
        ef = cmds.playbackOptions(q=True, max=True)
        
        sel = cmds.optionMenuGrp(self.ctrl["seq"], q=True, select=True)
        seq = self.sequences[sel-1]
        
        cmds.menuItem(label="None", parent=self.ctrl["shot"] + "|OptionMenu")
        
        c = 2
        idx = None
        for shot in seq:
            self.shots.append(shot)
            
            label = 'S%s - [%s - %s]'%(str(shot["order"]).ljust(4), str(shot["startFrame"]), str(shot["endFrame"]))
            cmds.menuItem(label=label, parent=self.ctrl["shot"] + "|OptionMenu")
            if sf == shot["startFrame"] and ef == shot["endFrame"]:
                idx = c
            c = c + 1
            
        if idx is not None:
            cmds.optionMenuGrp(self.ctrl["shot"], e=True, select=idx)
    
    def getCameras(self):
        camlist = cmds.ls(type="camera")
        camlist.remove('frontShape')
        camlist.remove('perspShape')
        camlist.remove('sideShape')
        camlist.remove('topShape')
        
        return camlist
            
def colorAndTexture():
    data = {}
    
    sel = cmds.ls(sl=True, l=True)
    cmds.select(hi=True)
    shapes = cmds.ls(sl=True, type="mesh")
    cmds.select(sel, r=True)
    
    for shape in shapes:
        shadingEngines = cmds.listConnections(shape, type="shadingEngine")
        if shadingEngines is None:
            continue
        for shadingEngine in shadingEngines:
            if shadingEngine is None:
                continue
            data[shadingEngine] = {}
            if cmds.listConnections(shadingEngine + ".surfaceShader") is None:
                continue 
            shader = cmds.listConnections(shadingEngine + ".surfaceShader")[0]
            
            
            shaderTypes = { 'lambert':'color', 'surfaceShader':'outColor', 'rampShader':'color[0].color_Color', 'phong':'color' }
            shaderType = cmds.nodeType(shader)
            if shaderType in shaderTypes.keys():
                conn = cmds.listConnections(shader + "." + shaderTypes[shaderType], s=True, d=False)
                if conn is None:
                    color = cmds.getAttr(shader + "." + shaderTypes[shaderType])
                    data[shadingEngine]["color"] = color[0]
                else:
                    color = cmds.getAttr(conn[0] + ".defaultColor")
                    data[shadingEngine]["color"] = color[0]
                    
                    tex = cmds.getAttr(conn[0] + ".fileTextureName")
                    data[shadingEngine]["texture"] = tex
            else:
                print 'Shader Type "%s" not in list'%shaderType
                
    return data
            
        