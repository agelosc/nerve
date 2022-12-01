# -*- coding: utf-8 -*-
import os, time, heapq
from functools import partial
try:
    from importlib import reload
except:
    pass

from datetime import datetime, timedelta

import nerve
import nerve.win
import nerve.apps
import nerve.maya

import nerve.maya.utilities as utils
import maya.cmds as cmds
import maya.mel as mel

class Dialog:
    @staticmethod
    def Input(msg='Enter Name:', title='Nerve', unique=[]):
        result = cmds.promptDialog(
                title=title,
                message=msg,
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')
        if result == 'OK':
            input = cmds.promptDialog(query=True, text=True)
            if input in unique:
                return Dialog.Input(msg=msg, title='Already Exists', unique=unique)
            if not input:
                return False
            return input
        return False

    @staticmethod
    def ConfirmCancel(msg):
        result = cmds.confirmDialog( title='Confirm', message=msg, button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
        if result == 'Yes':
            return True
        return False

    @staticmethod
    def Confirm(msg):
        cmds.confirmDialog( title='Confirm', message=msg, button=['OK'], defaultButton='OK')

    @staticmethod
    def File(fileMode=3):
        '''
        fileMode:
        0 Any file, whether it exists or not.
        1 A single existing file.
        2 The name of a directory. Both directories and files are displayed in the dialog.
        3 The name of a directory. Only directories are displayed in the dialog.
        4 Then names of one or more existing files.
        '''
        return cmds.fileDialog2(fileMode=fileMode, startingDirectory=cmds.workspace(q=True, rootDirectory=True), dialogStyle=2)

def uicmd(*args):
    if len(args)>2:
        return args[0](*args[1:-1])
    else:
        return args[0]()

class Menu:
    def __init__(self):
        self.ctrl = {}
        self.name = 'Nerve'

        if cmds.menu(self.name, exists=True):
            cmds.deleteUI(self.name)

        gMainWindow = mel.eval('$temp1=$gMainWindow;')
        self.ctrl['mainMenu'] = cmds.menu(self.name, parent=gMainWindow, tearOff=True, label=self.name)

        # Jobs
        self.ctrl['jobs'] = cmds.menuItem(subMenu=True, label='Jobs', parent=self.ctrl['mainMenu'], tearOff=True)
        jobs = nerve.Job.GetRecent()
        for recent in jobs:
            job = nerve.Job(recent)
            label = '{0:<20}{1}'.format(job.GetName(), job.GetFilePath('job'))
            label=job.GetPrettyName()
            #label = '{:<20} {:<15}'.format(job.GetFilePath('job'), job.GetName())
            cmds.menuItem(subMenu=False, label=label, parent=self.ctrl['jobs'], command=partial(uicmd, nerve.maya.Job.Set, job.GetFilePath('job')) )

        cmds.menuItem(divider=True, parent=self.ctrl['jobs'])
        #cmds.menuItem(subMenu=False, label='Add...', parent=self.ctrl['jobs'], command=self.JobAdd)
        cmds.menuItem(subMenu=False, label='Create...', parent=self.ctrl['jobs'], command=self.JobCreate)

        # Explore
        cmds.menuItem(subMenu=False, label='Explore', parent=self.ctrl['mainMenu'], command=utils.Explore)

        # Layers
        if False:
            cmds.menuItem(divider=True, dividerLabel='Layers', parent=self.ctrl['mainMenu'])
            self.ctrl['layerMenu'] = cmds.menuItem(subMenu=True, label='Sequences', tearOff=True, parent=self.ctrl['mainMenu'])
            cmds.menuItem(self.ctrl['layerMenu'], e=True, postMenuCommand=partial(self.LayerMenu, self.ctrl['layerMenu']), postMenuCommandOnce=False)

        # Tools
        cmds.menuItem(divider=True, dividerLabel='Tools', parent=self.ctrl['mainMenu'])
        self.Tools()

        cmds.menuItem(divider=True, dividerLabel='Assets', parent=self.ctrl['mainMenu'])
        cmds.menuItem(subMenu=False, label='Release...', parent=self.ctrl['mainMenu'], command=partial(uicmd, Manager, 'release'))
        cmds.menuItem(subMenu=False, label='Gather...', parent=self.ctrl['mainMenu'], command=partial(uicmd, Manager, 'gather'))

        cmds.menuItem(divider=True, parent=self.ctrl['mainMenu'])
        cmds.menuItem(subMenu=False, label='Reload Nerve...', parent=self.ctrl['mainMenu'], command=self.reloadNerve)

        if False:
            cmds.menuItem(divider=True, dividerLabel='Assets', parent=self.ctrl['mainMenu'])
            cmds.menuItem(subMenu=False, label='Asset Gather...', parent=self.ctrl['mainMenu'], command=partial(self.Manager, 'Assets', 'gather'))
            cmds.menuItem(subMenu=False, label='Asset Release...', parent=self.ctrl['mainMenu'], command=partial(self.Manager, 'Assets', 'release'))

        if False:
            # Sublayers
            cmds.menuItem(divider=True, dividerLabel='Sublayers', parent=self.ctrl['mainMenu'])
            cmds.menuItem(subMenu=False, label='Sublayer Gather...', parent=self.ctrl['mainMenu'], command=partial(self.Manager, 'Sequences', 'gather'))
            cmds.menuItem(subMenu=False, label='Sublayer Release...', parent=self.ctrl['mainMenu'], command=partial(self.Manager, 'Sequences', 'release'))

    def JobCreate(self, *args):
        dir = Dialog.File(3)
        if not dir:
            return False

        job = nerve.maya.Job(dir[0])
        job.Create()

        job.Set( job.GetFilePath('job') )
        cmds.menuItem(subMenu=False, label=job.GetName(), parent=self.ctrl['jobs'], insertAfter='', command=partial(uicmd, nerve.maya.Job.Set, job.GetFilePath('job')))

    def JobAdd(self, *args):
        dir = Dialog.File(3)
        if not dir:
            return False

        dir = dir[0]
        job = nerve.Job(dir)
        if not job.Exists():
            print('Job does not exist or not created with nerve.'),
            return False

        if dir in nerve.Job.GetRecent():
            print('Job already in recent jobs.'),
            return False

        nerve.Job.AddToRecent(dir)
        cmds.menuItem(subMenu=False, label=job.GetName(), parent=self.ctrl['jobs'], insertAfter='', command=partial(uicmd, nerve.maya.Job.Set, job.GetFilePath('job')))

    def reloadNerve(self, *args):
        import nerve
        reload(nerve)
        import nerve.maya
        reload(nerve.maya)
        import nerve.maya.tools
        reload(nerve.maya.tools)
        import nerve.maya.UI
        reload(nerve.maya.UI)
        nerve.maya.UI.Menu()
        print('Nerve Reloaded...'),

    def Tools(self):
        import nerve.maya.tools
        reload(nerve.maya.tools)

        def sep(label='', parent=self.ctrl['mainMenu']):
            args = {}
            args['divider'] = True
            args['parent'] = parent
            if label:
                args['dividerLabel'] = label
            cmds.menuItem(**args)

        def grp(label='', parent=self.ctrl['mainMenu']):
            return cmds.menuItem(subMenu=True, label=label, parent=parent, tearOff=True)

        def itm(label='', parent=self.ctrl['mainMenu'], cmd=None, args=[]):
            cmds.menuItem(subMenu=False, label=label, parent=parent, command=partial(uicmd, cmd, *args))


        self.ctrl['utils'] = grp('Utilities')
        if True: # Utilities
            parent = self.ctrl['utils']
            sep('Duplicate', parent)
            itm('Duplicate', parent, nerve.maya.tools.duplicate)
            itm('Instance', parent, nerve.maya.tools.instance)
            itm('Duplicate With Input Graph', parent, nerve.maya.tools.duplicateInputGraph)
            itm('Import All Instances', parent, nerve.maya.tools.deinstance)
            sep('Transforms', parent)
            itm('Reset to Origin', parent, nerve.maya.tools.center)
            itm('Snap Transform', parent, nerve.maya.tools.snap)
            itm('Locator To Pivot', parent, nerve.maya.tools.locatorToPivot)
            itm('Locator To Average', parent, nerve.maya.tools.locatorToAverage)
            sep('', parent)
            itm('Copy Transform', parent, nerve.maya.tools.copyTransform)
            itm('Paste Transform', parent, nerve.maya.tools.pasteTransform)
            sep('References', parent)
            itm('Import Reference', parent, nerve.maya.tools.importReference)
            itm('Remove Reference', parent, nerve.maya.tools.removeReference)
            sep('Namespaces', parent)
            itm('Clear Namespaces', parent, nerve.maya.tools.clearNamespaces)
            sep('FBX', parent)
            itm('FBX Locator To Group', parent, nerve.maya.tools.convertFBXLocToGrp)
            sep('Unknown', parent)
            itm('Remove Unknown Nodes', parent, nerve.maya.tools.removeUnknownNodes)
            itm('Remove Unknown Plugins', parent, nerve.maya.tools.removeUnknownPlugins)
            itm('Remove Turtle Plugin', parent, nerve.maya.tools.removeTurtle)

        self.ctrl['tools'] = grp('Tools')
        if True: # Scatter
            parent = self.ctrl['tools']
            sep('Scatter', parent)
            itm('Create Scatter...', parent, nerve.maya.tools.scatter)
            itm('Scatter UI', parent, nerve.maya.tools.scatterUI)
            sep('Toon', parent)
            itm('Connect Camera to Outlines', parent, nerve.maya.tools.connectCameraToOutlines)

        self.ctrl['render'] = grp('Rendering')
        if True: # Rendering
            self.ctrl['redshift'] = grp('Redshift', parent=self.ctrl['render'])
            if True: # Redshift
                parent = self.ctrl['redshift']
                sep('Lights', parent)
                itm('Quick Light Setup', parent, nerve.maya.tools.createQuickLightSetup)
                sep('Assets', parent)
                itm('Import Proxy Asset', parent, nerve.maya.tools.importRsProxy)
                itm('Re-release to Proxy/MayaBinary', parent, nerve.maya.tools.releaseMayaToProxy)
                sep('Shading', parent)
                itm('Convert Materials to RedsfhitMaterial', parent, nerve.maya.tools.rsConvertMaterial)
                itm('Convert Opacity To Sprite', parent, nerve.maya.tools.rsConvertOpacityToSprite)
                itm('Convert Sprite To Opacity', parent, nerve.maya.tools.rsConvertSpriteToOpacity)
                itm('Substance To RedshiftMaterial', parent, nerve.maya.tools.substanceToRsMaterial)
                itm('Add Color Correct', parent, nerve.maya.tools.rsConnectColorCorrect)
                sep('Proxies', parent)
                itm('Lock Proxy History', parent, nerve.maya.tools.lockRsProxyHistory)
                sep('Tesselation', parent)
                itm('Enable Tesselation', parent, nerve.maya.tools.enableRsTesselation)
                itm('Disable Tesselation', parent, nerve.maya.tools.disableRsTesselation)
                sep('Displacement', parent)
                itm('Enable Displacement', parent, nerve.maya.tools.enableRsDisplacement)
                itm('Disable Displacement', parent, nerve.maya.tools.disableRsDisplacement)

            parent = self.ctrl['render']
            sep('Color Management', parent)
            itm('Linear workflow', parent, nerve.maya.tools.SetLinearColorManagement)
            itm('ACES workflow', parent, nerve.maya.tools.SetACESColorManagement)
            sep('Rename', parent)
            itm('Rename Material', parent, nerve.maya.tools.renameMaterial)
            sep('Smooth Render', parent)
            itm('Enable Smooth Render', parent, nerve.maya.tools.enableSmoothRender)
            itm('Disable Smooth Render', parent, nerve.maya.tools.disableSmoothRender)
            sep('Render', parent)
            itm('Local Render All Layers', parent, nerve.maya.tools.localRender, [False, True])
            itm('Local Render Current Layer', parent, nerve.maya.tools.localRender, [True, True])
            itm('Local Render Command Only', parent, nerve.maya.tools.localRender, [True, False])

        self.ctrl['modeling'] = grp('Modeling')
        parent = self.ctrl['modeling']
        sep('Pivot', parent)
        itm('Center Pivot', parent, nerve.maya.tools.centerPivots)
        itm('Center Pivot at Base', parent, nerve.maya.tools.centerPivotAtBase)
        itm('Center Pivot at Base and Grid', parent, nerve.maya.tools.centerPivotAtBaseAndGrid)
        itm('Set Pivot to Origin', parent, nerve.maya.tools.freezePivot)
        sep('Freeze', parent)
        itm('Freeze Transform', parent, nerve.maya.tools.freezeTransforms)
        itm('Freeze Transform except Scale', parent, nerve.maya.tools.freezeTransformsNoScale)
        sep('UVs', parent)
        itm('Flatten UV Sets', parent, nerve.maya.tools.flattenUVSets)
        sep('Normals', parent)
        itm('Reset Normals', parent, nerve.maya.tools.resetNormals)
        sep('Tools', parent)
        itm('Merge Vertices', parent, nerve.maya.tools.mergeVertices)
        itm('Extrude', parent, nerve.maya.tools.extrude)
        itm('Edge Loop', parent, nerve.maya.tools.edgeLoop)
        itm('Bevel', parent, nerve.maya.tools.bevel)
        
    def Manager(self, *args):
        Manager(args[0], args[1])

    def SetFrameRange(self, *args):
        cmds.playbackOptions(e=True, min=args[0], max=args[1])

class Base:
    def SetDefaults(self, defaults, **kwargs):
        for key,val in defaults.items():
            kwargs[key] = kwargs[key] if key in kwargs.keys() else val
        return kwargs

    def textField(self, **kwargs):
        defaults = {}
        defaults['width'] = self.width - self.col1-15
        kwargs = self.SetDefaults(defaults, **kwargs)
        return cmds.textField(**kwargs)

    def scrollField(self, **kwargs):
        defaults = {}
        defaults['width'] = self.width - self.col1-15
        defaults['height'] = 70
        defaults['wordWrap'] = True
        kwargs = self.SetDefaults(defaults, **kwargs)
        return cmds.scrollField(**kwargs)

    def iconTextButton(self, **kwargs):
        defaults = {}
        #defaults['image'] = 'render_swColorPerVertex.png'
        defaults['backgroundColor'] = (0.22, 0.22, 0.22)
        defaults['style'] = 'iconOnly'
        defaults['scaleIcon'] = True
        defaults['width'] = (self.width - self.col1-15)/2
        defaults['marginWidth'] = 0
        defaults['marginHeight'] = 0
        defaults['height'] = defaults['width']

        kwargs = self.SetDefaults(defaults, **kwargs)
        return cmds.iconTextButton(**kwargs)

    def textScrollList(self, **kwargs):
        defaults = {}
        defaults['height'] = 170
        defaults['numberOfRows'] = 5
        defaults['allowMultiSelection'] = False

        kwargs = self.SetDefaults(defaults, **kwargs)
        return cmds.textScrollList(**kwargs)

    def text(self, *args, **kwargs):
        defaults = {}
        defaults['width'] = self.col1
        defaults['align'] = 'left'

        kwargs = self.SetDefaults(defaults, **kwargs)
        return cmds.text(*args, **kwargs)

    def tabLayout(self, **kwargs):
        defaults = {}
        kwargs = self.SetDefaults(defaults, **kwargs)
        return cmds.tabLayout(**kwargs)

    def window(self, **kwargs):
        defaults = {}
        defaults['title'] = self.name.capitalize()
        defaults['menuBar'] = False
        defaults['iconName'] = self.name
        defaults['sizeable'] = False
        defaults['toolbox'] = False
        defaults['maximizeButton'] = False
        defaults['resizeToFitChildren'] = True
        defaults['width'] = self.width
        defaults['height'] = self.height

        kwargs = self.SetDefaults(defaults, **kwargs)
        return cmds.window( self.name, **kwargs )

    def separator(self, **kwargs):
        defaults = {}
        #defaults['height'] = 15
        defaults['width'] = self.width-12
        defaults['style'] = 'in'
        kwargs = self.SetDefaults(defaults, **kwargs)

        return cmds.separator( **kwargs )

    def frameLayout(self, **kwargs):
        defaults = {}
        defaults['marginWidth'] = 4

        kwargs = self.SetDefaults(defaults, **kwargs)
        return cmds.frameLayout(**kwargs)

class Manager(Base):
    def __init__(self, action='release', **kwargs):
        import time

        self.name = 'nerver'
        self.width = 500
        self.height = 720
        self.col1 = 60
        self.cover = 'render_swColorPerVertex.png'
        #self.initAction = action

        self.time = time.time()
        self.clicks = 0

        self.data = {}
        self.ctrl = {}

        # Defaults
        self.defaults = {}
        self.defaults['action'] = action
        self.defaults['job'] = nerve.Job().GetFilePath('job')
        self.defaults['path'] = ''
        self.defaults['version'] = None
        for key in self.defaults.keys():
            if key in kwargs.keys():
                #if key == 'path':
                    #kwargs[key]+= '/'
                self.defaults[key] = kwargs[key]
                

        # Init Window
        if cmds.window(self.name, exists=True):
            cmds.deleteUI(self.name)

        self.ctrl['window'] = self.window()
        if True:
            cmds.columnLayout()
            if True:
                self.ctrl['tabs'] = self.tabLayout()
                if True:
                    self.ctrl['assets'] = cmds.columnLayout(width=self.width-8)
                    self.AssetsLayout()
                    cmds.setParent('..')
                cmds.setParent('..')
            cmds.setParent('..')

        cmds.tabLayout(self.ctrl['tabs'], e=True, tabLabel=[(self.ctrl['assets'], 'Assets')])

        cmds.showWindow(self.ctrl['window'])
        cmds.window(self.name, edit=True, width=self.width, height=self.height)

    def AssetsLayout(self):
        cmds.columnLayout()

        self.separator()
        if True: # Action
            cmds.rowLayout(numberOfColumns=4, height=50)
            self.text('Action')
            self.ctrl['action'] = cmds.radioCollection()
            width = (self.width - (self.col1*1) )/4
            self.ctrl['releaseRadio'] = cmds.radioButton(label='Release', changeCommand=self.Refresh, select=True, width=width)
            self.ctrl['gatherRadio'] = cmds.radioButton(label='Gather', changeCommand=self.Refresh, width=width)

            if self.defaults['action'] == 'release':
                cmds.radioButton(self.ctrl['releaseRadio'], e=True, select=True)
            else:
                cmds.radioButton(self.ctrl['gatherRadio'], e=True, select=True)
            cmds.setParent('..')

        self.separator()
        if True: # Job
            cmds.rowLayout(numberOfColumns=3, height=35)
            self.text('Job')
            self.ctrl['job'] = self.textField(text=self.defaults['job'], textChangedCommand=self.Refresh)
            cmds.text(u'\u25BC', width=30)
            self.ctrl['recentJobs'] = cmds.popupMenu('test', button=1)
            cmds.setParent('..')

            for recent in nerve.Job.GetRecent():
                mi = cmds.menuItem(label=recent, command=partial(uicmd, self.JobSet, recent))

            width = cmds.textField(self.ctrl['job'], q=True, width=True)
            cmds.textField(self.ctrl['job'], e=True, width=width-35)

        self.separator()
        if True: # Path
            cmds.rowLayout(numberOfColumns=2, height=40)
            self.text('Path')
            self.ctrl['path'] = self.textField(textChangedCommand=self.Refresh, height=30, text=self.defaults['path'])
            cmds.setParent('..')

        if True: # Lists
            cmds.rowLayout(numberOfColumns=4)
            #self.text('')
            #self.ctrl['pathlist'] = self.textScrollList(width=200, selectCommand=self.SelectPath, doubleClickCommand=self.EnterPath)
            self.ctrl['pathlist'] = self.textScrollList(width=200, selectCommand=self.EnterPath)
            self.ctrl['versionlist'] = self.textScrollList(width=82, selectCommand=self.Refresh)
            self.ctrl['formatlist'] = self.textScrollList(width=200, allowMultiSelection=True, selectCommand=self.Refresh)
            cmds.setParent('..')
        if False: # Lists
            cmds.rowLayout(numberOfColumns=2)
            #self.text('')
            #self.ctrl['pathlist'] = self.textScrollList(width=200, selectCommand=self.SelectPath, doubleClickCommand=self.EnterPath)
            self.ctrl['versionlist'] = self.textScrollList(width=141, selectCommand=self.Refresh)
            self.ctrl['formatlist'] = self.textScrollList(width=141, allowMultiSelection=True, selectCommand=self.Refresh)
            cmds.setParent('..')


        cmds.text('', height=10)
        self.separator()
        if True: # transform
            cmds.rowLayout(numberOfColumns=2, height=50)
            self.text('Transform')
            self.ctrl['transform'] = cmds.optionMenu()
            cmds.menuItem(label='Keep')
            cmds.menuItem(label='Origin')
            cmds.setParent('..')

        self.separator()

        if True: # Asset data
            textWidth = (self.width - self.col1-20)/2
            form = cmds.formLayout(numberOfDivisions=100)
            if True:

                column = cmds.columnLayout()
                if True: # Description
                    cmds.rowLayout(numberOfColumns=2)
                    self.text('Description')
                    self.ctrl['desc'] = self.textField(text='', width=textWidth, editable=True)
                    cmds.setParent('..')
                if True: # Date
                    cmds.rowLayout(numberOfColumns=2)
                    self.text('Date')
                    self.ctrl['date'] = self.textField(text='', width=textWidth, editable=False)
                    cmds.setParent('..')
                if True: # By
                    cmds.rowLayout(numberOfColumns=2)
                    self.text('User')
                    self.ctrl['user'] = self.textField(text='', width=textWidth, editable=False)
                    cmds.setParent('..')
                if True:
                    cmds.rowLayout(numberOfColumns=2)
                    self.text('Latest')
                    self.ctrl['latest'] = self.textField(text='', width=textWidth, editable=False)
                    cmds.setParent('..')
                if True: # Comments
                    cmds.rowLayout(numberOfColumns=2)
                    self.text('Comment')
                    self.ctrl['comment'] = self.scrollField(text='', width=textWidth)
                    cmds.setParent('..')
                cmds.setParent('..')

                right = cmds.columnLayout()
                if True:
                    cover = cmds.columnLayout(adj=False, width=textWidth, height=textWidth)
                    self.ctrl['cover'] = self.iconTextButton(width=textWidth, image=self.cover, command=partial(self.Cover, 'view'))
                    cmds.setParent('..')

                if True:
                    cmds.rowLayout(numberOfColumns=3)
                    cmds.button(label='Grab', width=textWidth/3, command=partial(self.Cover, 'grab'))
                    cmds.button(label='Paste', width=textWidth/3,  command=partial(self.Cover, 'paste'))
                    cmds.button(label='Select', width=textWidth/3,  command=partial(self.Cover, 'select'))
                    cmds.setParent('..')
                cmds.setParent('..')

            cmds.setParent('..')

            cmds.formLayout(form, edit=True, attachForm=[(column, 'top', 5), (right, 'right', 5), (right, 'top', 5)])

        cmds.text('  ', height=10)
        self.separator()
        cmds.text(' ', height=5)
        if True: # button
            cmds.rowLayout(numberOfColumns=1)
            self.ctrl['doit'] = cmds.button(label='Release', width=self.width-14, height=50, command=self.ReleaseGather)
            cmds.setParent('..')

        cmds.setParent('..')

        self.Refresh({})

    def Cover(self, *args):
        action = args[0]

        if action == 'view':
            imagepath = cmds.iconTextButton(self.ctrl['cover'], q=True, image=True)
            if nerve.Path(imagepath).Exists():
                image = nerve.Image(imagepath)
                image.Open()
            return True

        if action == 'grab':
            nerve.win.Screenshot()
            return True

        if action == 'paste':
            image = nerve.Image()
            image.SaveClipboard()
            if not image:
                print('Image not found in clipboard. Use Grab first.'),
                return False

            image.Square()
            #image.Save()

            cmds.iconTextButton(self.ctrl['cover'], e=True, image=image.GetFile().AsString())
            return True

        if action == 'select':
            file = Dialog.File(1)
            if not file:
                return False

            file = nerve.Path(file[0])
            extensions = ["jpg", "png", "gif"]
            if file.GetExtension().lower() in extensions:
                image = nerve.Image( file )
                image.Square()
                #image.Save()
                cmds.iconTextButton(self.ctrl['cover'], e=True, image=image.GetFile().AsString())
            else:
                print('Invalid file type. Skipping...'),
            return True

    def Refresh(self, *args):
        data = {}
        for key in ['job', 'path', 'pathlist', 'versionlist', 'formatlist', 'action', 'description', 'cover']:
            data[key] = self.GetData(key)

        self.Refresh_action()
        self.Refresh_pathlist()
        self.Refresh_versionlist()
        self.Refresh_formatlist()
        self.Refresh_assetinfo()
        self.Refresh_button()

    def Refresh_button(self):
        formatlist = self.GetData('formatlist')
        action = self.GetData('action')

        cmds.button(self.ctrl['doit'], e=True, enable=len(formatlist)>0)
        cmds.button(self.ctrl['doit'], e=True, label=action.capitalize())

    def Refresh_assetinfo(self):
        path = self.GetData('path')
        versionlist = self.GetData('versionlist')
        formatlist = self.GetData('formatlist')

        # Clear
        for key in ['desc', 'date', 'user', 'latest']:
            cmds.textField(self.ctrl[key], e=True, text='')
        cmds.scrollField(self.ctrl['comment'], e=True, text='')
        cmds.iconTextButton(self.ctrl['cover'], e=True, image=self.cover)

        args = {}
        args['job'] = self.GetData('job')
        args['path'] = self.GetData('path')
        asset = nerve.Asset(**args)
        if asset.Exists():
            cmds.textField(self.ctrl['desc'], e=True, text=asset.GetLayerData('description'))
        if asset.HasCover():
            cmds.iconTextButton(self.ctrl['cover'], e=True, image=asset.GetFilePath('cover'))

        if not len(versionlist) or versionlist[0] == '<new>': # return if version is not selected or new
            return False

        args = {}
        args['job'] = self.GetData('job')
        args['path'] = self.GetData('path')
        args['version'] = nerve.String.versionAsInt(versionlist[0])
        asset = nerve.Asset(**args)

        #latestFormat = asset.GetLatestFormat()
        cmds.textField(self.ctrl['latest'], e=True, text=nerve.Format(asset.GetLayerData('format')).GetLong())

        # Selected Formats
        if not len(formatlist):
            return False

        format = asset.GetFormat()
        formats_all = asset.GetFormats()

        for f in [nerve.Format(f).GetName() for f in formatlist]:
            if f in formats_all:
                format = f
                break
        asset.SetFormat(format)

        # Get default/latest format variant assetInfo if format not selected, last selected format otherwise
        #assetInfo = asset.GetAssetInfo()
        #asset.Load()
        fdata = asset.GetFormatData()
        if 'date' in fdata.keys():
            cmds.textField(self.ctrl['date'], e=True, text=fdata['date'])
        if 'user' in fdata.keys():
            cmds.textField(self.ctrl['user'], e=True, text=fdata['user'])
        cmds.scrollField(self.ctrl['comment'], e=True, text=fdata['comment'] if 'comment' in fdata.keys() else '')

    def Refresh_formatlist(self):
        formatlist = self.GetData('formatlist')
        versionlist = self.GetData('versionlist')

        cmds.textScrollList(self.ctrl['formatlist'], e=True, removeAll=True)

        if not len(versionlist):
            return True

        path = self.GetData('path')
        version = 0 if versionlist[0] == '<new>' else nerve.String.versionAsInt( versionlist[0] )

        args = {}
        args['job'] = self.GetData('job')
        args['path'] = path
        args['version'] = version
        asset = nerve.Asset(**args)

        formats_asset = [nerve.Format(f).GetLong() for f in asset.GetFormats()]
        formats_all = nerve.Format.All(long=True) if self.GetData('action') == 'release' else formats_asset

        # Create textScrollList arguments
        args = {'edit':True}
        for i in range(len(formats_all)): # for every available format
            args['append'] = formats_all[i] # append item
            if self.GetData('action') == 'release': # if release make available bold and unavailable italics
                if formats_all[i] in formats_asset:
                    args['lineFont'] = [i+1, 'boldLabelFont']
                else:
                    args['lineFont'] = [i+1, 'obliqueLabelFont']

            else: # if gather make all plain font
                args['lineFont'] = [i+1, 'plainLabelFont']

            cmds.textScrollList(self.ctrl['formatlist'], **args) # append item with font

        # reselect items that exist in updated format list
        selectItems = []
        for item in formatlist:
            if item in formats_all:
                selectItems.append(item)

        if formats_all:
            cmds.textScrollList(self.ctrl['formatlist'], e=True, selectItem=selectItems)

    def Refresh_versionlist(self):
        path = self.GetData('path')
        versionlist = self.GetData('versionlist')
        # Asset
        args = {}
        args['job'] = self.GetData('job')
        args['path'] = path
        asset = nerve.Asset(**args)
        

        # Versions
        versions = []
        if asset.Exists():
            versions = asset.GetVersions(asString=True)
        # add new version item
        if self.GetData('action') == 'release':
            versions.append('<new>')

        cmds.textScrollList(self.ctrl['versionlist'], e=True, removeAll=True, append=versions)
        if len(versionlist) and versionlist[0] in versions:
            cmds.textScrollList(self.ctrl['versionlist'], e=True, selectItem=versionlist[0])
            return True

        if self.defaults['path']:
            version = self.defaults['version']
            if not version:
                version = asset.GetVersions()[-1]
            cmds.textScrollList(self.ctrl['versionlist'], e=True, selectItem=nerve.String.versionAsString(version))
        

    def Refresh_pathlist(self):
        path = self.GetData('path')
        pathlist = self.GetData('pathlist')

        # Asset
        args = {}
        args['job'] = self.GetData('job')
        args['path'] = path if (path and path[-1] == '/') else nerve.String.GetParentPath(path)
        asset = nerve.Asset(**args)

        '''
        # Children
        if '*' in path: # Get Children with Wildcard
            children = asset.GetChildrenByFilter( path.replace('*', '') )
        else: # Get all children
        '''
        children = asset.GetChildren()

        # Add level up
        if path and path != '/' and '/' in path[1:]: # path is set and is not / and is not at root level
            children.insert(0, '..')

        # Empty Scroll List
        cmds.textScrollList(self.ctrl['pathlist'], e=True, removeAll=True, append=children)

        # Make Assets with Children bold
        for i in range(len(children)):
            args['path'] = path+'/'+children[i]
            childAsset = nerve.Asset(**args)
            if childAsset.HasChildren():
                font = 'boldLabelFont'
            else:
                font = 'plainLabelFont'
            #font = 'boldLabelFont' if children[i] and nerve.Asset(**args).HasChildren() else 'plainLabelFont'
            cmds.textScrollList(self.ctrl['pathlist'], e=True, lineFont=(i+1, font))

        # Reselect
        if len(pathlist) and pathlist[0] in children:
            cmds.textScrollList(self.ctrl['pathlist'], e=True, selectItem=pathlist[0])
            return True
        
        
        if not len(pathlist) and self.defaults['path']:
            cmds.textScrollList(self.ctrl['pathlist'], e=True, selectItem=nerve.Path(self.defaults['path']).GetHead())
            self.Refresh()
        




    def Refresh_action(self):
        # Change Button label
        action = self.GetData('action')

        # Enable/Disable Asset Data
        if action == 'release':
            cmds.textField(self.ctrl['desc'], e=True, enable=True)
            cmds.scrollField(self.ctrl['comment'], e=True, editable=True, backgroundColor=(0.17, 0.17, 0.17))
            cmds.optionMenu(self.ctrl['transform'], e=True, enable=True)
        else:
            cmds.textField(self.ctrl['desc'], e=True, enable=False)
            cmds.scrollField(self.ctrl['comment'], e=True, editable=False, backgroundColor=(0.25, 0.25, 0.25))
            cmds.optionMenu(self.ctrl['transform'], e=True, enable=False)

    def EnterPath(self):
        sel = self.GetData('pathlist')
        if not sel:
            return False

        path = self.GetData('path')

        # Asset
        args = {}
        args['job'] = self.GetData('job')
        args['path'] = path + sel[0]
        asset = nerve.Asset(**args)
        if not asset.HasChildren() and sel[0] != '..': 
            self.SelectPath()
            return False

        if sel[0] == '..':
            path = nerve.Path(path).GetParent().AsString() + '/'
            cmds.textField(self.ctrl['path'], e=True, text=path.lstrip('/'))
        else:
            if path:
                if path[-1] == '/':
                    cmds.textField(self.ctrl['path'], e=True, text=path+sel[0]+'/')
                else:
                    path = nerve.Path(path).SetHead(sel[0]).AsString()
                    cmds.textField(self.ctrl['path'], e=True, text=path+'/')
            else:
                cmds.textField(self.ctrl['path'], e=True, text=sel[0]+'/')

    def SelectPath(self):
        sel = self.GetData('pathlist')
        if not sel:
            return False

        if sel[0] == '..':
            sel[0] = ''

        path = self.GetData('path')
        if path:
            if path[-1] == '/':
                cmds.textField(self.ctrl['path'], e=True, text=path+sel[0])
            else:
                path = nerve.Path(path).SetHead(sel[0]).AsString()
                cmds.textField(self.ctrl['path'], e=True, text=path)
        else:
            cmds.textField(self.ctrl['path'], e=True, text=sel[0])

    def GetTransform(self, n):
        data = {}
        pos = cmds.xform(n, q=True, ws=True, t=True)
        rot = cmds.xform(n, q=True, ws=True, ro=True)
        scale = cmds.xform(n, q=True, ws=True, s=True)

        data['transform'] = (pos[0], pos[1], pos[2])
        data['rotate'] = (rot[0], rot[1], rot[2])
        data['scale'] = (scale[0], scale[1], scale[2])

        return data

    def SetTransform(self, n, data):
        cmds.xform(n, ws=True, t=data['transform'])
        cmds.xform(n, ws=True, ro=data['rotate'])
        cmds.xform(n, ws=True, s=data['scale'])

    def ResetTransform(self, n):
        cmds.xform(n, ws=True, t=(0,0,0))
        cmds.xform(n, ws=True, ro=(0,0,0))
        cmds.xform(n, ws=True, s=(1,1,1))

    def ReleaseGather(self, *args):
        args = {}
        for key in ['path', 'job', 'version', 'description', 'comment']:
            args[key] = self.GetData(key)

        # Release
        if self.GetData('action') == 'release':
            sel = cmds.ls(sl=True, l=True)
            if not len(sel):
                print('Nothing Selected. Skipping release...'),
                return False

            xforms = []
            if self.GetData('transform') == 2:
                for n in sel:
                    xforms.append( self.GetTransform(n))
                    self.ResetTransform(n)

            tmp = nerve.Asset(**args)
            args['version'] = tmp.GetVersion()
            for format in self.GetData('formats'):
                args['format'] = nerve.Format(format).GetName()
                asset = nerve.maya.asset( **args )

                if hasattr(asset, 'ReleaseUI'):
                    result = asset.ReleaseUI()
                else:
                    result = asset.Release()

            cover = nerve.Path(self.GetData('cover'))
            if cover.Exists() and cover != asset.GetFilePath('cover'):
                cover.Copy(asset.GetFilePath('cover'))
                
            
            if self.GetData('transform') == 2:
                for i in range(len(sel)):
                    n = sel[i]
                    xform = xforms[i]
                    self.SetTransform(n, xform)

            if result:
                Dialog.Confirm('Asset Released.')
            return True
            
        # Gather
        if self.GetData('action') == 'gather':
            format = self.GetData('formats')[0]
            args['format'] = nerve.Format(format).GetLong()
            asset = nerve.maya.asset(**args)

            if hasattr(asset, 'GatherUI'):
                asset.GatherUI()
            else:
                asset.Gather()
            

        self.Refresh({})

    def GetData(self, key):
        if key not in self.data.keys():
            if key == 'job':
                return cmds.textField(self.ctrl['job'], q=True, text=True)

            if key == 'path':
                return cmds.textField(self.ctrl['path'], q=True, text=True)

            if key == 'pathlist':
                return cmds.textScrollList(self.ctrl['pathlist'], q=True, selectItem=True) or []

            if key == 'versionlist':
                return cmds.textScrollList(self.ctrl['versionlist'], q=True, selectItem=True) or []

            if key == 'formatlist':
                return cmds.textScrollList(self.ctrl['formatlist'], q=True, selectItem=True) or []

            if key == 'version':
                versionAsString = self.GetData('versionlist')
                if not versionAsString:
                    return 0
                if versionAsString[0] == '<new>':
                    return 0
                return nerve.String.versionAsInt(versionAsString[0])

            if key == 'formats':
                return cmds.textScrollList(self.ctrl['formatlist'], q=True, selectItem=True) or []

            if key == 'action':
                buttons = cmds.radioCollection(self.ctrl['action'], q=True, collectionItemArray=True)
                for button in buttons:
                    if cmds.radioButton(button, q=True, select=True):
                        action = cmds.radioButton(button, q=True, label=True).lower()
                        return action

            if key == 'description':
                return cmds.textField(self.ctrl['desc'], q=True, text=True)

            if key == 'cover':
                return cmds.iconTextButton(self.ctrl['cover'], q=True, image=True)

            if key == 'comment':
                return cmds.scrollField(self.ctrl['comment'], q=True, text=True)

            if key == 'transform':
                return cmds.optionMenu(self.ctrl['transform'], q=True, select=True)

            raise Exception(key+' not found in data.')

        return self.data[key]

    def JobSet(self, dir):
        #nerve.maya.Job.Set(dir)
        cmds.textField(self.ctrl['job'], e=True, text=dir)
        self.Refresh({})

class Scatter(Base):
    def __init__(self):
        self.data = {}
        self.ctrl = {}

        self.name = 'scatter'
        self.width = 340
        self.height = 600
        self.col1 = 70

        success = self.init()
        if success:
            self.initUI()

    def initUI(self):
        if cmds.window(self.name, exists=True):
            cmds.deleteUI(self.name)

        self.ctrl['window'] = self.window()
        if True:
            cmds.columnLayout()
            self.frameLayout(label='Scatter')
            if True: # MASH node
                cmds.rowLayout(numberOfColumns=2, height=50)
                self.text('Mash')
                self.textField(text=self.data['mash'], editable=False)
                cmds.setParent('..')
            cmds.setParent('..')

            if True: # Geometry
                self.frameLayout(label='Geometry')
                if True:
                    cmds.rowLayout(numberOfColumns=3)
                    self.text('Geometry')
                    self.ctrl['geo'] = self.textField(text=self.GetGeometry(), editable=False )
                    self.ctrl['connectgeo'] = cmds.button(label='Connect', command=self.SetGeometry, width=60)
                    cmds.textField(self.ctrl['geo'], e=True, width= cmds.textField(self.ctrl['geo'], q=True, width=True)-60)
                    cmds.setParent('..')

                if True:
                    cmds.rowLayout(numberOfColumns=3)
                    self.text('')
                    self.ctrl['calcRotation'] = cmds.checkBox(label='Calculate Rotation', value=cmds.getAttr(self.GetDistNode() + '.calcRotation'), changeCommand=self.calcRotation)
                    self.ctrl['useUpVector'] = cmds.checkBox(label='Use Up Vector', value=cmds.getAttr(self.GetDistNode() + '.useUpVector'), changeCommand=self.useUpVector)
                cmds.setParent('..')

            if True: # instances
                self.frameLayout(label='Instances')
                if True:
                    cmds.rowLayout(numberOfColumns=2, rowAttach=(1, 'top', 0))
                    self.text('Originals')
                    self.ctrl['instances'] = self.textScrollList(allowMultiSelection=True, append=[cmds.ls(i, l=False)[0] for i in self.GetInstances()], uniqueTag=self.GetInstances())
                    cmds.setParent('..')

                if True: # Instance Buttons
                    cmds.rowLayout(numberOfColumns=4)
                    self.text('')
                    self.ctrl['instSelect'] = cmds.button(label='Select', width=(self.width - self.col1)/3 - 5, command=self.InstanceSelect)
                    self.ctrl['instAdd'] = cmds.button(label='Add', width=(self.width - self.col1)/3 - 5, command=self.InstanceAdd)
                    self.ctrl['instRemove'] = cmds.button(label='Remove', width=(self.width - self.col1)/3 - 5, command=self.InstanceRemove)
                    cmds.setParent('..')

                if True: # display
                    cmds.rowLayout(numberOfColumns=2)
                    self.text('Display')

                    self.ctrl['display'] = cmds.optionMenu(changeCommand=self.display)
                    for item in ['Geometry', 'Bounding Boxes', 'Bounding Box']:
                        cmds.menuItem(label=item)
                    value = cmds.getAttr( self.GetInstancer() + '.levelOfDetail')
                    cmds.optionMenu(self.ctrl['display'], e=True, select=value+1)
                    cmds.setParent('..')

                if True: # Point Count
                    cmds.rowLayout(numberOfColumns=2)
                    self.text('Point Count')
                    self.ctrl['pointCount'] = cmds.intSliderGrp( field=True, minValue=0, maxValue=100, fieldMaxValue=100000000, value=cmds.getAttr(self.GetDistNode() + '.pointCount'), changeCommand=self.pointCount, dragCommand=self.pointCount )
                    cmds.setParent('..')

                if True:
                    self.frameLayout(label='Variations')
                    for attr in ['rotationX', 'rotationY', 'rotationZ']:
                        if True:
                            cmds.rowLayout(numberOfColumns=2)
                            self.text(attr)
                            node = self.GetRandNode()
                            cmd = partial(self.updateFloat, attr, node )
                            value = cmds.getAttr(node+'.'+attr)
                            self.ctrl[attr] = cmds.floatSliderGrp( field=True, minValue=0, maxValue=360, value=value, changeCommand=cmd, dragCommand=cmd)
                            cmds.setParent('..')

                    if True:
                        cmds.rowLayout(numberOfColumns=2)
                        self.text('Scale')
                        node = self.GetRandNode()
                        cmd = partial(self.updateFloat, 'scaleX', node )
                        value = cmds.getAttr(node+'.scaleX')
                        self.ctrl['scaleX'] = cmds.floatSliderGrp( field=True, minValue=0, maxValue=2, fieldMaxValue=10000, value=value, changeCommand=cmd, dragCommand=cmd)
                        cmds.setParent('..')


            cmds.setParent('..')

        cmds.showWindow(self.ctrl['window'])
        cmds.window(self.name, edit=True, width=self.width, height=self.height)

    def display(self, *args):
        value = cmds.optionMenu(self.ctrl['display'], q=True, select=True)
        cmds.setAttr( self.GetInstancer() + '.levelOfDetail', value-1 )

    def updateFloat(self, *args):
        attr = args[0]
        node = args[1]
        value = cmds.floatSliderGrp(self.ctrl[attr], q=True, value=True)
        cmds.setAttr(node + '.' + attr, value)

    def calcRotation(self, *args):
        value = cmds.checkBox(self.ctrl['calcRotation'], q=True, value=True)
        cmds.setAttr(self.GetDistNode() + '.calcRotation', value )

    def useUpVector(self, *args):
        value = cmds.checkBox(self.ctrl['useUpVector'], q=True, value=True)
        cmds.setAttr(self.GetDistNode() + '.useUpVector', value )

    def pointCount(self, *args):
        cmds.setAttr( self.GetDistNode() + '.pointCount', cmds.intSliderGrp(self.ctrl['pointCount'], q=True, v=True) )

    def InstanceSelect(self, *args):
        cmds.select(self.GetSelectedInstances(), r=True)

    def InstanceAdd(self, *args):
        sel = cmds.ls(sl=True, l=True)
        if not len(sel):
            print('Nothing selected.'),
            return False

        instances = self.GetInstances()
        instancer = self.GetInstancer()
        for n in sel:
            if n not in instances:
                size = cmds.getAttr(instancer + '.inputHierarchy', size=True)
                cmds.connectAttr(n + '.matrix', instancer + '.inputHierarchy[{}]'.format(size+2), f=True)
                cmds.textScrollList(self.ctrl['instances'], e=True, append=cmds.ls(n, l=False), uniqueTag=n)
            else:
                print('{} is already an instance. Skipping...'.format(n)),

        cmds.setAttr(self.GetIdNode() + '.numObjects', len(self.GetInstances()))

    def InstanceRemove(self, *args):
        items = self.GetSelectedInstances()
        instancer = self.GetInstancer()
        for item in items:
            plug = cmds.listConnections(item + '.matrix', p=True, type='instancer') or []
            cmds.disconnectAttr(item + '.matrix', plug[0])
            cmds.textScrollList(self.ctrl['instances'], e=True, removeItem=cmds.ls(item, l=False)[0])

        cmds.setAttr(self.GetIdNode() + '.numObjects', len(self.GetInstances()))

    def GetGeometry(self):
        dist = self.GetDistNode()
        geo = cmds.listConnections( dist + '.inputMesh' ) or []
        return cmds.ls(geo, l=True)[0] if geo else ''

    def SetGeometry(self, *args):
        sel = cmds.ls(sl=True, l=True)
        if not len(sel):
            print('Nothing selected.'),
            return False

        mesh = sel[0]
        if cmds.nodeType(mesh) == 'transform':
            mesh = cmds.listRelatives(mesh, fullPath=True, s=True) or []
            mesh = mesh[0]

        if cmds.nodeType(mesh) != 'mesh':
            print('Selection is not a polygon mesh.'),
            return False

        dist = self.GetDistNode()
        cmds.setAttr(dist + '.arrangement', 4)
        cmds.connectAttr(mesh+'.worldMesh', dist + '.inputMesh', f=True)
        cmds.setAttr(dist + '.areaBasedScatter', True)

        cmds.textField(self.ctrl['geo'], e=True, text=self.GetGeometry())

    def GetSelectedInstances(self):
        items = cmds.textScrollList(self.ctrl['instances'], q=True, selectUniqueTagItem=True)
        return items

    def GetNode(self, type, origin):
        history = cmds.listHistory(origin, allConnections=True, pruneDagObjects=True)
        for h in history:
            if cmds.nodeType(h) == type:
                return h
        return False

    def GetMashNode(self, sel):
        for n in sel:
            node = self.GetNode('MASH_Waiter', n)
            if node:
                return node

        return False

    def GetInstancer(self):
        inst = cmds.listConnections(self.data['mash'], type='instancer') or []
        if not inst:
            raise Exception('Instancer not found. Scatter setup is corrupted.')
            return False
        return inst[0]

    def GetIdNode(self):
        id = self.GetNode('MASH_Id', self.data['mash'])
        if not id:
            raise Exception('MASH_Id not found. Scatter setup is corrupted.')
            return False
        return id

    def GetDistNode(self):
        dist = self.GetNode('MASH_Distribute', self.data['mash'])
        if not dist:
            raise Exception('MASH_Distribute not found. Scatter setup is corrupted.')
            return False
        return dist

    def GetRandNode(self):
        rand = self.GetNode('MASH_Random', self.data['mash'])
        if not rand:
            raise Exception('MASH_Random not found. Scatter setup is corrupted.')
            return False
        return rand

    def GetInstances(self):
        inst = self.GetInstancer()
        items = cmds.listConnections(inst + '.inputHierarchy') or []
        return [ cmds.ls(i, l=True)[0] for i in items ]

    def init(self):
        sel = cmds.ls(sl=True, l=True)
        if not len(sel):
            print('Nothing Selected.'),
            return False

        mash = self.GetMashNode(sel)
        if not mash:
            print('Cannot find MASH node.'),
            return False

        self.data['mash'] = mash

        return True
