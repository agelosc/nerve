#from importlib import reload
import os, sys
import nerve

import nerve.maya
reload(nerve.maya)

import maya.cmds as cmds


def All():
    Alembic()
    OBJ()
    MayaBinary()
    MayaAscii()
    FBX()
    RedshiftProxy()
    Assets()

def Alembic():
    # New Scene
    cmds.file(new=True, f=True)
    # Create Cube
    cube = cmds.polyCube()
    cmds.select(cube[0], r=True)
    # Cube Sublayer
    cubeSublayer = nerve.Sublayer('cube', format='abc', version=1)
    nerve.maya.Release(cubeSublayer.GetFilePath('session'))
    cubeSublayer.Create()

    # Create Sphere
    cmds.file(new=True, f=True)
    sphere = cmds.polySphere()
    cmds.select(sphere[0], r=True)

    # Sphere Sublayer
    sphereSublayer = nerve.Sublayer('sphere', format='abc', version=1)
    nerve.maya.Release(sphereSublayer.GetFilePath('session'))
    sphereSublayer.Create()

    # Import
    cmds.file(new=True, f=True)
    assert cubeSublayer.GetFilePath('session').Exists() is True
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'import')
    assert cmds.objExists(cube[0]) is True

    # Replace From Import
    cmds.select(cube[0], r=True)
    nerve.maya.Gather(sphereSublayer.GetFilePath('session'), 'replace')
    assert cmds.objExists(sphere[0]) is True

    # Reference
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'reference')
    assert cmds.objExists('cube:'+cube[0]) is True

    cmds.select('cube:'+cube[0], r=True)
    nerve.maya.Gather(sphereSublayer.GetFilePath('session'), 'replace')
    assert cmds.objExists('cube:'+sphere[0]) is True

    # Export Animation
    cmds.file(new=True, f=True)
    cube = cmds.polyCube()
    cmds.setKeyframe(cube[0]+'.ty')
    cmds.currentTime(10, u=True)
    cmds.setAttr(cube[0]+'.ty', 5)
    cmds.setKeyframe(cube[0]+'.ty')

    cubeSublayer = nerve.Sublayer('cube', format='abc', version=2, frameRange=(1, 10))
    nerve.maya.Release(cubeSublayer.GetFilePath('session'), frameRange=(1,10))

    # Import Animation
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'import')

    cmds.currentTime(1, u=True)
    assert cmds.getAttr(cube[0] + '.ty') == 0
    cmds.currentTime(10, u=True)
    assert cmds.getAttr(cube[0] + '.ty') == 5

    # Reference Animation
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'reference')

    cmds.currentTime(1, u=True)
    assert cmds.getAttr('cube:'+cube[0] + '.ty') == 0
    cmds.currentTime(10, u=True)
    assert cmds.getAttr('cube:'+cube[0] + '.ty') == 5

    # Export deformation animation
    cmds.file(new=True, f=True)
    plane = cmds.polyPlane(w=1, h=1, sx=2, sy=1, ax=(0,1,0))
    bend = cmds.nonLinear(type='bend')
    cmds.setAttr(bend[1]+'.rz', -90)
    cmds.setKeyframe(bend[0] + '.curvature', v=0, t=1)
    cmds.setKeyframe(bend[0] + '.curvature', v=-90, t=10)

    planeSublayer = nerve.Sublayer('plane', format='abc', version=1, frameRange=(1, 10))
    cmds.select(plane[0], r=True)
    nerve.maya.Release(planeSublayer.GetFilePath('session'), frameRange=(1,10))
    planeSublayer.Create()

    # Import deformation animation
    cmds.file(new=True, f=True)
    nerve.maya.Gather(planeSublayer.GetFilePath('session'), 'import')
    cmds.currentTime(1, u=True)
    pos = cmds.xform(plane[0]+'.vtx[0]', q=True, ws=True, t=True)
    assert int(pos[0]*1000) == -500
    cmds.currentTime(10, u=True)
    pos = cmds.xform(plane[0]+'.vtx[0]', q=True, ws=True, t=True)
    assert int(pos[0]*1000) == -318

    print('##############################')
    print('## Passed All Alembic Tests ##')
    print('##############################')

