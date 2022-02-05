import os
import unittest

try:
    from importlib import reload
except:
    pass

import nerve
reload(nerve)
import nerve.maya
reload(nerve.maya)

import maya.cmds as cmds

class MayaMaterial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def createLambert(self, name, assign=None):
        mat = cmds.shadingNode('lambert', asShader=True, name=name)
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name+'_SG')
        cmds.connectAttr(mat + '.outColor', sg + '.surfaceShader', f=True)
        if assign:
            cmds.sets(assign, e=True, forceElement=sg)
        return mat

    def test_1_simple_lambert(self):
        cmds.file(new=True, f=True)

        cube = cmds.polyCube()
        yellow = self.createLambert('lambertYellow', cube[0])
        cmds.setAttr(yellow + '.color', 1,1,0)

        red = self.createLambert('lambertRed', cube[0] + '.f[0]')
        cmds.setAttr(red + '.color', 1,0,0)

        # Release
        material = nerve.maya.Material('lambert', version=1)
        cmds.select(cube[0], r=True)
        material.Release()

        cmds.file(new=True, f=True)
        material.Gather()
        self.assertEqual( cmds.getAttr('lambertYellow.color')[0], (1.0,1.0,0.0) )
        self.assertEqual( cmds.getAttr('lambertRed.color')[0], (1.0,0.0,0.0) )

    def test_2_lambert_withTexture(self):
        cmds.file(new=True, f=True)
        cube = cmds.polyCube()

        mat = self.createLambert('lambert', cube[0])
        tex = nerve.maya.Node.CreateTexture('color')

        cmds.setAttr( tex + '.fileTextureName', 'color.jpg', type='string')
        cmds.setAttr( tex + '.colorSpace', 'ACEScg', type='string')
        cmds.setAttr( tex + '.alphaIsLuminance', True)

        uv = cmds.listConnections(tex + '.uv', type='place2dTexture')[0]
        cmds.setAttr(uv + '.repeatU', 2)
        cmds.setAttr(uv + '.repeatV', 3)
        cmds.setAttr(uv + '.offsetU', 0.5)
        cmds.setAttr(uv + '.offsetV', -0.5)
        cmds.setAttr(uv + '.rotateUV', 90)

        cmds.connectAttr(tex + '.outColor', mat + '.color', f=True)

        # Release
        material = nerve.maya.Material('lambertTex', version=1)
        cmds.select(cube[0], r=True)
        material.Release()

        cmds.file(new=True, f=True)
        material.Gather()

        self.assertEqual( cmds.getAttr(tex + '.fileTextureName'), 'color.jpg')
        self.assertEqual( cmds.getAttr(tex + '.colorSpace'), 'ACEScg')
        self.assertTrue( cmds.getAttr(tex + '.alphaIsLuminance') )
        self.assertEqual( cmds.getAttr(uv + '.repeatU'), 2)
        self.assertEqual( cmds.getAttr(uv + '.repeatV'), 3)
        self.assertEqual( cmds.getAttr(uv + '.offsetU'), 0.5)
        self.assertEqual( cmds.getAttr(uv + '.offsetV'), -0.5)
        self.assertEqual( cmds.getAttr(uv + '.rotateUV'), 90)

    def test_3_lambertWithCCTexture(self):
        cmds.file(new=True, f=True)
        cube = cmds.polyCube()

        mat = self.createLambert('lambert', cube[0])
        tex = nerve.maya.Node.CreateTexture('color')


