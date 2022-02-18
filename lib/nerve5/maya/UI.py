# Maya
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as mu

# Nerve
import nerve5 as nerve
from nerve5.maya import getToolPaths
import nerve5.maya.utils
import nerve5.maya.modeling
import nerve5.maya.animation
import nerve5.maya.rigging
import nerve5.maya.rendering
import nerve5.maya.asset
import nerve5.maya.matchmoving
import nerve5.maya.fx

# Other
from functools import partial
import glob
import os
import sys
import json
import collections

def seperator(parent):
    cmds.menuItem(divider=True, parent=parent)

def test():
    print "OK"


class menu():
    def __init__(self):
        self.ctrl = {}
        self.name = "Nerve5"

        if ( cmds.menu(self.name, exists=True) ):
            cmds.deleteUI(self.name)

        gMainWindow = mel.eval('$temp1=$gMainWindow;')
        self.ctrl["mainMenu"] = cmds.menu(self.name, parent=gMainWindow, tearOff=True, label=self.name)

        # JOBS
        self.ctrl["jobs"] = cmds.menuItem(subMenu=True, label="Jobs", tearOff=True)
        if True:
            # Recent

            self.ctrl["recent"] = cmds.menuItem(subMenu=True, label="Recent", tearOff=True)
            cmds.menuItem(self.ctrl["recent"], edit=True, postMenuCommand=partial(self._addRecentJobMenu, self.ctrl["recent"]) )
            seperator( self.ctrl["jobs"] )
            # Job list
            cmds.menuItem(self.ctrl["jobs"], edit=True, parent=self.ctrl["mainMenu"], postMenuCommand=partial(self._addJobMenu, nerve.cfg.path("job"), 1, self.ctrl["jobs"]),  postMenuCommandOnce=True)

        cmds.menuItem(subMenu=False, label="Explore", parent=self.ctrl["mainMenu"], command=self._explore)
        seperator( self.ctrl["mainMenu"] )

        # Sequences
        self.ctrl["seq"] = cmds.menuItem(subMenu=True, label="Sequences", tearOff=True, parent=self.ctrl["mainMenu"])
        cmds.menuItem( self.ctrl["seq"], edit=True, postMenuCommand=partial(self._seqMenu, self.ctrl["seq"]), postMenuCommandOnce=False)

        # Tools
        self.jobToolsMenu()
        seperator( self.ctrl["mainMenu"] )

        # Utilities
        self._addModMenu( "Utilities", nerve.maya.utils.UI(), self.ctrl["mainMenu"] )
        self._addModMenu( "Modeling", nerve.maya.modeling.UI(), self.ctrl["mainMenu"] )
        self._addModMenu( "Animation", nerve.maya.animation.UI(), self.ctrl["mainMenu"] )
        self._addModMenu( "Rigging", nerve.maya.rigging.UI(), self.ctrl["mainMenu"] )
        self._addModMenu( "Matchmoving", nerve.maya.matchmoving.UI(), self.ctrl["mainMenu"] )
        self._addModMenu( "Rendering", nerve.maya.rendering.UI(), self.ctrl["mainMenu"] )
        self._addModMenu( "FX", nerve.maya.fx.UI(), self.ctrl["mainMenu"] )

        seperator( self.ctrl["mainMenu"] )
        cmds.menuItem(subMenu=False, label="Gather..", parent=self.ctrl["mainMenu"], command=partial(self.assetManager, 'gather'))
        cmds.menuItem(subMenu=False, label="Release...", parent=self.ctrl["mainMenu"], command=partial(self.assetManager, 'release'))
        cmds.menuItem(subMenu=False, label="Check Versions..", parent=self.ctrl["mainMenu"], command=self.checkVersions)
        #seperator( self.ctrl["mainMenu"] )
        #cmds.menuItem(subMenu=False, label="Export Alembics..", parent=self.ctrl["mainMenu"], command=self.exportAlembics)

        seperator( self.ctrl["mainMenu"] )
        self.ctrl["submitToDeadline"] = cmds.menuItem(subMenu=False, label="Submit To Deadline", parent=self.ctrl["mainMenu"], command=self.submitToDeadline)

        seperator( self.ctrl["mainMenu"] )
        cmds.menuItem(subMenu=False, label="Reload Nerve", parent=self.ctrl["mainMenu"], command=self.reload)

    def exportAlembics(*args):
        import nerve.maya.alembic
        reload(nerve.maya.alembic)
        nerve.maya.alembic.ui()


    def submitToDeadline(self, *args):
        mel.eval('source "DeadlineMayaClient.mel"; DeadlineMayaClient(); SubmitJobToDeadline;')


    def assetManager(self, *args):
        assetManager( args[0] )

    def checkVersions(self, *args):
        nerve.maya.asset.checkVersions()

    def reload(self, *args):
        mel.eval('rehash')
        import nerve5.maya
        reload(nerve5.maya)
        reload(nerve5.maya.utils)
        reload(nerve5.maya.rigging)
        reload(nerve5.maya.rendering)
        reload(nerve5.maya.modeling)
        reload(nerve5.maya.asset)
        reload(nerve5.maya.animation)
        reload(nerve5.maya.UI)
        reload(nerve5.maya.matchmoving)
        reload(nerve5.maya.fx)

        print "Nerve Reloaded...",


    def _seqMenu(self, *args):
        ctrl = args[0]

        cmds.menu(ctrl, e=True, deleteAllItems=True)

        configPath = nerve.maya.configPath()
        seqs = nerve.sequence.list(configPath)
        for path in seqs:
            seq = nerve.sequence( path )
            seq.load()

            seqCtrl = cmds.menuItem( subMenu=True, tearOff=True, label=seq.name, parent=ctrl)

            # Shot Menu Items
            for shot in seq["shots"]:
                label = 'S%s: [%s - %s]'%(str(shot["order"]).zfill(2), str(str(shot["startFrame"])).zfill(4), str(shot["endFrame"]).zfill(4))
                if shot["desc"] != '':
                    label+= " %s"%(shot["desc"])

                shotCtrl = cmds.menuItem(label=label, parent=seqCtrl, command=partial(self.setFrameRange, shot["startFrame"], shot["endFrame"]))
                shotOptCtrl = cmds.menuItem(optionBox=True)
                cmds.menuItem( shotOptCtrl, e=True, command=partial(self._shotDialog, 'edit', seq, shot, seqCtrl, shotCtrl, shotOptCtrl) )


            # +/- 5 frames
            def plusMinus(*args):
                cmds.playbackOptions(min=cmds.playbackOptions(q=True, min=True)-5 )
                cmds.playbackOptions(max=cmds.playbackOptions(q=True, max=True)+5 )

            seperator( seqCtrl )
            self.ctrl['plusMinus'] = cmds.menuItem(subMenu=False, label='+/- 5 frames', parent=seqCtrl, command=plusMinus)

            # New Shot
            seperator( seqCtrl )
            shotCtrl = cmds.menuItem( subMenu=False, label='New...', parent=seqCtrl, command=partial( self._shotDialog, 'new', seq, None, None, None, None ))

        seperator( ctrl )
        self.ctrl["newSeq"] = cmds.menuItem(subMenu=False, label='New...', parent=ctrl, command=self._newSeq)

    def _shotDialog( self, *args):
        def _shotUI(*args):
            # UI Functions [begin]
            def cancel(*args):
                cmds.layoutDialog(dismiss="Cancel")
                print 'shot editing canceled...',

            def delete(*args):
                result = cmds.confirmDialog( title='Confirm', message='Are you sure you want to delete shot?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
                if result == 'Yes':
                    seq = args[1]
                    shot = args[2]
                    seq.data["shots"].remove(shot)
                    seq.save()
                    cmds.layoutDialog(dismiss='Cancel')

                    print 'shot was deleted...',

            def doIt(*args):
                ctrl = args[0]
                mode = args[1]
                seq = args[2]
                shot = args[3]
                seqCtrl = args[4]
                shotCtrl = args[5]
                shotOptCtrl = args[6]


                shot = {}
                shot["desc"] = cmds.textFieldGrp(ctrl["desc"], q=True, text=True)
                shot["startFrame"] = cmds.intFieldGrp(ctrl["frameRange"], q=True, value1=True)
                shot["endFrame"] = cmds.intFieldGrp(ctrl["frameRange"], q=True, value2=True)
                shot["order"] = cmds.intFieldGrp(ctrl["order"], q=True, value1=True)

                if args[1] == "edit":
                    seq["shots"].remove(args[3])

                for s in seq["shots"]:
                    if int(shot["order"]) == int(s["order"]):
                        seq["shots"].remove( s )

                seq.data["shots"].append( shot )
                seq.save()
                cmds.layoutDialog(dismiss="OK")

                if args[1] == 'edit':
                    print 'Shot edited...',
                else:
                    print 'Shot created...',


                # Update seq menu
                label = 'S%s: [%s - %s]'%(str(shot["order"]).zfill(2), str(str(shot["startFrame"])).zfill(4), str(shot["endFrame"]).zfill(4))
                if shot["desc"] != '':
                    label+= " %s"%(shot["desc"])

                if mode != 'new':
                    cmds.menuItem(shotCtrl, e=True, label=label, command=partial( self.setFrameRange, shot["startFrame"], shot["endFrame"] ))
                    cmds.menuItem(shotOptCtrl, e=True, command=partial( self._shotDialog, 'edit', seq, shot, seqCtrl, shotCtrl, shotOptCtrl ))

            # UI Functions [end]

            mode = args[0]

            # Shot Values
            val = {}
            if mode == 'new':
                seq = args[1]

                if len(seq["shots"]):
                    val["order"] = int( seq["shots"][-1]["order"]) + 10
                else:
                    val["order"] = 10
                val["startFrame"] = cmds.playbackOptions(q=True, min=True)
                val["endFrame"] = cmds.playbackOptions(q=True, max=True)
                val["desc"] = ''

            elif mode == 'edit':
                seq = args[1]
                shot = args[2]
                for key in shot.keys():
                    val[key] = shot[key]

            # UI
            form = cmds.setParent(q=True)
            cmds.formLayout(form, e=True, width=400)

            if mode == 'edit':
                menuBarLayout = cmds.menuBarLayout()
                cmds.menu(label='Edit')
                cmds.separator(height=2, style='in')
                cmds.menuItem(label="Delete", command=partial(delete, *args))

            cmds.columnLayout()
            ctrl = {}
            ctrl["order"] = cmds.intFieldGrp( numberOfFields=1, label='Order',value1=int(val["order"]))
            ctrl["frameRange"] = cmds.intFieldGrp( numberOfFields=2, label='Frame Range',value1=int(val["startFrame"]), value2=int(val["endFrame"]))
            ctrl["desc"] = cmds.textFieldGrp( label='Description', text=val["desc"] )

            cmds.rowLayout(numberOfColumns=2)
            b1 = cmds.button( label='OK', height=30, width=199, command=partial(doIt, ctrl, *args))
            b2 = cmds.button( label='Cancel', height=30, width=199, command=cancel)

        # Shot Dialog
        cmds.layoutDialog( ui=partial( _shotUI, *args ) )



    def _newSeq(self, *args):
        result = cmds.promptDialog(title='New Sequence',message='Enter Sequence Name:', button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel')
        if result == 'OK':
            text = cmds.promptDialog(query=True, text=True)

            # Illegal Characters
            if nerve.illegalChars(text):
                cmds.confirmDialog( title='Error', message='Sequence Name contains illegal characters', button=['OK'], defaultButton='OK')
                nerve.error("Illegal Characters")
                return False

            # Name
            name = text.replace(" ", "_")
            path = nerve.maya.configPath()
            if not os.path.exists(path):
                os.mkdir(path)

            # Exists
            seqs = nerve.sequence.list( nerve.maya.configPath() )
            for s in seqs:
                if nerve.sequence.basename( s ) == name:
                    nerve.error('Sequence '+name+' already exists, try a different name')
                    return False

            file = nerve.maya.configPath() + '/seq_' + name + '.json'
            seq = nerve.sequence( file )
            seq.save()
            print 'New Sequence "' + seq.name + '" created...',

    def _addModMenu(self, name, uidata, parent):

        def getParent(data):
            if 'parent' in data.keys():
                return self.ctrl[data["parent"]]
            else:
                return self.ctrl[name]

        def getCtrl(data):
            if 'ctrl' in data.keys():
                return data['ctrl']
            else:
                return data["label"].strip()

        self.ctrl[name] = cmds.menuItem(subMenu=True, tearOff=True, label=name, parent=parent)

        for data in uidata:
            if 'type' in data.keys() and data["type"] == 'seperator':
                seperator( getParent(data) )
            elif 'type' in data.keys() and data["type"] == 'submenu':
                self.ctrl[ getCtrl(data) ] = cmds.menuItem(subMenu=True, tearOff=True, label=data["label"], parent=getParent(data))
            else:
                self.ctrl[ getCtrl(data) ] = cmds.menuItem(subMenu=False, label=data["label"], parent=getParent(data), command=data["command"])


    def _addRecentJobMenu(self, *args):
        parent = args[0]

        recentFiles = cmds.optionVar(query='RecentFilesList')
        if recentFiles == 0:
            recentFiles = []

        for recentFile in recentFiles:
            if recentFile[:8] != nerve.cfg.path("job"):
                continue

            tmp = recentFile.split("/")

            def addMenuItem(name, parent, setJob=False, path=None):
                items = cmds.menu(parent, q=True, itemArray=True) or []
                names = []
                for item in items:
                    names.append(cmds.menuItem(item, q=True, label=True))

                if name in names:
                    for i in range(len(names)):
                        if name == names[i]:
                            return items[i]
                else:
                    if setJob:
                        ctrl = cmds.menuItem(subMenu=False, label=name, parent=parent)
                        cmds.menuItem(ctrl, edit=True, command=partial(self.setJob, path))
                    else:
                        return cmds.menuItem(subMenu=True, tearOff=True, label=name, parent=parent)

            ctrl = addMenuItem(tmp[2], parent)
            ctrl = addMenuItem(tmp[3], ctrl)
            ctrl = addMenuItem(tmp[4], ctrl, setJob=True, path="/".join(tmp[:5]) + "/maya")

    def _addJobMenu(self, *args):
        path = args[0]
        depth = args[1]
        parent = args[2]

        def sp(a):
            return a.split('\\')[-1].lower()

        files = sorted(glob.glob(path + "/*"), key=sp)

        #files = sorted(os.listdir(path))
        for f in files:
            if os.path.isdir(f):
                name = f.replace("\\", "/").replace("//", "/").split("/")[-1]
                if depth < 3:
                    ctrl = cmds.menuItem(subMenu=True, tearOff=True, label=name, parent=parent)
                    cmds.menuItem(ctrl, edit=True, pmc=partial(self._addJobMenu, path + "/" + name, depth+1, ctrl), pmo=True)
                else:
                    mayaPath = path + "/" + name + "/maya"
                    if os.path.exists(mayaPath + "/workspace.mel"):
                        ctrl = cmds.menuItem(subMenu=False, label=name, parent=parent)
                        cmds.menuItem(ctrl, edit=True, command=partial(self.setJob, mayaPath))


    def jobToolsMenu(self, *args):


        def addToolsMenuItem(path, parent):
            filenames = os.listdir(path)

            # Directory
            for filename in filenames:
                # Folder
                if os.path.isdir(path+'/'+filename):
                    subMenu = cmds.menuItem( subMenu=True, label=filename, parent=parent )
                    addToolsMenuItem(path+'/'+filename, subMenu)

            # UI Exists
            if 'uidata.py' in filenames:
                import importlib
                uidata = importlib.import_module('uidata')
                reload(uidata)

                for data in uidata.data:
                    if 'type' in data.keys() and data["type"] == 'seperator':
                        seperator( parent )
                    elif 'type' in data.keys() and data["type"] == 'submenu':
                        self.ctrl[ data['label'] ] = cmds.menuItem(subMenu=True, tearOff=True, label=data["label"], parent=parent)
                    else:
                        self.ctrl[ data['label'] ] = cmds.menuItem(subMenu=False, label=data["label"], parent=parent, command=partial(self.jobToolCmd, data['command']))
            # UI does not exist
            else:
                for filename in filenames:
                    # Scripts
                    if filename[-3:] == '.py':
                        name = filename[:-3]

                        cmds.menuItem( subMenu=False, label=nerve.uncamelCase( name.split('-')[-1] ), parent=parent, command=partial( self.jobToolCmd, name ) )

                    if filename[-4:] == '.sep':
                        cmds.menuItem(divider=True, parent=parent)
        # addToolsMenuyItem [END]

        # Clear Old Job Paths
        for syspath in sys.path:
            tmp = syspath.replace('\\','/')
            if tmp[:8] == 'R:/jobs/':
                sys.path.remove(syspath)

        # Update Job Tool Paths
        for path in getToolPaths(r=True):
            if path not in sys.path:
                sys.path.append( path )

        # Remove Menu Item
        if 'tools' in self.ctrl.keys() and self.ctrl['tools'] is not None:
            cmds.deleteUI( self.ctrl['tools'], mi=True )
            self.ctrl['tools'] = None

        # Create Empty Menu
        self.ctrl['tools'] = cmds.menuItem( subMenu=True, label='Tools', parent=self.ctrl['mainMenu'], insertAfter=self.ctrl["seq"], tearOff=True)

        # Get Paths for UI
        paths = getToolPaths()
        for path in paths:
            addToolsMenuItem(path, self.ctrl["tools"])

    def jobToolCmd(*args):
        import importlib

        if args[1] not in sys.modules:
            i = importlib.import_module( args[1] )
        else:
            reload( sys.modules[args[1]] )
        #return i

    def setJob(self, *args):
        cmds.workspace(args[0], openWorkspace=True)
        self.jobToolsMenu([])
        print "Project set to " + args[0]

    def setFrameRange(*args):
        cmds.playbackOptions(min=args[1])
        cmds.playbackOptions(max=args[2])

    def _explore(self, *args):
        path = cmds.workspace(query=True, rootDirectory=True)
        path = path.replace("/", "\\")
        os.system("start explorer " + path)


class assetManager():
    def __init__(self, mode="release"):
        self.ctrl = {}
        self.name = "NerveAssetManager"
        self.sel = {'mode':mode, 'ui':True}
        self.currentJob = nerve.maya.asset.resolveJob()

        if(cmds.window(self.name, exists=True)):
            cmds.deleteUI(self.name)

        self.width = 600
        self.height = 670
        self.margin = 10

        self.ctrl["window"] = cmds.window(self.name, title=self.name, menuBar=False, iconName=self.name, sizeable=False, toolbox=False, maximizeButton=False, resizeToFitChildren=True, width=self.width, height=self.height)

        # Menu
        cmds.menuBarLayout()
        m = cmds.menu(label="File")
        m2 = cmds.menuItem(label="Quit", command=self.quit)
        cmds.separator( height=1, style='in' )

        cmds.columnLayout()
        # JOB SELECT
        if "Job Select" and True:
            self.ctrl["jobSelectFrameLayout"] = self.frameLayout(label="Job Select", collapsable=False, height=215)

            width = (self.width - self.margin - 15)
            self.ctrl["jobSelectRowColumnLayout"] = cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1,width/3), (2, width/3), (3,width/3)])

            self.ctrl["jobSelectJob"] = self.textScrollList()
            self.ctrl["jobSelectSeq"] = self.textScrollList()
            self.ctrl["jobSelectShot"] = self.textScrollList()

            cmds.setParent('..')
            cmds.setParent('..')

        # INFO
        self.ctrl["assetFrameLayout"] = self.frameLayout(label="Asset Select", collapsable=False)

        self.ctrl["tabLayout"] = cmds.tabLayout(changeCommand=self.deselect)
        # GATHER
        if "Gather" and True:
            self.ctrl["gatherLayout"] = cmds.frameLayout(labelVisible=False)
            cmds.columnLayout()

            self.dataAndThumb()

            # Select
            if True:
                cmds.columnLayout()

                width = (self.width - self.margin - 25)
                self.ctrl["gatherSelectRowColumnLayout"] = cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 255), (2,255), (3,55)])

                self.ctrl["gatherType"] = self.textScrollList()
                self.ctrl["gatherName"] = self.textScrollList(deleteKeyCommand=self.group)
                self.ctrl["gatherVersion"] = self.textScrollList()

                cmds.setParent('..')
                cmds.setParent('..')

            cmds.button(height=50, label="Gather", command=self.gather, width=570)
            cmds.setParent('..')
            cmds.setParent('..')


        # RELEASE
        if "Release" and True:
            self.ctrl["releaseLayout"] = cmds.frameLayout(labelVisible=False)
            cmds.columnLayout()

            self.dataAndThumb(mode='release')

            # Select
            if True:
                #self.ctrl["release"] = cmds.columnLayout()

                width = (self.width - self.margin - 25)
                self.ctrl["releaseSelectRowColumnLayout"] = cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 255), (2,255), (3,55)])

                self.ctrl["releaseType"] = self.textScrollList()
                self.ctrl["releaseName"] = self.textScrollList(deleteKeyCommand=self.group)
                self.ctrl["releaseVersion"] = self.textScrollList()

                cmds.setParent('..')

            cmds.button(height=50, label="Release", command=self.release, width=570)

            cmds.setParent('..')
            cmds.setParent('..')

        cmds.tabLayout(self.ctrl["tabLayout"], edit=True, tabLabel=((self.ctrl["gatherLayout"], "Gather"), (self.ctrl["releaseLayout"], "Release")))
        if self.sel["mode"] == "gather":
            cmds.tabLayout(self.ctrl["tabLayout"], edit=True, selectTab=self.ctrl["gatherLayout"])
        else:
            cmds.tabLayout(self.ctrl["tabLayout"], edit=True, selectTab=self.ctrl["releaseLayout"])

        cmds.setParent('..')
        cmds.setParent('..')
        cmds.setParent('..')

        cmds.showWindow(self.name)
        cmds.window(self.name, edit=True, leftEdge=300, width=self.width, height=self.height)

        self.refresh()

    def group(self, *args):
        obj = self.getDataObj()
        path = obj.datapath() + '/' + obj.datafile()

        if not os.path.exists(path):
            cmds.warning('Asset does not exist yet or selection is incomplete')
            return False

        group = ''
        with open(path) as datafile:
            data = json.load(datafile)
            if 'group' in data.keys():
                group = data['group']

        result = cmds.promptDialog(title='Group Name', message='Enter Name:', button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel', text=group)
        if result == 'OK':
            group = cmds.promptDialog(query=True, text=True)
            if group != '':
                data['group'] = group
                with open(path, 'w') as datafile:
                    json.dump(data, datafile)
                self.refresh()
            else:
                cmds.warning('group name cannot be empty. Abording...')

    def dataAndThumb(self, mode='gather'):
        # Functions [start]
        def render(*args):
            pr = args[1]
            filePrefix = cmds.getAttr( 'defaultRenderGlobals.imageFilePrefix' )
            fileFormat = cmds.getAttr( 'defaultRenderGlobals.imageFormat' )

            cmds.setAttr( 'defaultRenderGlobals.imageFormat', 32 )

            newFilePrefix = 'thumb.1'
            thumbPath = nerve.maya.projPath() + '/maya/images/tmp/' + newFilePrefix + '.png'
            if os.path.exists( thumbPath ):
                os.remove(thumbPath)
                tmp = int(newFilePrefix.split('.')[-1])
                postFix = '1' if tmp == 2 else '2'
                newFilePrefix = 'thumb.' + str(postFix)

            cmds.setAttr( 'defaultRenderGlobals.imageFilePrefix', newFilePrefix, type="string" )

            path = cmds.hwRender( currentView=True, width=1280, height=720, noRenderView=False, writeAlpha=False)
            self.sel["thumb"] = path
            cmds.iconTextButton( args[0].ctrl[pr+"thumb"], e=True, image=path)


            # restore
            if filePrefix is None:
                filePrefix = ""
            cmds.setAttr( 'defaultRenderGlobals.imageFilePrefix', filePrefix, type="string" )
            cmds.setAttr( 'defaultRenderGlobals.imageFormat', fileFormat )

        # Functions [end]

        pr = 'r'
        args = {}
        args['textField'] = {}
        args['scrollField'] = {}
        scrollHeight = 115
        if mode == 'gather':
            pr = 'g'
            scrollHeight = 74
            args["textField"] = {'editable':False}
            c = 0.25
            args["scrollField"] = {'enable':True, 'editable':False, 'backgroundColor':[c,c,c]}

        # DATA & THUMB
        if True:
            cmds.rowLayout(numberOfColumns=2, height=140, columnWidth=[(1, 330), (2,230)])

            cmds.columnLayout()

            if mode == 'gather':
                if True:
                    cmds.rowLayout(numberOfColumns=2)
                    cmds.text('Date: ')
                    self.ctrl[pr+"date"] = cmds.textField(text='', width=292, **args["textField"])
                    cmds.setParent('..')
                if True:
                    cmds.rowLayout(numberOfColumns=2)
                    cmds.text('From: ')
                    self.ctrl[pr+"from"] = cmds.textField(text='', width=290, **args["textField"])
                    cmds.setParent('..')
            if True:
                cmds.columnLayout()
                cmds.text(label="Comments: ")
                self.ctrl[pr+"comments"] = cmds.scrollField(height=scrollHeight, width=324,**args["scrollField"])
                cmds.setParent('..')

            cmds.setParent('..')

            #self.ctrl[pr+"thumb"] = cmds.iconTextButton(width=230, height=130, image="sty",

            if mode == 'release':
                c = 0.22
                self.ctrl[pr+"thumb"] = cmds.iconTextButton(width=230, height=130, image='render_swColorPerVertex.png', backgroundColor=[c,c,c], command=partial(render, self, pr))
            else:
                c = 0.22
                self.ctrl[pr+"thumb"] = cmds.iconTextButton(width=230, height=130, image='nodeGrapherClose.png', backgroundColor=[c,c,c])

            cmds.setParent('..')

    def frameLayout(self, **kwargs):
        args = {}
        args["width"] = self.width-2
        args["labelIndent"] = 0
        args["font"] = "boldLabelFont"
        args["marginHeight"] = self.margin
        args["marginWidth"] = self.margin
        args["collapsable"] = False
        args["collapse"] = False

        for key in kwargs.keys():
            args[key] = kwargs[key]

        return cmds.frameLayout(**args)

    def textScrollList(self, **kwargs):

        args = {}
        args["height"] = 170
        args["numberOfRows"] = 5
        args["allowMultiSelection"] = False
        args["font"] ="plainLabelFont"
        args["selectCommand"] = self.refresh

        for key in kwargs.keys():
            args[key] = kwargs[key]

        return cmds.textScrollList(**args)

    def refreshCtrlWithGroups(self, name, default, list, ctrl):
        # get selection
        selection = cmds.textScrollList(ctrl, query=True, selectItem=True)

        # set selection
        if selection is None:
            self.sel[name] = default
        else:
            self.sel[name] = str(selection[0]).lstrip()

        # remove all
        cmds.textScrollList(ctrl, edit=True, removeAll=True)

        list = collections.OrderedDict(sorted(list.items()))

        # recreate list
        if not list:
            list = {}

        items = []
        tabbedItems = []
        line = 1

        for grp in list.keys():
            tab = ''
            if grp != '<none>':
                cmds.textScrollList(ctrl, edit=True, append=grp)
                cmds.textScrollList(ctrl, edit=True, lineFont=[line, 'smallBoldLabelFont'])
                line+=1
                tab = '      '

            for item in list[grp]:
                items.append(item)
                tabbedItems.append(tab+item)
                cmds.textScrollList(ctrl, edit=True, append=tab+item )
                line+=1

        #for item in list:
            #cmds.textScrollList(ctrl, edit=True, append=item)

        # reselect
        for i in range(len(items)):
            if self.sel[name] == items[i]:
                cmds.textScrollList(ctrl, edit=True, selectItem=tabbedItems[i])

        if self.sel[name] not in items:
            self.sel[name] = ''


    def refreshCtrl(self, name, default, list, ctrl):
        # get selection
        selection = cmds.textScrollList(ctrl, query=True, selectItem=True)

        # set selection
        if selection is None:
            self.sel[name] = default
        else:
            self.sel[name] = str(selection[0])

        # remove all
        cmds.textScrollList(ctrl, edit=True, removeAll=True)

        # recreate list
        if list is None:
            list = []
        for item in list:
            cmds.textScrollList(ctrl, edit=True, append=item)

        # reselect
        if self.sel[name] in list:
            cmds.textScrollList(ctrl, edit=True, selectItem=self.sel[name])
        else:
            self.sel[name] = ''



    def refresh(self, *args):
        self.sel.update( {"job":None, "seq":None, "shot":None, "type":None, "name":None, "version":None} )
        workspace = nerve.maya.projPath()
        job = {}
        job["job"] = workspace.split('/')[2]
        job["seq"] = workspace.split('/')[3]
        job["shot"] = workspace.split('/')[4]

        def sp(a):
            return str(a).lower()

        jobPath = nerve.cfg.path('job')
        # job
        jobList = sorted(os.listdir( jobPath ), key=str.lower)

        self.refreshCtrl('job', job["job"], jobList, self.ctrl["jobSelectJob"])

        # seq
        if self.sel['job'] != '':
            seqList = sorted( os.listdir( jobPath + '/' + self.sel['job']  ), key=sp)
        else:
            seqList = []
        self.refreshCtrl('seq', job['seq'], seqList, self.ctrl['jobSelectSeq'])

        # shot
        if self.sel['seq'] != '':
            shotList = sorted(os.listdir( jobPath + '/' + self.sel['job'] + '/' + self.sel['seq']), key=sp)
        else:
            shotList = []
        self.refreshCtrl('shot', job["shot"], shotList, self.ctrl["jobSelectShot"])

        # Mode
        idx = cmds.tabLayout(self.ctrl["tabLayout"], q=True, selectTabIndex=True)-1
        self.sel["mode"] = 'release' if idx else 'gather'

        # GATHER
        if self.sel["mode"] == "gather":
            # type
            if self.sel["shot"] != '':
                types = self.getAssetTypes(current=True)

            else:
                types = []

            self.refreshCtrl('type', None, types, self.ctrl["gatherType"])

            # name
            if self.sel['type'] != '':
                names = self.getNames()
            else:
                names = {}

            self.refreshCtrlWithGroups('name', None, names, self.ctrl["gatherName"])

            # version
            if self.sel["name"] != '':
                versions = self.getVersions()

            else:
                versions = []

            versions = [str(x) if x!=0 else 'none' for x in versions]
            self.refreshCtrl('version', None, versions, self.ctrl["gatherVersion"])

            # data & thumb
            if self.sel["version"] != '':
                obj = self.getDataObj()
                # Comments
                if obj.has('comments'):
                    cmds.scrollField( self.ctrl['gcomments'], e=True, text=obj["comments"] )
                else:
                    cmds.scrollField( self.ctrl['gcomments'], e=True, text='' )

                # date
                if obj.has('date'):
                    cmds.textField( self.ctrl['gdate'], e=True, text=obj["date"])
                else:
                    cmds.textField( self.ctrl['gdate'], e=True, text='')

                # From
                if obj.has('from'):
                    cmds.textField( self.ctrl['gfrom'], e=True, text=obj['from'] )
                else:
                    cmds.textField( self.ctrl['gfrom'], e=True, text='' )

                # Thumb
                if obj.has('thumb'):
                    cmds.iconTextButton( self.ctrl['gthumb'], e=True, image=obj['thumb'] )
                else:
                    cmds.iconTextButton( self.ctrl['gthumb'], e=True, image='error.png' )
            else:
                cmds.scrollField( self.ctrl['gcomments'], e=True, text='' )
                cmds.textField( self.ctrl['gdate'], e=True, text='')
                cmds.textField( self.ctrl['gfrom'], e=True, text='' )

                # hotkeyFieldClear.png
                # closeTabButton.png
                # nodeGrapherClose
                cmds.iconTextButton( self.ctrl['gthumb'], e=True, image='nodeGrapherClose.png' )
                #


        # Release
        if self.sel["mode"] == "release":
            # type
            if self.sel['shot'] != '':
                types = self.getAssetTypes()
            else:
                types = []

            self.refreshCtrl('type', None, types, self.ctrl["releaseType"])

            # names
            if self.sel['type'] != '':
                names = self.getNames()
                if '<none>' not in names.keys():
                    names['<none>'] = []
                names['<none>'] = ['<new>'] +  names['<none>']
            else:
                names = {}

            self.refreshCtrlWithGroups('name', None, names, self.ctrl['releaseName'])

            # version
            if self.sel['name'] != '':
                versions = self.getVersions()
                if len(versions):
                    if versions[0] != 0:
                        versions.append('<next>')
                    else:
                        versions[0] = 'none'
                else:
                    versions = ['<none>'] + versions
                    versions.append( '<first>' )
            else:
                versions = []

            versions = [str(x) for x in versions]
            self.refreshCtrl('version', None, versions, self.ctrl["releaseVersion"])

            # Comments
            cmds.scrollField(self.ctrl["rcomments"], edit=True, text='')
            if self.sel['version'] != '' and '<' not in self.sel["version"]:
                obj = self.getDataObj()
                cmds.scrollField(self.ctrl["rcomments"], e=True, text=obj["comments"])
                if 'thumb' in obj.keys():
                    cmds.iconTextButton( self.ctrl['rthumb'], e=True, image=obj["thumb"] )
                else:
                    cmds.iconTextButton( self.ctrl['rthumb'], e=True, image='render_swColorPerVertex.png' )
            else:
                cmds.iconTextButton( self.ctrl['rthumb'], e=True, image='render_swColorPerVertex.png' )



    def getAssetTypes(self, current=False):
        types = []
        if current:
            path = nerve.maya.pathFromArgs(self.sel)
            types = os.listdir(path + 'assets/')

        else:
            import inspect
            for m in inspect.getmembers(nerve.maya.asset):
                if isinstance( m[1], type(nerve.assetBase) ):
                    types.append(m[0])

        return types

    def getNames(self, asList=False):
        path = nerve.maya.pathFromArgs(self.sel)
        path+= 'assets/'
        path+= self.sel['type'] + '/'

        files = glob.glob(path + '*.json' )

        if asList:
            if not os.path.exists(path):
                return []

            names = []
            for f in files:
                f = f.replace('\\', '/')
                f = f.split('/')[-1]
                f = f.replace( '.json', '' )
                if '_v' in f:
                    names.append( f.split('_v')[0] )
                else:
                    names.append( f )

            return list(set(names))

        else:
            if not os.path.exists(path):
                return {}

            groups = {}
            groups['<none>'] = []

            for f in files:
                f = f.replace('\\', '/')
                data = json.load( open(f) )
                if 'group' in data.keys():
                    if data['group'] not in groups.keys():
                        groups[data['group']] = []
                    groups[data['group']].append( data['name'] )
                else:
                    groups['<none>'].append( data['name'] )

            for grp in groups.keys():
                groups[grp] = list(set( groups[grp] ))

            return groups


    def getVersions(self):
        path = nerve.maya.pathFromArgs(self.sel)
        path+= 'assets/'
        path+= self.sel['type'] + '/'

        versions = []
        files = glob.glob(path + self.sel["name"] + '_*.json')
        files+= glob.glob(path + self.sel["name"] + '.json')

        if not len(files):
            return versions

        for f in files:
            f = f.replace('\\', '/')
            f = f.split('/')[-1]
            f = f.replace('.json', '')

            if '_v' in f:
                versions.append( int(f.split('_v')[-1]) )
            else:
                versions.append( 0 )


        return sorted(versions)

    def getDataObj(self):
        '''
        path = nerve.maya.pathFromArgs(self.sel)
        path+= 'assets/'
        path+= self.sel['type'] + '/'
        path+= self.sel['name']

        if self.sel["version"] == 'none':
            path+= '.json'
        else:
            path+= '_v' + str( self.sel["version"] ).zfill(3) + '.json'

        return path
        '''
        self.sel["version"] = 0 if self.sel["version"] == 'none' else self.sel["version"]
        Class = getattr(nerve.maya.asset, self.sel['type'])
        obj = Class(**self.sel)
        obj.importData()

        return obj

    def gather(self, *args):
        keys = ['job', 'seq', 'shot', 'type', 'name', 'version']
        for k in keys:
            if self.sel[k] is None or self.sel[k] == '':
                nerve.maya.error(k + ' not selected')
                return False

        # Version
        if self.sel['version'] == 'none':
            self.sel['version'] = 0

        nerve.maya.asset.gather( **self.sel )

    def release(self, *args):

        #self.refresh()
        keys = ['job', 'seq', 'shot', 'type', 'name', 'version']
        for k in keys:
            if self.sel[k] is None or self.sel[k] == '':
                nerve.maya.error(k + ' not selected')
                return False

        # New Name
        if self.sel["name"] == '<new>':
            result = cmds.promptDialog( title='New Asset Name', message='Enter Name:', button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel')
            if result == 'OK':
                name = cmds.promptDialog(query=True, text=True)
                if nerve.illegalChars(name, '_'):
                    nerve.maya.error("New Asset name has illegal characters")
                    return False
                else:
                    if name in self.getNames(asList=True):
                        nerve.maya.confirm( 'Name already exists.' )
                        return False
                    self.sel["name"] = name
            else:
                return False

        # Version
        if self.sel["version"] == '<none>' or self.sel['version'] == 'none':
            self.sel["version"] = 0
        elif self.sel["version"] == '<next>' or self.sel['version'] == '<first>':
            self.sel["version"] = None

        # comments
        self.sel["comments"] = cmds.scrollField(self.ctrl["rcomments"], q=True, text=True)

        # Do It
        nerve.maya.asset.release( **self.sel )

    def deselect(self, *args):
        self.sel["type"] = None
        self.sel["name"] = None
        self.sel["version"] = None


        self.refresh()

    def quit(self, *args):
        cmds.deleteUI(self.name)