def OBJ():
    # Create Cube Sublayer
    cmds.file(new=True, f=True)

    cube = cmds.polyCube()
    cmds.select(cube[0], r=True)

    cubeSublayer = nerve.Sublayer('cube', format='obj', version=1)
    nerve.maya.Release(cubeSublayer.GetFilePath('session'))
    cubeSublayer.Create()

    # Create Sphere Sublayer
    cmds.file(new=True, f=True)
    sphere = cmds.polySphere()
    cmds.select(sphere[0], r=True)

    sphereSublayer = nerve.Sublayer('sphere', format='obj', version=1)
    nerve.maya.Release(sphereSublayer.GetFilePath('session'))
    sphereSublayer.Create()

    # Import
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'import')
    assert cmds.objExists(cube[0]) is True

    # Reference
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'reference')
    assert cmds.objExists('cube:'+cube[0]) is True

    # Replace Reference
    cmds.select('cube:'+cube[0], r=True)
    nerve.maya.Gather(sphereSublayer.GetFilePath('session'), 'replace')
    assert cmds.objExists('cube:'+sphere[0]) is True

    print('##########################')
    print('## Passed All OBJ Tests ##')
    print('##########################')

def MayaBinary():
    # Create Cube Sublayer
    cmds.file(new=True, f=True)

    cube = cmds.polyCube()
    cmds.select(cube[0], r=True)

    cubeSublayer = nerve.Sublayer('cube', format='mb', version=1)
    nerve.maya.Release(cubeSublayer.GetFilePath('session'))
    cubeSublayer.Create()

    # Create Sphere Sublayer
    cmds.file(new=True, f=True)
    sphere = cmds.polySphere()
    cmds.select(sphere[0], r=True)

    sphereSublayer = nerve.Sublayer('sphere', format='mb', version=1)
    nerve.maya.Release(sphereSublayer.GetFilePath('session'))
    sphereSublayer.Create()

    # Import
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'import')
    assert cmds.objExists(cube[0]) is True

    # Reference
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'reference')
    assert cmds.objExists('cube:'+cube[0]) is True

    # Replace Reference
    cmds.select('cube:'+cube[0], r=True)
    nerve.maya.Gather(sphereSublayer.GetFilePath('session'), 'replace')
    assert cmds.objExists('cube:'+sphere[0]) is True

    print('#################################')
    print('## Passed All MayaBinary Tests ##')
    print('#################################')

def MayaAscii():
    # Create Cube Sublayer
    cmds.file(new=True, f=True)

    cube = cmds.polyCube()
    cmds.select(cube[0], r=True)

    cubeSublayer = nerve.Sublayer('cube', format='ma', version=1)
    nerve.maya.Release(cubeSublayer.GetFilePath('session'))
    cubeSublayer.Create()

    # Create Sphere Sublayer
    cmds.file(new=True, f=True)
    sphere = cmds.polySphere()
    cmds.select(sphere[0], r=True)

    sphereSublayer = nerve.Sublayer('sphere', format='ma', version=1)
    nerve.maya.Release(sphereSublayer.GetFilePath('session'))
    sphereSublayer.Create()

    # Import
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'import')
    assert cmds.objExists(cube[0]) is True

    # Reference
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'reference')
    assert cmds.objExists('cube:'+cube[0]) is True

    # Replace Reference
    cmds.select('cube:'+cube[0], r=True)
    nerve.maya.Gather(sphereSublayer.GetFilePath('session'), 'replace')
    assert cmds.objExists('cube:'+sphere[0]) is True

    print('################################')
    print('## Passed All MayaAscii Tests ##')
    print('################################')

