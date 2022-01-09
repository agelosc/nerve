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
            label = '{0:<20}{1}'.format(job.GetName(), job.GetDir())
            label=job.GetName()
            #label = '{:<20} {:<15}'.format(job.GetDir(), job.GetName())
            cmds.menuItem(subMenu=False, label=label, parent=self.ctrl['jobs'], command=partial(uicmd, nerve.maya.Job.Set, job.GetDir()) )

        cmds.menuItem(divider=True, parent=self.ctrl['jobs'])
        cmds.menuItem(subMenu=False, label='Add...', parent=self.ctrl['jobs'], command=self.JobAdd)
        #cmds.menuItem(subMenu=False, label='Create...', parent=self.ctrl['jobs'], command=self.JobCreate)

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
        cmds.menuItem(subMenu=False, label=job.GetName(), parent=self.ctrl['jobs'])

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
            sep('Scatter', parent)
            itm('Create Scatter...', parent, nerve.maya.tools.scatter)
            itm('Scatter UI', parent, nerve.maya.tools.scatterUI)
            sep('Locators', parent)
            itm('Snap Location', parent, nerve.maya.tools.snap)
            itm('Locator To Pivot', parent, nerve.maya.tools.locatorToPivot)
            itm('Locator To Average', parent, nerve.maya.tools.locatorToAverage)
            sep('References', parent)
            itm('Import Reference', parent, nerve.maya.tools.importReference)
            itm('Remove Reference', parent, nerve.maya.tools.removeReference)
            sep('Namespaces', parent)
            itm('Clear Namespaces', parent, nerve.maya.tools.clearNamespaces)
            sep('Unknown', parent)
            itm('Remove Unknown Nodes', parent, nerve.maya.tools.removeUnknownNodes)
            itm('Remove Unknown Plugins', parent, nerve.maya.tools.removeUnknownPlugins)
            itm('Remove Turtle Plugin', parent, nerve.maya.tools.removeTurtle)

        self.ctrl['render'] = grp('Rendering')
        if True: # Rendering
            self.ctrl['redshift'] = grp('Redshift', parent=self.ctrl['render'])
            if True: # Redshift
                parent = self.ctrl['redshift']
                #itm('Release...', parent, nerve.maya.tools.rsRelease)
                #itm('Gather...', parent, nerve.maya.tools.rsGather)
                sep('Proxies', parent)
                itm('Lock Proxy History', parent, nerve.maya.tools.lockRsProxyHistory)
                sep('Tesselation', parent)
                itm('Enable Tesselation', parent, nerve.maya.tools.enableRsTesselation)
                itm('Disable Tesselation', parent, nerve.maya.tools.disableRsTesselation)
                sep('Displacement', parent)
                itm('Enable Displacement', parent, nerve.maya.tools.enableRsDisplacement)
                itm('Disable Displacement', parent, nerve.maya.tools.disableRsDisplacement)

            parent = self.ctrl['render']
            sep('Smooth Render', parent)
            itm('Enable Smooth Render', parent, nerve.maya.tools.enableSmoothRender)
            itm('Disable Smooth Render', parent, nerve.maya.tools.disableSmoothRender)
            sep('Render', parent)
            itm('Local Render', parent, nerve.maya.tools.localRender)

    def Manager(self, *args):
        Manager(args[0], args[1])

    def LayerMenu(self, *args):
        ctrl = args[0]

        cmds.menu(ctrl, e=True, deleteAllItems=True)

        layer = nerve.Layer()
        for seqname in layer.GetChildren():
            seqctrl = cmds.menuItem( subMenu=True, tearOff=True, label=seqname, parent=ctrl)
            seq = nerve.Layer(seqname)
            for shotname in seq.GetChildren():
                shot = nerve.Layer(seqname+'/'+shotname)

                frameRange = shot.GetFrameRange() if shot.HasFrameRange() else [0,0]
                description = shot.GetDescription() if shot.HasDescription() else ''

                label = '{0}'.format( shotname )
                label+= ': [{0} - {1}]'.format( str(int( frameRange[0] )), str(int(frameRange[1])) ) if shot.HasFrameRange() else ''
                label+= ' ' + description

                shotctrl = cmds.menuItem(label=label, parent=seqctrl, command=partial(self.SetFrameRange, frameRange[0], frameRange[1]))
                shotOptCtrl = cmds.menuItem(optionBox=True)
                cmds.menuItem(shotOptCtrl, e=True, command=partial(self.Manager, 'release', seqname+'/'+shotname))

            # New
            cmds.menuItem(divider=True, parent=seqctrl)
            cmds.menuItem(subMenu=False, label='New...', parent=seqctrl, command=partial(CreateShot, seqname))

        # New
        cmds.menuItem(divider=True, parent=ctrl)
        cmds.menuItem(subMenu=False, label='New...', parent=ctrl, command=CreateSequence)

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
        defaults['image'] = 'render_swColorPerVertex.png'
        defaults['backgroundColor'] = (0.22, 0.22, 0.22)
        defaults['style'] = 'iconOnly'
        defaults['scaleIcon'] = True
        defaults['width'] = (self.width - self.col1-15)/2
        defaults['marginWidth'] = 0
        defaults['marginHeight'] = 0
        defaults['height'] = defaults['width']

        kwargs = self.SetDefaults(defaults, **kwargs)
        return cmds.iconTextButton(**kwargs)
        #return cmds.image(image=defaults['image'])

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
        defaults['title'] = self.name
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
    def __init__(self):
        import time

        self.name = 'nerver'
        self.width = 500
        self.height = 700
        self.col1 = 60

        self.time = time.time()
        self.clicks = 0

        self.data = {}
        self.ctrl = {}

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
            cmds.radioButton(label='Release', changeCommand=self.Refresh, select=True, width=width)
            cmds.radioButton(label='Gather', changeCommand=self.Refresh, width=width)
            cmds.setParent('..')

        self.separator()
        if True: # Job
            cmds.rowLayout(numberOfColumns=3, height=35)
            self.text('Job')
            self.ctrl['job'] = self.textField(text=nerve.Job.Get())
            cmds.text(u'\u25BC', width=30)
            self.ctrl['recentJobs'] = cmds.popupMenu('test', button=1)
            cmds.setParent('..')

            for recent in nerve.Job.GetRecent():
                mi = cmds.menuItem(label=recent, command=partial(uicmd, self.JobSet, recent))

            width = cmds.textField(self.ctrl['job'], q=True, width=True)
            cmds.textField(self.ctrl['job'], e=True, width=width-35)

        self.separator()
        if True: # Path
            cmds.rowLayout(numberOfColumns=2, height=30)
            self.text('Path')
            self.ctrl['path'] = self.textField()
            cmds.setParent('..')

        if True: # Lists
            cmds.rowLayout(numberOfColumns=4)
            #self.text('')
            self.ctrl['pathlist'] = self.textScrollList(width=200, selectCommand=self.SelectPath, doubleClickCommand=self.EnterPath)
            self.ctrl['versionlist'] = self.textScrollList(width=82, selectCommand=self.Refresh)
            self.ctrl['formatlist'] = self.textScrollList(width=200, allowMultiSelection=True, selectCommand=self.Refresh)
            cmds.setParent('..')
        cmds.text('', height=10)
        self.separator()

        if True: # Asset data
            textWidth = (self.width - self.col1-20)/2
            form = cmds.formLayout(numberOfDivisions=100)
            if True:

                column = cmds.columnLayout()
                if True: # Description
                    cmds.rowLayout(numberOfColumns=2)
                    self.text('Description')
                    self.ctrl['desc'] = self.textField(text='', width=textWidth)
                    cmds.setParent('..')
                if True: # Date
                    cmds.rowLayout(numberOfColumns=2)
                    self.text('Date')
                    self.ctrl['date'] = self.textField(text='', width=textWidth)
                    cmds.setParent('..')
                if True: # By
                    cmds.rowLayout(numberOfColumns=2)
                    self.text('Owner')
                    self.ctrl['owner'] = self.textField(text='', width=textWidth)
                    cmds.setParent('..')
                if True: # Comments
                    cmds.rowLayout(numberOfColumns=2)
                    self.text('Comments')
                    self.ctrl['comments'] = self.scrollField(text='', width=textWidth)
                    cmds.setParent('..')
                cmds.setParent('..')

                right = cmds.columnLayout()
                if True:
                    cover = cmds.columnLayout(adj=False, width=textWidth, height=textWidth)
                    self.ctrl['cover'] = self.iconTextButton(width=textWidth, command=self.ViewCover)
                    cmds.setParent('..')

                if True:
                    cmds.rowLayout(numberOfColumns=3)
                    cmds.button(label='Grab', width=textWidth/3, command=self.GrabCover)
                    cmds.button(label='Paste', width=textWidth/3, command=self.PasteCover)
                    cmds.button(label='Select', width=textWidth/3, command=self.SelectCover)
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

        # Commands
        for ctrl in ['job', 'path']:
            cmds.textField(self.ctrl[ctrl], e=True, textChangedCommand=self.Refresh)
        self.Refresh({})

    def ViewCover(self, *args):
        image = cmds.iconTextButton(self.ctrl['cover'], q=True, image=True)
        if nerve.Path(image).Exists():
            import os
            os.startfile(image)

    def GrabCover(self, *args):
        nerve.win.Screenshot()

    def PasteCover(self, *args):
        image = nerve.Image.SaveFromClipboard()
        if not image:
            print('Image not found in clipboard. Use Grab first.'),
            return False
        cmds.iconTextButton(self.ctrl['cover'], e=True, image=image.AsString())

    def SelectCover(self, *args):
        file = Dialog.File(1)
        if not file:
            return False

        file = nerve.Path(file[0])

        extensions = ["jpg", "png", "gif"]
        if file.GetExtension().lower() in extensions:
            cmds.iconTextButton(self.ctrl['cover'], e=True, image=file.AsString())
        else:
            print('Invalid file type. Skipping...'),

    def Refresh(self, *args):
        data = {}
        for key in ['job', 'path', 'pathlist', 'versionlist', 'formatlist', 'action', 'description', 'cover']:
            data[key] = self.GetData(key)

        if True: # Action
            cmds.button(self.ctrl['doit'], e=True, label=data['action'].capitalize())
            enable = data['action']=='release'
            color =  (0.17, 0.17, 0.17) if enable else (0.25, 0.25, 0.25)
            for ctrl in ['desc', 'date', 'owner']:
                cmds.textField(self.ctrl[ctrl], e=True, enable=enable)
            cmds.scrollField(self.ctrl['comments'], e=True, backgroundColor=color)
            cmds.scrollField(self.ctrl['comments'], e=True, editable=enable)

        if True: # pathlist
            if data['path'] and data['path'][-1] == '/':
                path = data['path']
            else:
                path = nerve.Path(data['path']).GetParent().AsString()
            asset = nerve.Asset(job=data['job'], path=path)
            #children = nerve.Asset.GetChildrenByFilter(data['path'], data['job'])
            children = asset.GetChildren()
            if data['path'] and data['path'] != '/' and '/' in data['path']: # add back item
                children.insert(0, '..')

            # fill children
            cmds.textScrollList(self.ctrl['pathlist'], e=True, removeAll=True)
            c=0
            for child in children:
                c+=1
                cmds.textScrollList(self.ctrl['pathlist'], e=True, append=child)
                if child == '..':
                    continue

                casset = nerve.Asset(job=data['job'], path=path + '/'+child)
                if casset.HasChildren():
                    cmds.textScrollList(self.ctrl['pathlist'], e=True, lineFont=(c, 'boldLabelFont') )

            #cmds.textScrollList(self.ctrl['pathlist'], e=True, removeAll=True, append=children)
            if len(data['pathlist']) and data['pathlist'][0] in children:
                cmds.textScrollList(self.ctrl['pathlist'], e=True, selectItem=data['pathlist'][0])


        if True: # versionlist
            asset = nerve.Asset(job=data['job'], path=data['path'])
            versions = []
            if asset.Exists():
                versions = asset.GetVersionsFromDisk()
            versions = [ nerve.String.versionAsString(v) for v in versions]

            if data['action'] == 'release':
                versions.append('<new>')

            cmds.textScrollList(self.ctrl['versionlist'], e=True, removeAll=True, append=versions)
            if len(data['versionlist']) and data['versionlist'][0] in versions:
                cmds.textScrollList(self.ctrl['versionlist'], e=True, selectItem=data['versionlist'][0])

        if True: # formatlist
            allFormats = []
            assetFormats = []

            if data['versionlist']: # if version is selected
                version = nerve.String.versionAsInt(data['versionlist'][0]) if data['versionlist'][0] != '<new>' else 0
                asset = nerve.Asset(job=data['job'], path=data['path'], version=version)
                assetFormats = [nerve.maya.Format.GetLong(f) for f in asset.GetFormats()]

                if data['action'] == 'release': # if release display all formats
                    allFormats = nerve.maya.Format.GetAllLong()
                else: # if gather display only available formats
                    allFormats = assetFormats

            cmds.textScrollList(self.ctrl['formatlist'], e=True, removeAll=True)

            args = {'edit':True}
            for i in range(len(allFormats)): # for every available format
                args['append'] = allFormats[i] # append item
                if data['action'] == 'release': # if release make available bold and unavailable italics
                    if allFormats[i] in assetFormats:
                        args['lineFont'] = [i+1, 'boldLabelFont']
                    else:
                        args['lineFont'] = [i+1, 'obliqueLabelFont']
                else: # if gather make all plain font
                    args['lineFont'] = [i+1, 'plainLabelFont']
                cmds.textScrollList(self.ctrl['formatlist'], **args) # append item with font

            # reselect items that exist in updated format list
            selectItems = []
            for item in data['formatlist']:
                if item in allFormats:
                    selectItems.append(item)
            if allFormats:
                cmds.textScrollList(self.ctrl['formatlist'], e=True, selectItem=selectItems)

        if True: # Asset Data
            fdescription = asset.Exists()
            cmds.textField(self.ctrl['desc'], e=True, text=asset.GetDescription() if fdescription else '')
            fcover = asset.Exists() and asset.HasCover()
            cmds.iconTextButton(self.ctrl['cover'], e=True, image=asset.GetCover() if fcover else 'render_swColorPerVertex.png')
            #if asset.HasCover():
                #print(asset.GetCover())


        cmds.button(self.ctrl['doit'], e=True, enable=len(selectItems))

    def EnterPath(self):
        sel = self.GetData('pathlist')
        if not sel:
            return False

        path = self.GetData('path')
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

    def ReleaseGather(self, *args):
        args = {}
        for key in ['path', 'job', 'version']:
            args[key] = self.GetData(key)

        asset = nerve.Asset(**args)

        for format in self.GetData('formats'):
            asset.SetFormat( nerve.maya.Format.GetShort(format) )
            if self.GetData('action') == 'release':
                nerve.maya.ReleaseUI(asset.GetFilePath('session'))
                asset.Create()
            else:
                nerve.maya.GatherUI(asset.GetFilePath('session'))

        if self.GetData('action'):
            #msg = 'Asset released.\n{}\n{}'.format(args['path'].rstrip('/'), '\n'.join(self.GetData('formats')))
            msg = 'Asset Released.'
            Dialog.Confirm(msg)


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
                            self.text(attr.capitalize())
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
            mesh = cmds.listRelatives(mesh, s=True) or []
            mesh = mesh[0]

        if cmds.nodeType(mesh) != 'mesh':
            print('Selection is not a polygon mesh.'),
            return False

        dist = self.GetDistNode()
        cmds.setAttr(dist + '.arrangement', 4)
        cmds.connectAttr(mesh+'.worldMesh', dist + '.inputMesh', f=True)

        cmds.textField(self.ctrl['geo'], e=True, text=self.GetGeometry())

    def GetSelectedInstances(self):
        items = cmds.textScrollList(self.ctrl['instances'], q=True, selectUniqueTagItem=True)
        return items

    def GetNode(self, type, origin):
        history = cmds.listHistory(origin, allConnections=True)
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

