# Maya
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as mu

import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI

# Nerve#
import nerve5 as nerve

# Other
import os
import json

print "NERVE::Initialising..."
mu.executeDeferred('gNerve = nerve5.maya.deferred();')

def deferred():
    gMainWindow = mel.eval('global string $gMainWindow; $temp1=$gMainWindow;')
    if gMainWindow != '':
        print "NERVE::Loading UI..."

        import UI
        UI.menu()

        '''
        import lego
        lego.menu()
        '''


def getToolPaths(r=False):
    def getSubPaths(path):
        paths = []
        filenames = os.listdir(path)
        for filename in filenames:
            if os.path.isdir(path + '/' + filename):
                paths.append( path + '/' + filename )
                paths.extend( getSubPaths( path + '/' + filename ) )

        return paths

    # Get Paths
    workspace = cmds.workspace(q=True, rootDirectory=True )
    job = '/'.join( workspace.split('/')[:-4] )
    seq = workspace.split('/')[-4]
    sho = workspace.split('/')[-3]

    paths = []
    tmp = workspace + 'scripts'
    if os.path.exists( tmp ):
        paths.append(tmp)
        if r:
            paths.extend( getSubPaths(tmp) )

    if sho != 'build':
        tmp = job + '/' + seq + '/build/maya/scripts'
        if os.path.exists( tmp ):
            paths.append( tmp )
            if r:
                paths.extend( getSubPaths(tmp) )

    if seq != 'build':
        tmp = job + '/build/build/maya/scripts'
        if os.path.exists(tmp):
            paths.append( tmp )
            if r:
                paths.extend( getSubPaths(tmp) )

    return paths

def error(msg):
    cmds.confirmDialog(title="Error", message=msg, button=['OK'], defaultButton='OK')

def confirm(msg, title=''):
    cmds.confirmDialog(title=title, message=msg, button=['OK'], defaultButton='OK')

def activeCamera(fullPath=False):
    view = OpenMayaUI.M3dView.active3dView()
    cam = OpenMaya.MDagPath()
    view.getCamera(cam)
    camPath = cam.fullPathName()

    if fullPath is True:
        return camPath
    else:
        return camPath.split('|')[-1]

# Paths

def pathFromArgs(data):
    path = nerve.cfg.path("job")

    if 'job' not in data.keys() or 'seq' not in data.keys() or 'shot' not in data.keys():
        nerve.error('ey error, pathFromArgs()')

    path+= data["job"] + '/'
    path+= data["seq"] + '/'
    path+= data["shot"] + '/'

    return path

def projPath():
    return cmds.workspace(q=True, rootDirectory=True).replace('maya/', '')

def configPath():
    return projPath() + '/config'

def mayaPath():
    return projPath() + '/maya'

def assetPath():
    return projPath() + '/assets'

def playblast(filename, width=None, height=None, sound=False):

    # RVIO
    rviopaths = ["C:/Program Files/Shotgun/RV-7.1.1/bin/rvio_hw.exe", "D:/Program Files/Shotgun/RV-7.1.1/bin/rvio_hw.exe"]
    rvio = None
    for rviopath in rviopaths:
        if os.path.isfile(rviopath):
            rvio = rviopath

    if width is None:
        width = cmds.getAttr("defaultResolution.width")
    if height is None:
        height = cmds.getAttr("defaultResolution.height")

    gPlayBackSlider = mel.eval( '$tmpVar=$gPlayBackSlider' )
    sound = cmds.timeControl( gPlayBackSlider, q=True, sound=True )

    args = {}
    if sound != '':
        args["sound"] = sound
    args["percent"] = 100

    args["wh"] = [ width, height ]
    args["offScreen"] = 1
    args["quality"] = 100
    args["forceOverwrite"] = True
    args["viewer"] = False

    if rvio is None or sound:
        args["filename"] = filename
        try:
            args['sound'] = cmds.ls(type='audio')[0]
        except:
            pass

        args["format"] = "qt"
        args["compression"] = "H.264"

        return cmds.playblast( **args )
    else:
        tmppath = os.environ["TEMP"] + "/dailies/"
        args["filename"] = tmppath + "daily"
        args["format"] = "image"
        args["compression"] = "jpg"
        fileseq = cmds.playblast( **args )

        if fileseq is None:
            return None

        cmd = '"%s" "%s" -o "%s" -fps 24'%(rvio, fileseq, filename)
        print cmd
        batfilepath = tmppath + "daily.bat"
        batfile = open(batfilepath, 'w')
        batfile.write(cmd)
        batfile.close()
        os.system( '"%s"'%batfilepath )

        import shutil
        shutil.rmtree(tmppath)

        return filename