def FBX():
    # Create Cube Sublayer
    cmds.file(new=True, f=True)

    cube = cmds.polyCube()
    cmds.select(cube[0], r=True)

    cubeSublayer = nerve.Sublayer('cube', format='fbx', version=1)
    nerve.maya.Release(cubeSublayer.GetFilePath('session'))
    cubeSublayer.Create()

    # Create Sphere Sublayer
    cmds.file(new=True, f=True)
    sphere = cmds.polySphere()
    cmds.select(sphere[0], r=True)

    sphereSublayer = nerve.Sublayer('sphere', format='fbx', version=1)
    nerve.maya.Release(sphereSublayer.GetFilePath('session'))
    sphereSublayer.Create()

    # Import
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'import')
    assert cmds.objExists(cube[0]) is True

    # Reference
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'reference')
    assert cmds.objExists('cube:'+cube[0]) is True

    # Replace Reference
    cmds.select('cube:'+cube[0], r=True)
    nerve.maya.Gather(sphereSublayer.GetFilePath('session'), 'replace')
    assert cmds.objExists('cube:'+sphere[0]) is True

    # Export Keyframe Animation
    cmds.file(new=True, f=True)
    cube = cmds.polyCube()
    cmds.setKeyframe(cube[0]+'.ty')
    cmds.currentTime(10, u=True)
    cmds.setAttr(cube[0]+'.ty', 5)
    cmds.setKeyframe(cube[0]+'.ty')

    cubeSublayer = nerve.Sublayer('cube', format='fbx', version=2, frameRange=(1, 10))
    nerve.maya.Release(cubeSublayer.GetFilePath('session'), frameRange=(1,10))

    # Import Animation
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'import')

    cmds.currentTime(1, u=True)
    assert cmds.getAttr(cube[0] + '.ty') == 0
    cmds.currentTime(10, u=True)
    assert cmds.getAttr(cube[0] + '.ty') == 5

    # Reference Animation
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'reference')

    cmds.currentTime(1, u=True)
    assert cmds.getAttr('cube:'+cube[0] + '.ty') == 0
    cmds.currentTime(10, u=True)
    assert cmds.getAttr('cube:'+cube[0] + '.ty') == 5

    print('##########################')
    print('## Passed All FBX Tests ##')
    print('##########################')

def RedshiftProxy():

    cmds.file(new=True, f=True)

    # Create Cube Sublayer
    cube = cmds.polyCube()
    cmds.select(cube[0], r=True)
    cubeSublayer = nerve.Sublayer('cube', format='rs', version=1)
    nerve.maya.Release(cubeSublayer.GetFilePath('session'))
    cubeSublayer.Create()

    # Create Sphere Sublayer
    cmds.file(new=True, f=True)
    sphere = cmds.polySphere()
    cmds.select(sphere[0], r=True)
    sphereSublayer = nerve.Sublayer('sphere', format='rs', version=1)
    nerve.maya.Release(sphereSublayer.GetFilePath('session'))
    sphereSublayer.Create()

    # Import
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'import')
    assert cmds.polyEvaluate('cube', v=True) == 36

    # Replace From Import
    cmds.select('cube', r=True)
    nerve.maya.Gather(sphereSublayer.GetFilePath('session'), 'replace')
    assert cmds.polyEvaluate('cube', v=True) == 2280

    # Animation
    cmds.file(new=True, f=True)
    cube = cmds.polyCube()
    cmds.setKeyframe(cube[0]+'.ty', v=0, t=1)
    cmds.setKeyframe(cube[0]+'.ty', v=5, t=10)

    cubeSublayer = nerve.Sublayer('cube', format='rs', version=2)
    nerve.maya.Release(cubeSublayer.GetFilePath('session'), frameRange=(1,10))
    cubeSublayer.Create()


    output = r'####################################\n'
    output+= r'## Passed All RedshiftPRoxy Tests ##\n'
    output+= r'####################################\n'

    cmds.evalDeferred('print("{}");'.format(output) )