class BaseOLD:
    def GetWidth(self, div=2):
        return (self.config['width']/div)-self.config['margin']

    def SetDefaults(self, defaults, **kwargs):
        for key,val in defaults.items():
            kwargs[key] = kwargs[key] if key in kwargs.keys() else val
        return kwargs

    def rowLayout(self, **kwargs):
        defaults = {}
        defaults['numberOfColumns'] = 2
        defaults['columnAlign'] = [1, 'right']
        kwargs = self.SetDefaults(defaults, **kwargs)
        kwargs['columnWidth'] = [(i+1,self.GetWidth(kwargs['numberOfColumns'])) for i in range(defaults['numberOfColumns'])]
        cmds.rowLayout(**kwargs)

    def frameLayout(self, **kwargs):
        defaults = {}
        defaults['collapsable'] = True
        defaults['width'] = self.config['width'] - self.config['margin'] - 6
        kwargs = self.SetDefaults(defaults, **kwargs)
        return cmds.frameLayout(**kwargs)

    def button(self, **kwargs):
        defaults = {}

    def textScrollList(self, **kwargs):
        defaults = {}
        defaults['height'] = 170
        defaults['numberOfRows'] = 5
        defaults['allowMultiSelection'] = False
        kwargs = self.SetDefaults(defaults, **kwargs)
        return cmds.textScrollList(**kwargs)

    def label(self, label, **kwargs):
        defaults = {}
        defaults['width'] = self.config['width']/4
        kwargs = self.SetDefaults(defaults, **kwargs)
        kwargs['label'] = label
        return cmds.text(**kwargs)

    def tabLayout(self, **kwargs):
        defaults = {}
        kwargs = self.SetDefaults(defaults, **kwargs)
        return cmds.tabLayout(**kwargs)

    def window(self, **kwargs):
        defaults = {}
        defaults['title'] = self.name
        defaults['menuBar'] = False
        defaults['iconName'] = self.name
        defaults['sizeable'] = False
        defaults['toolbox'] = False
        defaults['maximizeButton'] = False
        defaults['resizeToFitChildren'] = True
        defaults['width'] = self.config['width']
        defaults['height'] = self.config['width']

        kwargs = self.SetDefaults(defaults, **kwargs)
        return cmds.window( self.name, **kwargs )