class Maya(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def newScene(self):
        cmds.file(new=True, f=True)

    def simpleCubeWithMaterials(self):
        # Shading Engines
        cube = cmds.polyCube()

        # Yellow Lambert
        lambertA = cmds.shadingNode('lambert', asShader=True, name='lambertA')
        cmds.setAttr(lambertA + '.color', 1, 1, 0 )
        SGA = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name='SGA')
        cmds.connectAttr( lambertA + '.outColor', SGA+'.surfaceShader', f=True)
        cmds.sets(cube[0], e=True, forceElement=SGA)

        # Red Lambert
        lambertB = cmds.shadingNode('lambert', asShader=True, name='lambertB')
        cmds.setAttr(lambertB + '.color', 1, 0, 0 )
        SGB = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name='SGB')
        cmds.connectAttr( lambertB + '.outColor', SGB+'.surfaceShader', f=True)
        cmds.sets(cube[0] + '.f[0]', e=True, forceElement=SGB)

        # Lambert With Textures
        lambertTex = cmds.shadingNode('lambert', asShader=True, name='lambertTex')
        cmds.setAttr(lambertTex + '.color', 0, 0, 1 )

        # Color Texture
        texColor = nerve.maya.Node.CreateTexture('ColorTex')
        cmds.setAttr(texColor + '.fileTextureName', 'color.jpg', type='string')
        cmds.connectAttr(texColor + '.outColor', lambertTex + '.color', f=True)

        # Alpha Texture Through setRange
        texAlpha = nerve.maya.Node.CreateTexture('AlphaTex')
        cmds.setAttr(texAlpha + '.fileTextureName', 'alpha.jpg', type='string')
        setRange = cmds.shadingNode('setRange', asUtility=True)
        cmds.connectAttr(texAlpha + '.outAlpha', setRange + '.valueX', force=True)        
        cmds.connectAttr(setRange + '.outValueX', lambertTex + '.diffuse', f=True)

        SGTex = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name='SGTex')
        cmds.connectAttr( lambertTex + '.outColor', SGTex+'.surfaceShader', f=True)
        cmds.sets(cube[0] + '.f[1]', e=True, forceElement=SGTex)


        return cube[0]

    @unittest.skip('job')
    def test_10_Job(self):
        path = nerve.Path('$TEMP/nerve/mayaTests')
        job = nerve.maya.Job(path)
        if job.Exists():
            job.Delete()

        # Create New Job
        self.assertFalse(path.Exists())
        job.Create(addToRecents=False)
        self.assertTrue(path.Exists())
        mayaproject = path+'maya'
        self.assertTrue(mayaproject.Exists())
        for f in ['workspace.mel', 'maya.cmd', 'scenes', 'sourceimages']:
            self.assertTrue( (mayaproject+f).Exists()  )

        # Set Project
        nerve.maya.Job.Set( path.AsString() )
        self.assertEqual( cmds.workspace(q=True, o=True), mayaproject.AsString())

    @unittest.skip('node')
    def test_20_Node(self):
        self.newScene()

        # Shading Engines
        cube = self.simpleCubeWithMaterials()
        for sg in ['SGA', 'SGB', 'SGTex']:
            self.assertIn(sg,  nerve.maya.Node.GetShadingEngines(cube) )
        # Materials
        for mat in ['lambertA', 'lambertB', 'lambertTex']:
            self.assertIn( mat, nerve.maya.Node.GetMaterials(cube),  )

    def test_30_Materials(self):
        cmds.file(new=True, f=True)

        mat = nerve.maya.Material('lambert', version=1)
        cube = self.simpleCubeWithMaterials()
        cmds.select(cube, r=True)
        mat.Release()

        if False:
            cmds.file(new=True, f=True)
            mat.Import()
            self.assertTrue( cmds.objExists('lambertA') )
            self.assertTrue( cmds.objExists('lambertB') )
            colorA = cmds.getAttr('lambertA.color')[0]
            colorB = cmds.getAttr('lambertB.color')[0]
            #print(colorA)
            #print(colorB)

            self.assertEqual( colorA, (1,1,0))
            self.assertEqual( colorB, (1,0,0))
            
        

def Run():
    testSuite = unittest.TestSuite()
    testSuite.addTest( unittest.makeSuite(MayaMaterial))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(testSuite)
