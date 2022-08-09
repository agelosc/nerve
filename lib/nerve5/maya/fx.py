import maya.cmds as cmds
import maya.mel as mel
import maya.utils as mu

from functools import partial

import nerve5 as nerve
import os

def UI():
    data = []

    data.append( {'label':'Water Surface', 'command':water} )

    return data

def water(*args):
    sel = cmds.ls(sl=True, l=True)

    p = 'houdiniEngine'
    if not cmds.pluginInfo(p, q=True, loaded=True):
        cmds.loadPlugin(p)

    node = cmds.houdiniAsset( loadAsset=('R:/software/houdini/engine/water.hda', 'Sop/water') )
    hgeo = cmds.createNode( 'houdiniInputGeometry' )

    if len(sel):
        n = sel[0]
        shape = cmds.listRelatives(n, s=True, f=True)
        if shape is None:
            return True
        cmds.connectAttr( shape[0] + '.outMesh', hgeo + '.inputGeometry', f=True )
        cmds.connectAttr( n + '.worldMatrix[0]', hgeo + '.inputTransform', f=True )
        cmds.connectAttr( hgeo + '.outputNodeId', node + '.input[0].inputNodeId', f=True )

        cmds.houdiniAsset(reloadAsset=node)