class ManagerOLD(BaseOLD):
    def __init__(self, tab='Sequences', mode='release', layer=''):
        self.data = {}
        self.ctrl = {}
        self.subctrl = {}
        self.layout = {}
        self.sublayout = {}
        self.name = 'Managaris'

        self.config = {}
        self.config['width'] = 600
        self.config['height'] = 705
        self.config['margin'] = 4
        self.config['colors'] = {}
        self.config['colors']['inactive'] = [0.25,0.25,0.25]
        self.config['colors']['default'] = [0.17,0.17,0.17]

        # Create
        if cmds.window(self.name, exists=True):
            cmds.deleteUI(self.name)

        self.ctrl['window'] = self.window()
        cmds.columnLayout()
        self.ctrl['mainTabs'] = self.tabLayout()
        if True: # Main Tab Layout
            # Assets Tab
            self.layout['Assets'] = cmds.columnLayout()
            self.AssetsLayout(mode)
            cmds.setParent('..') # Assets Column Layout

            # Layers Tab
            self.layout['Sequences'] = cmds.columnLayout()
            self.SequencesLayout(mode)
            cmds.setParent('..') # Layers Column Layout

            # Dailies
            self.layout['Dailies'] = cmds.columnLayout()
            self.DailiesLayout()
            cmds.setParent('..') # Layers Column Layout


        cmds.setParent('..') # Main Tab Layout
        cmds.setParent('..') # Main Column Layout

        cmds.tabLayout(self.ctrl['mainTabs'], e=True, tabLabel=[(self.layout['Assets'], 'Assets'), (self.layout['Sequences'], 'Sequences'), (self.layout['Dailies'], 'Dailies')])
        cmds.tabLayout(self.ctrl['mainTabs'], e=True, selectTab=self.layout[tab])
        cmds.tabLayout(self.ctrl['mainTabs'], e=True, changeCommand=self.refresh)

        cmds.showWindow(self.ctrl['window'])
        cmds.window(self.name, edit=True, width=self.config['width'], height=self.config['height'])
        self.refresh()

    def refresh(self, *args):
        idx = cmds.tabLayout(self.ctrl['mainTabs'], q=True, selectTabIndex=True)
        labels = cmds.tabLayout(self.ctrl['mainTabs'], q=True, tabLabel=True)
        tab = labels[idx-1]

        if tab == 'Assets':
            cmds.window(self.name, edit=True, height=480)
        if tab == 'Sequences':
            cmds.window(self.name, edit=True, height=890)

        if tab in self.sublayout.keys():
            mode = cmds.tabLayout(self.sublayout[tab]['tabs'], q=True, selectTabIndex=True)
            mode = 'gather' if mode == 1 else 'release'
            getattr(self, tab+'Refresh')(mode)
        else:
            getattr(self, tab+'Refresh')()

    # Sublayer Base #
    def SublayerBaseLayout(self, tab, mode):
        if tab not in self.sublayout.keys():
            self.sublayout[tab] = {}
        if tab not in self.subctrl.keys():
            self.subctrl[tab] = {}

        self.sublayout[tab]['tabs'] = self.tabLayout(width=self.GetWidth(1)-5)
        if True:
            self.sublayout[tab]['gather'] = cmds.columnLayout()
            width = 330
            height = width/1.77

            if True:
                cmds.rowLayout(numberOfColumns=2)
                if True:
                    cmds.columnLayout()
                    if True:
                        wwidth = width-100
                        cmds.rowLayout(numberOfColumns=2)
                        cmds.text('Date: ')
                        self.subctrl[tab]['gatherDate'] = cmds.textField(text='', width=210, editable=False)
                        cmds.setParent('..')

                        cmds.rowLayout(numberOfColumns=2)
                        cmds.text('From: ')
                        self.subctrl[tab]['gatherUser'] = cmds.textField(text='', width=208, editable=False)
                        cmds.setParent('..')

                        cmds.columnLayout()
                        cmds.text('', height=48)
                        cmds.text('Description: ')
                        self.subctrl[tab]['gatherDesc'] = cmds.scrollField(text='', width=240, height=74, editable=False, backgroundColor=[0.25,0.25,0.25])
                        cmds.setParent('..')

                    cmds.setParent('..')

                    cmds.columnLayout()
                    if True:
                        self.subctrl[tab]['gatherThumbnail'] = cmds.iconTextButton(width=width, height=height, flat=True, image='render_swColorPerVertex.png', backgroundColor=[0.22,0.22,0.22])

                    cmds.setParent('..')
                cmds.setParent('..')
            cmds.setParent('..')

            self.sublayout[tab]['release'] = cmds.columnLayout()
            if True:
                cmds.rowLayout(numberOfColumns=2)
                if True:
                    cmds.columnLayout()
                    if True:
                        wwidth = width-100
                        cmds.rowLayout(numberOfColumns=2)
                        cmds.text('Date: ')
                        self.subctrl[tab]['releaseDate'] = cmds.textField(text='', width=210, editable=False)
                        cmds.setParent('..')

                        cmds.rowLayout(numberOfColumns=2)
                        cmds.text('From: ')
                        self.subctrl[tab]['releaseUser'] = cmds.textField(text='', width=208, editable=False)
                        cmds.setParent('..')

                        cmds.columnLayout()
                        cmds.text('', height=48)
                        cmds.text('Description: ')
                        self.subctrl[tab]['releaseDesc'] = cmds.scrollField(text='', width=240, height=74, editable=True)
                        cmds.setParent('..')

                    cmds.setParent('..')

                    cmds.columnLayout()
                    if True:
                        cmds.paneLayout(height=height, width=width)
                        self.subctrl[tab]['modelPanel'] = cmds.modelPanel(menuBarVisible=False)
                        self.subctrl[tab]['modelEditor'] = cmds.modelPanel(self.subctrl[tab]['modelPanel'], q=True, modelEditor=True)
                        cmds.modelEditor(self.subctrl[tab]['modelEditor'], e=True, displayAppearance='smoothShaded', grid=False)
                        cmds.setParent('..')
                        cmds.setParent('..')

                    cmds.setParent('..')
                cmds.setParent('..')
            cmds.setParent('..')

            cmds.tabLayout(self.sublayout[tab]['tabs'], e=True, tabLabel=[(self.sublayout[tab]['gather'], 'Gather'), (self.sublayout[tab]['release'], 'Release')])
            cmds.tabLayout(self.sublayout[tab]['tabs'], e=True, selectTab=self.sublayout[tab][mode])
            cmds.tabLayout(self.sublayout[tab]['tabs'], e=True,  changeCommand=self.refresh)

        cmds.setParent('..')

        cmds.columnLayout()
        if True:
            cmds.rowLayout(numberOfColumns=4, columnAlign4=['left', 'left', 'left', 'left'])
            gwidth = self.GetWidth(4)
            width = gwidth + (gwidth*0.5)/3
            if True:
                cmds.text(label='Group', width=width)
                cmds.text(label='Name', width=width)
                cmds.text(label='Version', width=self.GetWidth(4)/2)
                cmds.text(label='Format', width=width)
            cmds.setParent('..')
            cmds.rowLayout(numberOfColumns=4)
            if True:
                self.subctrl[tab]['asset1'] = self.textScrollList(width=width, selectCommand=self.refresh)
                self.subctrl[tab]['asset2'] = self.textScrollList(width=width, selectCommand=self.refresh)
                self.subctrl[tab]['asset3'] = self.textScrollList(width=gwidth/2, selectCommand=self.refresh)
                self.subctrl[tab]['asset4'] = self.textScrollList(width=width, selectCommand=self.refresh)
                for i in range(1,5):
                    cmds.textScrollList(self.subctrl[tab]['asset'+str(i)], e=True, deleteKeyCommand=partial(self.ClearSelection, self.subctrl[tab]['asset'+str(i)]))
            cmds.setParent('..')

        cmds.columnLayout()
        if True:
            self.subctrl[tab]['assetDoIt'] = cmds.button(label='Gather', width=self.GetWidth(1)-7, height=50)
        cmds.setParent('..')
        cmds.setParent('..')

    def SublayerBaseObject(self, tab, **kwargs):
        if tab == 'Assets':
            return nerve.Asset(**kwargs)
        if tab == 'Sequences':
            path = ''
            if self.data['layer1']:
                path = self.data['layer1']
                if self.data['layer2']:
                    path+='/'+self.data['layer2']
            kwargs['layer'] = path
            return nerve.Sublayer(**kwargs)

    def SublayerBaseRefresh(self, tab, mode):
        # Group
        items = self.SublayerBaseObject(tab, path='').GetChildren()
        if mode == 'release':
            items.append('<new>')
        self.data['asset1'] = self.RefreshTextScrollList(self.subctrl[tab]['asset1'], 'asset1', items)

        # Name
        if self.data['asset1']:
            items = self.SublayerBaseObject(tab, path=self.data['asset1']).GetChildren()
            if mode == 'release':
                items.append('<new>')
            self.data['asset2'] = self.RefreshTextScrollList(self.subctrl[tab]['asset2'], 'asset2', items )
        else:
            self.data['asset2'] = self.RefreshTextScrollList(self.subctrl[tab]['asset2'], 'asset2', [] )
            self.data['asset2'] = None

        # Version
        path = ''
        if self.data['asset1']:
            path = self.data['asset1']
            if self.data['asset2']:
                path+= '/'+self.data['asset2']

        obj = self.SublayerBaseObject(tab, path=path)

        if self.data['asset1'] or self.data['asset2']:
            items =  obj.GetVersionsAsString()
            if mode == 'release':
                items.append('<next>')
            self.data['asset3'] = self.RefreshTextScrollList(self.subctrl[tab]['asset3'], 'asset3', items)
        else:
            self.data['asset3'] = self.RefreshTextScrollList(self.subctrl[tab]['asset3'], 'asset3', [])
            self.data['asset3'] = None

        # Formats
        if self.data['asset3']:
            version = nerve.versionAsInt(self.data['asset3'])
            formats = nerve.maya.GetFormats()
            items = self.SublayerBaseObject(tab, path=path, version=version).GetFormats()

            gitems = [formats[i] for i in items]
            ritems = [formats[key] for key in formats.keys()]

            if mode == 'gather':
                self.data['asset4'] = self.RefreshTextScrollList(self.subctrl[tab]['asset4'], 'asset4', gitems)
            else:
                if self.data['asset3'] == '<next>':
                    gitems = []
                self.data['asset4'] = self.RefreshTextScrollList(self.subctrl[tab]['asset4'], 'asset4', ritems, gitems)

        else:
            cmds.textScrollList(self.subctrl[tab]['asset4'], e=True, removeAll=True)
            self.data['asset4'] = None

        # Description
        if self.data['asset4']:
            self.data['description'] = cmds.scrollField(self.subctrl[tab]['releaseDesc'], q=True, text=True)
        else:
            self.data['description'] = ''

        # Get Current Asset
        #version = nerve.versionAsInt(self.data['asset3']) if self.data['asset4'] else 0
        #asset = nerve.Asset(path, version=version)

        # Gather Metadata
        if self.data['asset4']:
            format = nerve.maya.GetFormats(invert=True)[self.data['asset4']]
            obj = self.SublayerBaseObject(tab, path=path, version=version, format=format)
            data = obj.GetAssetInfo()

            cmds.textField(self.subctrl[tab]['gatherDate'], e=True, text=data['date'] if 'date' in data.keys() else '' )
            cmds.textField(self.subctrl[tab]['gatherUser'], e=True, text=data['user'] if 'user' in data.keys() else '' )
            cmds.scrollField(self.subctrl[tab]['gatherDesc'], e=True, text=data['description'] if 'description' in data.keys() else '' )

            cmds.textField(self.subctrl[tab]['releaseDate'], e=True, text=data['date'] if 'date' in data.keys() else '' )
            cmds.textField(self.subctrl[tab]['releaseUser'], e=True, text=data['user'] if 'user' in data.keys() else '' )
            cmds.scrollField(self.subctrl[tab]['releaseDesc'], e=True, text=data['description'] if 'description' in data.keys() else '' )

            thumbnail = obj.GetThumbnail()
            if not thumbnail:
                thumbnail = 'render_swColorPerVertex'
            cmds.iconTextButton(self.subctrl[tab]['gatherThumbnail'], e=True, image=thumbnail)
        else:
            cmds.textField(self.subctrl[tab]['gatherDate'], e=True, text='')
            cmds.textField(self.subctrl[tab]['releaseDate'], e=True, text='')
            cmds.textField(self.subctrl[tab]['gatherUser'], e=True, text='')
            cmds.textField(self.subctrl[tab]['releaseUser'], e=True, text='')
            cmds.scrollField(self.subctrl[tab]['gatherDesc'], e=True, text='')
            cmds.scrollField(self.subctrl[tab]['releaseDesc'], e=True, text='')
            cmds.iconTextButton(self.subctrl[tab]['gatherThumbnail'], e=True, image='render_swColorPerVertex')

        # Button
        if mode == 'gather':
            func = getattr(self, tab+'Gather')
            cmds.button(self.subctrl[tab]['assetDoIt'], e=True, label='Gather', command=func)
            if (self.data['asset1'] or self.data['asset2']) and self.data['asset3'] and self.data['asset4']:
                cmds.button(self.subctrl[tab]['assetDoIt'], e=True, enable=True)
            else:
                cmds.button(self.subctrl[tab]['assetDoIt'], e=True, enable=False)
        else:
            func = getattr(self, tab+'Release')
            cmds.button(self.subctrl[tab]['assetDoIt'], e=True, label='Release', command=func)
            if (self.data['asset1'] or self.data['asset2']) and self.data['asset3'] and self.data['asset4']:
                cmds.button(self.subctrl[tab]['assetDoIt'], e=True, enable=True)
            else:
                cmds.button(self.subctrl[tab]['assetDoIt'], e=True, enable=False)

    # Assets
    def AssetsLayout(self, mode):
        self.SublayerBaseLayout('Assets', mode )

    def AssetsRefresh(self, mode):
        self.SublayerBaseRefresh('Assets', mode)

    def AssetsGather(self, *args):
        path = self.data['asset1']
        if self.data['asset2']:
            path+= '/'+self.data['asset2']
        version = nerve.versionAsInt(self.data['asset3'])
        formats = nerve.maya.GetFormats(invert=True)
        format = formats[self.data['asset4']]

        asset = nerve.Asset(path, version=version, format=format)
        nerve.maya.GatherUI(asset.GetFilePath('session'))

    def AssetsRelease(self, *args):
        path = self.data['asset1']
        if path == '<new>':
            result = Dialog.Input('Enter Group', 'Asset Group')
            if not result:
                return False
            path = result

        if self.data['asset2']:
            if self.data['asset2'] == '<new>':
                result = Dialog.Input('Enter Name', 'Asset Name')
                if not result:
                    return False
                path+= '/'+result
            else:
                path+= '/'+self.data['asset2']

        if self.data['asset3'] == '<next>':
            version = 0
        else:
            version = nerve.versionAsInt(self.data['asset3'])
        formats = nerve.maya.GetFormats(invert=True)
        format = formats[self.data['asset4']]
        description = self.data['description']

        asset = nerve.Asset(path, version=version, format=format, description=description)
        nerve.maya.ReleaseUI(asset.GetFilePath('session'))

        asset.Create()

        # Thumbnail
        path = nerve.Path('$TMP') + 'nerve'
        if not path.Exists():
            path.Create()

        filename = path.AsString() + '/' + str(asset.GetName()) + '.jpg'

        args = {}
        args['completeFilename'] = filename
        args['editorPanelName'] = self.subctrl['Assets']['modelEditor']
        args['frame'] = cmds.currentTime(q=True)
        args['forceOverwrite'] = True
        args['compression'] = 'jpg'
        args['format'] = 'image'
        args['offScreen'] = True
        args['showOrnaments'] = False
        args['viewer'] = False
        args['widthHeight'] = [330, 330/1.77]
        args['percent'] = 100
        cmds.playblast( **args)

        asset.AttachThumbnail( filename )

        self.refresh()

    # Sequences
    def SequencesLayout(self, mode):

        if True:
            cmds.columnLayout()
            if True:
                cmds.rowLayout(numberOfColumns=2)
                if True:
                    cmds.columnLayout(width=250)
                    if True:
                        cmds.text('Frame Range')
                        self.ctrl['layerFrameRange'] = cmds.intFieldGrp(numberOfFields=2,  columnWidth=[1, 80], columnAlign=[1, 'left'])

                        cmds.text('Description')
                        self.ctrl['layerDescription'] = cmds.scrollField(height=80)
                        cmds.text('', height=5)
                        self.ctrl['layerSave'] = cmds.button(label='Save', width=248, height=50, command=self.SequencesSave)
                    cmds.setParent('..')
                    cmds.columnLayout()
                    if True:
                        self.ctrl['layerThumbnail'] = cmds.iconTextButton(width=330, height=330/1.77, image='render_swColorPerVertex.png', backgroundColor=[0.22,0.22,0.22])
                    cmds.setParent('..')
                cmds.setParent('..')

                cmds.separator(width=self.GetWidth(1))
                cmds.rowLayout(numberOfColumns=2, columnAlign2=['left', 'left'])
                if True:
                    cmds.text('Sequence', width=self.GetWidth(2)-5)
                    cmds.text('Shot', width=self.GetWidth(2)-5)

                cmds.setParent('..')

                cmds.rowLayout(numberOfColumns=2)
                if True:
                    self.ctrl['layer1'] = self.textScrollList(width=self.GetWidth(2)-5, selectCommand=self.refresh)
                    self.ctrl['layer2'] = self.textScrollList(width=self.GetWidth(2)-5, selectCommand=self.refresh)
                cmds.setParent('..')
            cmds.setParent('..')

            #cmds.rowLayout(numberOfColumns=1)
            #if True:
                #cmds.button(label='Save', width=self.GetWidth(1)-12, height=50)
            #cmds.setParent('..')

        self.frameLayout(label='Sublayers')
        self.SublayerBaseLayout('Sequences', mode)
        cmds.setParent('..')

    def SequencesRefresh(self, mode):
        def NewSeq():
            sel = cmds.textScrollList(self.ctrl['layer1'], q=True, selectItem=True)[0]
            if sel == '<new>':
                name = CreateSequence()
                cmds.textScrollList(self.ctrl['layer1'], e=True, append=name)
                cmds.textScrollList(self.ctrl['layer1'], e=True, selectItem=name)
            self.refresh()

        def NewShot():
            seq = cmds.textScrollList(self.ctrl['layer1'], q=True, selectItem=True)[0]
            sel = cmds.textScrollList(self.ctrl['layer2'], q=True, selectItem=True)[0]
            if sel == '<new>':
                name = CreateShot(seq)
                cmds.textScrollList(self.ctrl['layer2'], e=True, append=name)
                cmds.textScrollList(self.ctrl['layer2'], e=True, selectItem=name)

            self.refresh()


        cmds.textScrollList(self.ctrl['layer1'], e=True, selectCommand=NewSeq, deleteKeyCommand=partial(self.ClearSelection, self.ctrl['layer1']))
        cmds.textScrollList(self.ctrl['layer2'], e=True, selectCommand=NewShot, deleteKeyCommand=partial(self.ClearSelection, self.ctrl['layer2']))

        layer = nerve.Layer()
        items = layer.GetChildren()
        items.append('<new>')

        self.data['layer1'] = self.RefreshTextScrollList(self.ctrl['layer1'], 'layer1', items)

        if self.data['layer1']:
            layer = nerve.Layer(self.data['layer1'])
            items = layer.GetChildren()
            items.append('<new>')
            self.data['layer2'] = self.RefreshTextScrollList(self.ctrl['layer2'], 'layer2', items)
        else:
            self.RefreshTextScrollList(self.ctrl['layer2'], 'layer2', [])
            self.data['layer2'] = None

        if self.data['layer1'] and self.data['layer2']:
            layer = nerve.Layer(self.data['layer1'] + '/' + self.data['layer2'])

            cmds.intFieldGrp(self.ctrl['layerFrameRange'], e=True, enable=True)
            if layer.HasFrameRange():
                cmds.intFieldGrp(self.ctrl['layerFrameRange'], e=True, v1=layer.GetFrameRange()[0], v2=layer.GetFrameRange()[1])

            cmds.scrollField(self.ctrl['layerDescription'], e=True, enable=True, text='')
            if layer.HasDescription():
                cmds.scrollField(self.ctrl['layerDescription'], e=True, text=layer.GetDescription())

            cmds.button(self.ctrl['layerSave'], e=True, enable=True)
        else:
            min = cmds.playbackOptions(q=True, min=True)
            max = cmds.playbackOptions(q=True, max=True)

            cmds.scrollField(self.ctrl['layerDescription'], e=True, enable=False, text='')
            cmds.intFieldGrp(self.ctrl['layerFrameRange'], e=True, enable=False, v1=min, v2=max)
            cmds.button(self.ctrl['layerSave'], e=True, enable=False)

        self.SublayerBaseRefresh('Sequences', mode)

    def SequencesSave(self, *args):
        frameRange = tuple(cmds.intFieldGrp(self.ctrl['layerFrameRange'], q=True, v=True))
        desc = cmds.scrollField(self.ctrl['layerDescription'], q=True, text=True)
        layer = nerve.Layer(self.data['layer1'] + '/' + self.data['layer2'], frameRange=frameRange, description=desc)
        layer.Create()

    def SequencesRelease(self, *args):
        layerpath = self.data['layer1'] or ''
        layerpath+= self.data['layer2'] or ''

        if layerpath == '':
            print("LAYER IS JOB")

        path = self.data['asset1']
        if path == '<new>':
            result = Dialog.Input('Enter Group', 'Sublayer Group')
            if not result:
                return False
            path = result

        if self.data['asset2']:
            if self.data['asset2'] == '<new>':
                result = Dialog.Input('Enter Name', 'Sublayer Name')
                if not result:
                    return False
                path+= '/'+result
            else:
                path+= '/'+self.data['asset2']

        if self.data['asset3'] == '<next>':
            version = 0
        else:
            version = nerve.versionAsInt(self.data['asset3'])

        formats = nerve.maya.GetFormats(invert=True)
        format = formats[self.data['asset4']]
        description = self.data['description']

        sublayer = nerve.Sublayer(path, version=version, format=format, description=description, layer=layerpath)
        nerve.maya.ReleaseUI(sublayer.GetFilePath('session'))
        sublayer.Create()

        self.refresh()

    def SequencesGather(self, *args):
        pass

    # Dailies
    def DailiesLayout(self):
        #self.frameLayout(label='Sequences')
        if True:
            cmds.columnLayout()
            if True:
                cmds.rowLayout(numberOfColumns=2, columnAlign2=['left', 'left'])
                if True:
                    cmds.text('Sequence', width=self.GetWidth(2)-3)
                    cmds.text('Shot', width=self.GetWidth(2)-3)
                cmds.setParent('..')

                cmds.rowLayout(numberOfColumns=2)
                if True:
                    self.ctrl['dailySeq'] = self.textScrollList(width=self.GetWidth(2)-3, selectCommand=self.refresh)
                    cmds.textScrollList(self.ctrl['dailySeq'], e=True, deleteKeyCommand=partial(self.ClearSelection, self.ctrl['dailySeq']))
                    self.ctrl['dailyShot'] = self.textScrollList(width=self.GetWidth(2)-3, allowMultiSelection=True, selectCommand=self.refresh)
                    cmds.textScrollList(self.ctrl['dailyShot'], e=True, deleteKeyCommand=partial(self.ClearSelection, self.ctrl['dailyShot']))
                cmds.setParent('..')
            cmds.setParent('..')
        #cmds.setParent('..')

    def DailiesRefresh(self):
        layer = nerve.Layer()
        items = layer.GetChildren()
        self.data['dailySeq'] = self.RefreshTextScrollList(self.ctrl['dailySeq'], 'dailySeq', items)

        if self.data['dailySeq']:
            layer = nerve.Layer(self.data['dailySeq'])
            items = layer.GetChildren()
            currentItems = cmds.textScrollList(self.ctrl['dailyShot'], q=True, allItems=True) or []
            for item in items:
                if item not in currentItems:
                    cmds.textScrollList(self.ctrl['dailyShot'], e=True, append=item)
            self.data['dailyShot'] = []
        else:
            cmds.textScrollList(self.ctrl['dailyShot'], e=True, removeAll=True)

    # OLD
    def refresh_layers(self, *args):
        mainTab = cmds.tabLayout(self.ctrl['mainTabs'], q=True, selectTabIndex=True)

        # Layers Tab
        if mainTab == 2:
            sublayerMode = cmds.tabLayout(self.ctrl['sublayerTabLayout'], q=True, selectTabIndex=True)

            # Layers
            if True:
                # Sequence
                self.data['seq'] = self.RefreshTextScrollList(self.ctrl['layer1'], nerve.Layer().GetChildren())

                # Shot
                if self.data['seq']:
                        self.data['shot'] = self.RefreshTextScrollList(self.ctrl['layer2'], nerve.Layer(self.data['seq']).GetChildren())
                else:
                    cmds.textScrollList(self.ctrl['layer2'], e=True, removeAll=True)
                    self.data['shot'] = None

                # Metadata
                if self.data['shot']:
                    layer = nerve.Layer( self.data['seq'] + '/' + self.data['shot'] )
                    frameRange = layer.GetFrameRange() if layer.HasFrameRange() else (0,0)
                    description = layer.GetDescription() if layer.HasDescription() else ''

                    cmds.floatField(self.ctrl['layerStartFrame'], e=True, enable=True, value=frameRange[0])
                    cmds.floatField(self.ctrl['layerEndFrame'], e=True, enable=True, value=frameRange[1])
                    cmds.textField(self.ctrl['description'], e=True, enable=True, text=description, editable=True, bgc=self.config['colors']['default'])
                    cmds.button(self.ctrl['saveLayer'], e=True, enable=True)
                else:
                    cmds.floatField(self.ctrl['layerStartFrame'], e=True, enable=False, value=0)
                    cmds.floatField(self.ctrl['layerEndFrame'], e=True, enable=False, value=0)
                    cmds.textField(self.ctrl['description'], e=True, text='', editable=False, bgc=self.config['colors']['inactive'])
                    cmds.button(self.ctrl['saveLayer'], e=True, enable=False)

            # Sublayers
            if True:
                # Sublayer
                if self.data['shot']:
                    layer = nerve.Layer( self.data['seq']+'/'+self.data['shot'] )
                    items = layer.GetSublayers()
                    if sublayerMode == 1:
                        items.append('<new>')
                    self.data['sublayer'] = self.RefreshTextScrollList(self.ctrl['sublayer1'], items)
                else:
                    cmds.textScrollList(self.ctrl['sublayer1'], e=True, removeAll=True)
                    self.data['sublayer'] = None

                # Version
                if self.data['sublayer']:
                    sublayer = nerve.Sublayer( self.data['sublayer'], layer=self.data['seq']+'/'+self.data['shot'] )
                    items = sublayer.GetVersionsAsString()
                    if sublayerMode == 1:
                        items.append('<new>')
                    self.data['version'] = self.RefreshTextScrollList(self.ctrl['sublayer2'], items)
                else:
                    cmds.textScrollList(self.ctrl['sublayer2'], e=True, removeAll=True)
                    self.data['version'] = None

                # Format
                if self.data['sublayer'] and self.data['version']:
                    version = int(self.data['version'][1:]) if self.data['version'] != '<new>' else 0
                    sublayer = nerve.Sublayer( self.data['sublayer'], layer=self.data['seq']+'/'+self.data['shot'], version=version )
                    allFormats = nerve.maya.GetFormats()
                    if sublayerMode == 1:
                        formats = allFormats.values()
                    else:
                        sublayerFormats = sublayer.GetFormats()
                        formats = [ val for key,val in allFormats.items() if key in sublayerFormats ]
                    self.data['format'] = self.RefreshTextScrollList(self.ctrl['sublayer3'], formats)
                else:
                    cmds.textScrollList(self.ctrl['sublayer3'], e=True, removeAll=True)
                    self.data['format'] = None

                if self.data['sublayer'] and self.data['version'] and self.data['format']:
                    cmds.button(self.ctrl['sublayerReleaseBtn'], e=True, enable=True)
                else:
                    cmds.button(self.ctrl['sublayerReleaseBtn'], e=True, enable=False)

    def ClearSelection(self, *args):
        ctrl = args[0]
        cmds.textScrollList(ctrl, e=True, removeAll=True)
        self.refresh()

    def Sublayer_Layout(self, prefix):
        # Sublayers
        self.frameLayout(label=(prefix+'s').capitalize())
        if True:
            cmds.columnLayout()
            if True:
                cmds.rowLayout(numberOfColumns=3)
                if True:
                    self.ctrl[prefix+'1'] = self.textScrollList(width=self.GetWidth(3)-1, selectCommand=self.refresh)
                    self.ctrl[prefix+'2'] = self.textScrollList(width=self.GetWidth(3)-1, selectCommand=self.refresh)
                    self.ctrl[prefix+'3'] = self.textScrollList(width=self.GetWidth(3)-2, selectCommand=self.refresh)
                cmds.setParent('..')

                self.ctrl[prefix+'TabLayout'] = cmds.tabLayout(width=590, selectCommand=self.refresh)
                if True:
                    self.ctrl[prefix+'ReleaseLayout'] = cmds.frameLayout(labelVisible=False)
                    if True: # Release
                        cmds.columnLayout()
                        if True:
                            self.ctrl[prefix+'ReleaseBtn'] = cmds.button(label='Release', width=self.config['width']-10, height=50, command=self.ReleaseSublayer)
                        cmds.setParent('..')
                    cmds.setParent('..')

                    self.ctrl[prefix+'GatherLayout'] = cmds.frameLayout(labelVisible=False)
                    if True: # Gather
                        cmds.columnLayout()
                        if True:
                            pass
                        cmds.setParent('..')
                    cmds.setParent('..')
                cmds.setParent('..')
                cmds.tabLayout(self.ctrl[prefix+'TabLayout'], e=True, tabLabel=[(self.ctrl[prefix+'ReleaseLayout'], 'Release'), (self.ctrl[prefix+'GatherLayout'], 'Gather')])
            cmds.setParent('..')
        cmds.setParent('..')

    def Layers_Layout(self):
        # Layers
        self.frameLayout(label='Sequences')
        if True: # Layers frameLayout
            cmds.columnLayout()
            if True: # Layers columnLayout
                cmds.rowLayout(numberOfColumns=2)
                if True:
                    cmds.columnLayout()
                    if True:
                        cmds.intFieldGrp(label='Frame Range', numberOfFields=2)
                    cmds.setParent('..')
                    #self.ctrl['layer1'] = self.textScrollList(width=self.GetWidth(3), selectCommand=self.refresh)
                    #self.ctrl['layer2'] = self.textScrollList(width=self.GetWidth(3), selectCommand=self.refresh)
                    cmds.columnLayout()
                    if True:
                        self.ctrl['layer3'] = cmds.iconTextButton(image='render_swColorPerVertex.png', backgroundColor=[0.22,0.22,0.22])
                    cmds.setParent('..')
                cmds.setParent('..')
            cmds.setParent('..') # Layers columnLayout

            #self.frameLayout(label='Metadata')
            if True: # Metadata
                cmds.rowLayout(numberOfColumns=1)
                if True:
                    self.Metadata_Layout()
                cmds.setParent('..')
            #cmds.setParent('..')
        cmds.setParent('..') # Layers frameLayout


        self.Sublayer_Layout('sublayer')

    def Metadata_Layout(self):
        #layout = self.frameLayout(label='Metadata', collapsable=False)
        if True: # Metadata Layout
            cmds.columnLayout()
            if True: # Metadata Column Layout
                self.rowLayout(numberOfColumns=1)
                if True:
                    cmds.text(label='Frame Range')
                cmds.setParent('..')

                cmds.rowLayout(numberOfColumns=2, columnAttach=[(1, 'left', 0), (2, 'left', 0)])
                if True:
                    self.ctrl['layerStartFrame'] = cmds.floatField(precision=0)
                    self.ctrl['layerEndFrame'] = cmds.floatField(precision=0)
                cmds.setParent('..')

                self.rowLayout(numberOfColumns=1, columnAttach=[1, 'left', 0])
                if True:
                    cmds.text(label='Description')
                cmds.setParent('..')
                self.rowLayout(numberOfColumns=1)
                if True:
                    self.ctrl['description'] = cmds.textField( width=self.GetWidth(3)*2, editable=True, enableBackground=True)
                    #self.ctrl['description'] = cmds.textField()
                cmds.setParent('..')

                self.rowLayout(numberOfColumns=1)
                if True:
                    self.ctrl['saveLayer'] = cmds.button(label='Save', height=30, width=self.GetWidth(3)*2, command=self.UpdateMetadata)
                cmds.setParent('..')
            cmds.setParent('..') # Metadata Column Layout

    def UpdateMetadata(self, *args):
        startFrame = cmds.floatField(self.ctrl['layerStartFrame'], q=True, v=True)
        endFrame = cmds.floatField(self.ctrl['layerEndFrame'], q=True, v=True)
        description = cmds.textField(self.ctrl['description'], q=True, text=True)

        layer = nerve.Layer( self.data['seq']+'/'+self.data['shot'], frameRange=(startFrame, endFrame), description=description)
        layer.Create()
        Dialog.Confirm('Layer Metadata Updated')

    def RefreshTextScrollList(self, ctrl, key, items, highlight=[]):
        prevsel = self.data[key] if key in self.data.keys() else None

        sel = (cmds.textScrollList(ctrl, q=True, selectItem=True) or [None])[0]
        cmds.textScrollList(ctrl, e=True, removeAll=True)
        c = 1
        for item in items:
            if item in highlight:
                cmds.textScrollList(ctrl, e=True, append=item, lineFont=[c, 'boldLabelFont'])
            else:
                cmds.textScrollList(ctrl, e=True, append=item)
            c+=1

        if sel and sel in items :
            cmds.textScrollList(ctrl, e=True, selectItem=sel)
        return (cmds.textScrollList(ctrl, q=True, selectItem=True) or [None])[0]

    def ReleaseSublayer(self, *args):
        version = int(self.data['version'][1:]) if self.data['version'] != '<new>' else 0
        sublayer = nerve.Sublayer(self.data['sublayer'], layer=self.data['seq'] + '/' + self.data['shot'], version=version, format=self.data['format'])