def USD():
    cmds.file(new=True, f=True)

    # Create Cube Sublayer
    cube = cmds.polyCube()
    cmds.select(cube[0], r=True)
    cubeSublayer = nerve.Sublayer('cube', format='usda', version=1)
    nerve.maya.Release(cubeSublayer.GetFilePath('session'))
    cubeSublayer.Create()

    # Create Sphere Sublayer
    cmds.file(new=True, f=True)
    sphere = cmds.polySphere()
    cmds.select(sphere[0], r=True)
    sphereSublayer = nerve.Sublayer('sphere', format='usda', version=1)
    nerve.maya.Release(sphereSublayer.GetFilePath('session'))
    sphereSublayer.Create()

    # Import Cube Sublayer
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'import')
    assert cmds.objExists('pCube1')

    # Reference Cube Sublayer
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'reference')
    assert cmds.objExists(''+cube[0]) is True

    # Replace Sphere Sublayer
    cmds.select('pCube1', r=True)
    print(sphereSublayer.GetFilePath('session'))
    nerve.maya.Gather(sphereSublayer.GetFilePath('session'), 'replace')
    assert cmds.objExists(''+sphere[0]) is True

    # Animation Single
    cmds.file(new=True, f=True)
    cube = cmds.polyCube()
    cmds.setKeyframe(cube[0], at='ty', t=1, v=0)
    cmds.setKeyframe(cube[0], at='ty', t=10, v=5)
    cmds.select(cube[0], r=True)
    cubeSublayer = nerve.Sublayer('cubeAmim', format='usda', version=1)
    nerve.maya.Release(cubeSublayer.GetFilePath('session'), frameRange=(1,10))
    cubeSublayer.Create()

    # Import Single Animation
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'import')
    assert cmds.objExists(cube[0]) is True
    cmds.currentTime(1, u=True)
    assert cmds.getAttr(cube[0] + '.ty') == 0
    cmds.currentTime(10, u=True)
    assert cmds.getAttr(cube[0] + '.ty') == 5

    # Reference Single Animation
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'reference')
    assert cmds.objExists(cube[0]) is True
    cmds.currentTime(1, u=True)
    assert cmds.getAttr(cube[0] + '.ty') == 0
    cmds.currentTime(10, u=True)
    assert cmds.getAttr(cube[0] + '.ty') == 5

    '''
    # Animation FilePerFrame
    cmds.file(new=True, f=True)
    sphere = cmds.polySphere()
    cmds.setKeyframe(sphere[0], at='ty', t=1, v=0)
    cmds.setKeyframe(sphere[0], at='ty', t=10, v=5)
    cmds.select(sphere[0], r=True)
    sphereSublayer = nerve.Sublayer('sphereAnim', format='usda', version=1, frameRange=(1,10))
    nerve.maya.Release(sphereSublayer.GetFilePath('session'), frameRange=(1,10), filePerFrame=True)
    sphereSublayer.Create()

    # Import FilePerFrame Animation
    cmds.file(new=True, f=True)
    nerve.maya.Gather(sphereSublayer.GetFilePath('session'), 'import')
    assert cmds.objExists(sphere[0]) is True
    #cmds.currentTime(1, u=True)
    #assert cmds.getAttr(sphere[0] + '.ty') == 0
    #cmds.currentTime(10, u=True)
    #assert cmds.getAttr(sphere[0] + '.ty') == 5
    '''

    output = r'##########################\n'
    output+= r'## Passed All USD Tests ##\n'
    output+= r'##########################\n'

    cmds.evalDeferred('print("{}");'.format(output) )