def save( objects, path, recursive=False ):

    if objects is None or not len(objects):
        cmds.error('No objects defined for saving...')
        return False

    data = []
    for object in objects:
        data.append( node( object, recursive ) )

    with open(path, 'w') as outfile:
        json.dump( data, outfile )

    print 'File saved...',
    return True

def load(path):

    # Functions [START]
    def getClassification(nodeType):
        classifications = ['shader', 'texture', 'light', 'geometry', 'utility', 'animation']
        for classification in classifications:
            if cmds.getClassification( nodeType, satisfies=classification ):
                return classification

    def createNode(data):

        # NAMESPACE ??

        cleanName = data['name'].split('|')[-1]
        classification = getClassification( data['type'] )

        shadingClassifications = ['shader', 'texture', 'light', 'utility']
        if classification in shadingClassifications:
            asWhat = { 'as'+classification.capitalize():True }
            data['name'] = cmds.shadingNode( data['type'], name=cleanName, **asWhat  )
        else:
            data['name'] = cmds.createNode( data['type'], name=cleanName )

        for attr in data['attributes'].keys():
            plug = data['name'] + '.' + attr

            # Get Attribute Data
            attrData = data['attributes'][attr]

            if attrData['isConnected']:
                cnode = createNode()
            else:
                simpleTypes = ['float', 'bool', 'enum', 'byte']
                vectorTypes = ['float3']
                if attrData['type'] in simpleTypes:
                    cmds.setAttr(plug, attrData['value'])
                elif attrData['type'] in vectorTypes:
                    cmds.setAttr(plug, attrData['value'][0], attrData['value'][1], attrData['value'][2])
                else:
                    print '%-40s%-40s'%( attrData['name'], attrData['type'] )

        return cleanName

    # Functions [END]

    # Get Data
    with open(path) as json_file:
        nodes = json.load(json_file)

    # Create Nodes
    for data in nodes:
        node = createNode(data)




class node(dict):
    def __init__(self, name, recursive=False):
        if not cmds.objExists(name):
            return False

        self["name"] = name
        self["type"] = cmds.nodeType(name)
        self['history'] = {}
        self["attributes"] = {}

        # Get Attributes
        attribs = cmds.listAttr( self.name, multi=True, settable=True, output=True )
        for attr in attribs:
            obj = attribute(self, attr, recursive)
            self.attributes[attr] = obj

    def __getattr__(self, attr):
        if attr in self.keys():
            return self[attr]

class attribute(dict):
    def __init__(self, parent, attr, recursive=False):
        plug = parent.name + '.' + attr

        self['name'] = attr
        self['type'] = cmds.getAttr(plug, type=True)
        self['value'] = self.getValue(plug)

        connection = cmds.listConnections( plug, s=True, d=False)
        self['isConnected'] = connection is not None
        if self.isConnected:
            self['connection'] = {}
            self['connection']['plug'] = cmds.listConnections( plug, s=True, d=False, p=True)[0]
            self['connection']['nodeName'] = connection[0]
            self['connection']['nodeType'] = cmds.nodeType(self.connection['nodeName'])
            if recursive:
                if connection[0] not in parent.history.keys():
                    parent.history[connection[0]] = node(connection[0], recursive)

    def getValue(self, plug):
        value = cmds.getAttr(plug)
        if self.type == 'float3':
            return value[0]

        return value

    def __getattr__(self, attr):
        if attr in self.keys():
            return self[attr]

        return None