def Assets():
    cmds.file(new=True, f=True)

    # Create Cube Sublayer
    cube = cmds.polyCube()
    cmds.select(cube[0], r=True)
    cubeAsset = nerve.Asset('cube', format='usda', version=1, description="TEST")
    nerve.maya.Release(cubeAsset.GetFilePath('session'))
    cubeAsset.Create()

    cubeAsset = nerve.Asset('cube', format='usda', version=2, description="TEST")
    nerve.maya.Release(cubeAsset.GetFilePath('session'))
    cubeAsset.Create()

    cubeAsset = nerve.Asset('cube', format='abc', version=2, description="TEST")
    nerve.maya.Release(cubeAsset.GetFilePath('session'))
    cubeAsset.Create()

    # Create Cube Sublayer with parent
    cmds.select(cube[0], r=True)
    cubeAsset = nerve.Asset('group/cube', format='usda', version=1, description="TEST")
    nerve.maya.Release(cubeAsset.GetFilePath('session'))
    cubeAsset.Create()

    # Create Cube Sublayer with parent
    cmds.select(cube[0], r=True)
    cubeAsset = nerve.Asset('cube/sphere', format='usda', version=1, description="TEST")
    nerve.maya.Release(cubeAsset.GetFilePath('session'))
    cubeAsset.Create()


    # Create Sphere Sublayer
    cmds.file(new=True, f=True)
    sphere = cmds.polySphere()
    cmds.select(sphere[0], r=True)
    sphereAsset = nerve.Sublayer('sphere', format='usda', version=1)
    nerve.maya.Release(sphereAsset.GetFilePath('session'))
    sphereAsset.Create()

    # Import Cube Sublayer
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeAsset.GetFilePath('session'), 'import')
    assert cmds.objExists('pCube1')

    # Reference Cube Sublayer
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeAsset.GetFilePath('session'), 'reference')
    assert cmds.objExists(''+cube[0]) is True

    # Replace Sphere Sublayer
    cmds.select('pCube1', r=True)
    print(sphereAsset.GetFilePath('session'))
    nerve.maya.Gather(sphereAsset.GetFilePath('session'), 'replace')
    assert cmds.objExists(''+sphere[0]) is True

    # Animation Single
    cmds.file(new=True, f=True)
    cube = cmds.polyCube()
    cmds.setKeyframe(cube[0], at='ty', t=1, v=0)
    cmds.setKeyframe(cube[0], at='ty', t=10, v=5)
    cmds.select(cube[0], r=True)
    cubeSublayer = nerve.Sublayer('cubeAmim', format='usda', version=1)
    nerve.maya.Release(cubeSublayer.GetFilePath('session'), frameRange=(1,10))
    cubeSublayer.Create()

    # Import Single Animation
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'import')
    assert cmds.objExists(cube[0]) is True
    cmds.currentTime(1, u=True)
    assert cmds.getAttr(cube[0] + '.ty') == 0
    cmds.currentTime(10, u=True)
    assert cmds.getAttr(cube[0] + '.ty') == 5

    # Reference Single Animation
    cmds.file(new=True, f=True)
    nerve.maya.Gather(cubeSublayer.GetFilePath('session'), 'reference')
    assert cmds.objExists(cube[0]) is True
    cmds.currentTime(1, u=True)
    assert cmds.getAttr(cube[0] + '.ty') == 0
    cmds.currentTime(10, u=True)
    assert cmds.getAttr(cube[0] + '.ty') == 5

    # Animation FilePerFrame
    cmds.file(new=True, f=True)
    sphere = cmds.polySphere()
    cmds.setKeyframe(sphere[0], at='ty', t=1, v=0)
    cmds.setKeyframe(sphere[0], at='ty', t=10, v=5)
    cmds.select(sphere[0], r=True)
    sphereSublayer = nerve.Sublayer('sphereAnim', format='usda', version=1, frameRange=(1,10))
    nerve.maya.Release(sphereSublayer.GetFilePath('session'), frameRange=(1,10), filePerFrame=True)
    sphereSublayer.Create()

    # Import FilePerFrame Animation
    cmds.file(new=True, f=True)
    nerve.maya.Gather(sphereSublayer.GetFilePath('session'), 'import')
    assert cmds.objExists(sphere[0]) is True
    #cmds.currentTime(1, u=True)
    #assert cmds.getAttr(sphere[0] + '.ty') == 0
    #cmds.currentTime(10, u=True)
    #assert cmds.getAttr(sphere[0] + '.ty') == 5

    output = r'##########################\n'
    output+= r'## Passed All USD Tests ##\n'
    output+= r'##########################\n'

    cmds.evalDeferred('print("{}");'.format(output) )
