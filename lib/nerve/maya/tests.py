import os, sys, inspect
import unittest

if __name__ == '__main__':
    import maya.standalone
    maya.standalone.initialize()

try:
    from importlib import reload
except:
    pass

import nerve
import nerve.maya
from nerve.maya import Node
import nerve.maya.tools

import maya.cmds as cmds

class Base(unittest.TestCase):
    def NewScene(self, clearAssets=False):
        cmds.file(new=True, f=True)
        if clearAssets:
            path = nerve.Path('$JOB/nerve/assets')
            if path.Exists():
                path.Remove(True)
    
    def CreateLambertNetwork(self, shadingEngine=False):
        mat = cmds.shadingNode('lambert', asShader=True, name='lambert')
        tex = nerve.maya.Node.create('file', 'colorTex')
        cc = cmds.shadingNode('colorCorrect', asUtility=True)
        alpha = nerve.maya.Node.create('file', 'alphaTex')
        setRange = cmds.shadingNode('setRange', asUtility=True)
        reverse = cmds.shadingNode('reverse', asUtility=True)

        result = {'mat':mat, 'tex':tex, 'cc':cc, 'alpha':alpha, 'setRange':setRange, 'reverse':reverse}

        if shadingEngine:
            sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name='lambert_SG')
            cmds.connectAttr(mat + '.outColor', sg+'.surfaceShader', f=True)
            result['sg'] = sg

        cmds.connectAttr(tex + '.outColor', cc + '.inColor', f=True)
        cmds.connectAttr(cc + '.outColor', mat + '.color', f=True)
        cmds.connectAttr(alpha + '.outColor', setRange + '.value', f=True)
        cmds.connectAttr(setRange + '.outValue', reverse + '.input', f=True)
        cmds.connectAttr(reverse + '.outputX', mat + '.diffuse', f=True)

        Node.setAttr( tex, 'fileTextureName', 'color.jpg')
        Node.setAttr(alpha, 'fileTextureName', 'alpha.jpg')

        return result

    def CreateLambert(self, name, assign=None):
        mat = cmds.shadingNode('lambert', asShader=True, name=name)
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name+'_SG')
        cmds.connectAttr(mat + '.outColor', sg + '.surfaceShader', f=True)
        if assign:
            cmds.sets(assign, e=True, forceElement=sg)
        return mat 

    def CreateMaterialAndAssign(self, shader, obj, name):
        mat = Node.create(shader, name=name)
        sg = Node.create('shadingGroup', name=name+'_SG')
        Node.connectAttr(mat, 'outColor', sg, 'surfaceShader')
        cmds.sets(obj, forceElement=sg)

        return mat

    def loadPlugin(self, plugin):
        if not cmds.pluginInfo(plugin, q=True, loaded=True):
            cmds.loadPlugin(plugin)
        

    def assertDeepEqual(self, src, tar, path=''):
        msg = '{} | src:{} tar:{}'.format(path, src, tar)

        if isinstance(src, str) or isinstance(tar, str):
            src = str(src)
            tar = str(tar)
            self.assertEqual(src, tar, msg=msg)
            return True

        self.assertIsInstance( src, type(tar), msg=msg )

        if isinstance(src, float):
            self.assertAlmostEqual(src, tar, msg=msg)
            return True

        if isinstance(src, int):
            self.assertEqual(src, tar, msg=msg)
            return True

        if isinstance(src, tuple):
            for i in range(len(src)):
                self.assertAlmostEqual( src[i], tar[i], msg=msg)
            return True
        
        if isinstance(src, dict):
            for key in src.keys():
                self.assertDeepEqual(src[key], tar[key], path+'/'+key)

class Maya(Base):
    def testJob(self):
        path = nerve.Path('$TEMP/nerve/mayaTests')
        job = nerve.maya.Job(path)
        if path.Exists():
            path.Remove(recursive=True)

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

class TestMayaNode(Base):
    def test_GetShadingEngines(self):
        self.NewScene()

        cube = cmds.polyCube()
        yellow = self.CreateLambert('A', cube[0])
        red = self.CreateLambert('B', cube[0] +'.f[0]')

        sgs = nerve.maya.Node.GetShadingEngines(cube[0])
        self.assertEqual( len(sgs), 2  )
        self.assertIn( 'A_SG', sgs)
        self.assertIn( 'B_SG', sgs)

    def test_GetMaterials(self):
        self.NewScene()

        cube = cmds.polyCube()
        yellow = self.CreateLambert('A', cube[0])
        red = self.CreateLambert('B', cube[0] +'.f[0]')

        materials = nerve.maya.Node.GetMaterials(cube[0])
        self.assertEqual( len(materials), 2  )
        self.assertIn( 'A', materials)
        self.assertIn( 'B', materials)           

class TestMayaMaterial(Base):
    @classmethod
    def setUpClass(cls):
        for plugin in ['mayaUsdPlugin', 'redshift4maya']:
            if not cmds.pluginInfo(plugin, q=True, loaded=True):
                cmds.loadPlugin(plugin)        
    
    def CreateAbstractNetwork(self):
        Mat = nerve.maya.Material('abstract', version=1)

        # Set Abstract Attributes & Textures
        Mat.SetTexture('color.jpg', 'diffuse', 'color')
        Mat.SetTexture('metalness.jpg', 'reflection', 'metalness')
        Mat.Set(1, 'reflection', 'type')
        Mat.SetTexture('bump.jpg', 'bump', 'map', type=0, height=0.5)
        Mat.SetTexture('disp.jpg', 'displacement', 'map', scale=0.5)
        #Mat.SetTexture('opacity.jpg', 'opacity', 'color')

        return Mat

    def test_Redsfhit(self):
        self.NewScene()
        Mat = self.CreateAbstractNetwork()

        # Create Abstract Material as RedshiftMaterial
        mat = Mat.GetAbstract('RedshiftMaterial')

        # Create in-between texture node
        reverse = Node.create('reverse')
        Node.connectAttr('metalness', 'outColor', reverse, 'input')
        Node.connectAttr(reverse, 'outputX', 'abstract', 'refl_metalness')

        # Create Empty Material
        MatMaya = nerve.maya.Material('abstract', version=1)
        MatMaya.SetAbstract(mat)

        self.assertDeepEqual( Mat.matdata, MatMaya.matdata )

        # Set Concrete
        MatMaya.SetConcrete(mat)
        # Get All Nodes
        sg = cmds.listConnections(mat + '.outColor', type='shadingEngine')
        nodes = cmds.listHistory(sg[0])

        # Re-create Concrete
        self.NewScene()
        MatMaya.GetConcrete(mat)
        # Assert the same nodes exist in new scene
        for n in nodes:
            self.assertTrue( cmds.objExists(n))

    def MaterialTypeTest(self, shader):
        self.NewScene()
        Mat = self.CreateAbstractNetwork()
        mat = Mat.GetAbstract(shader)

        MatMaya = nerve.maya.Material('abstract', version=1)
        MatMaya.SetAbstract(mat)

        table = Mat.GetMaterialTable(shader)
        for grp in table.keys():
            for key in Mat.matdata['abstract']['abstract'][grp].keys():
                src = Mat.matdata['abstract']['abstract'][grp][key]
                tar = MatMaya.matdata['abstract']['abstract'][grp][key]

                if shader in ['lambert', 'usdPreviewSurface', 'standardSurface', 'phong', 'phongE', 'blinn', 'surfaceShader']:
                    if grp == 'reflection' and key == 'type':
                        continue

                if shader == 'usdPreviewSurface' and grp == 'opacity' and key == 'color':
                    continue
                self.assertDeepEqual( src , tar, grp+'/'+key )
        
        sg = cmds.listConnections(mat + '.outColor', type='shadingEngine')
        nodes = cmds.listHistory(sg[0])
        self.NewScene()
        MatMaya.GetAbstract(shader)

        for n in nodes:
            self.assertTrue( cmds.objExists(n) )

    def test_lambert(self):
        self.MaterialTypeTest('lambert')

    def test_phong(self):
        self.MaterialTypeTest('phong')

    def test_blinn(self):
        self.MaterialTypeTest('blinn') 

    def test_standardSurface(self):
        self.MaterialTypeTest('standardSurface')

    def test_usdPreviewSurface(self):
        self.loadPlugin('mayaUsdPlugin')
        self.MaterialTypeTest('usdPreviewSurface')

    def test_phongE(self):
        self.MaterialTypeTest('phongE') 

    def test_surfaceShader(self):
        self.MaterialTypeTest('surfaceShader')               

    def test_convert(self):
        self.NewScene()
        Mat = self.CreateAbstractNetwork()

        mat = Mat.GetAbstract('RedshiftMaterial')
        cmds.select(mat, r=True)
        Mat.Convert('lambert')
        cmds.select(mat, r=True)
        Mat.Convert('phong')

    def test_importExport(self):
        self.NewScene(True)
        Mat = self.CreateAbstractNetwork()
        mat = Mat.GetAbstract('RedshiftMaterial')

        cmds.select(mat, r=True)
        Mat.Release()

        self.NewScene()
        Mat.Gather()

    def test_exportTextures(self):
        self.NewScene(True)
        Mat = nerve.maya.Material('abstract', version=1)

        # Set Abstract Attributes & Textures
        path = nerve.Path('$NERVE_LOCAL_PATH/tests/samples/mat')

        Mat.SetTexture(path+'color.jpg', 'diffuse', 'color')
        Mat.SetTexture(path+'gloss.jpg', 'reflection', 'roughness')
        Mat.SetTexture(path+'normal.jpg', 'bump', 'map', type=1)
        Mat.SetTexture(path+'refl.jpg', 'reflection', 'metalness', type=1)

        mat = Mat.GetAbstract()
        MatMaya = nerve.maya.Material('abstract', version=1)
        cmds.select(mat, r=True)
        MatMaya.SetAbstract( mat )
        MatMaya.SetConcrete( mat )
        
        MatMaya.Release()

        self.NewScene()
        MatMaya.Gather()
        for tex in cmds.ls(type='file'):
            ftp = nerve.Path(Node.getAttr(tex, 'fileTextureName')).GetParent()
            self.assertEqual( ftp.AsString(), MatMaya.GetFilePath('textures').AsString() )
        
class TestMayaTools(Base):
    def test_rsOpacityToSprite(self):
        self.loadPlugin('redshift4maya')
        self.NewScene()
        sg = nerve.maya.Node.create('shadingEngine')
        mat = nerve.maya.Node.create('RedshiftMaterial')
        tex = nerve.maya.Node.create('file')

        nerve.maya.Node.setAttr(tex, 'fileTextureName', 'opacity.jpg')
        nerve.maya.Node.connectAttr(tex, 'outColor', mat, 'opacity_color')
        nerve.maya.Node.connectAttr(mat, 'outColor', sg, 'surfaceShader')

        cmds.select(mat, r=True)
        nerve.maya.tools.rsConvertOpacityToSprite()

        self.assertEqual( nerve.maya.Node.getAttr(mat, 'opacity_color'), (1,1,1) )
        self.assertFalse( cmds.listConnections(mat + '.opacity_color') )
        
        sprite = cmds.listConnections(mat + '.outColor', type='RedshiftSprite')
        self.assertTrue(sprite)
        sprite = sprite[0]
        self.assertTrue( cmds.isConnected(mat + '.outColor', sprite + '.input') )
        self.assertEqual( nerve.maya.Node.getAttr(sprite, 'tex0'), 'opacity.jpg' )

    def test_rsSpriteToOpacity(self):
        self.loadPlugin('redshift4maya')
        self.NewScene()
        sg = Node.create('shadingEngine')
        spr = Node.create('RedshiftSprite')
        mat = Node.create('RedshiftMaterial')
        
        Node.setAttr( spr, 'tex0', 'opacity.jpg')
        Node.connectAttr(spr, 'outColor', sg, 'surfaceShader')
        Node.connectAttr(mat, 'outColor', spr, 'input')

        cmds.select(spr, r=True)
        nerve.maya.tools.rsConvertSpriteToOpacity()
        
        tex = cmds.listConnections(mat + '.opacity_color', type='file')
        self.assertTrue(tex)
        tex = tex[0]
        self.assertEqual( Node.getAttr(tex, 'fileTextureName'), 'opacity.jpg' )
        self.assertTrue( cmds.isConnected(mat + '.outColor', sg + '.surfaceShader') )

class TestAlembic(Base):
    def test_ReleaseGather(self):
        self.NewScene()
        
        # Create Cube
        cube = cmds.polyCube()
        cmds.select(cube[0], r=True)
        # Cube Sublayer
        #cubeAsset = nerve.Asset('cube', format='abc', version=1)
        cubeAsset = nerve.maya.Asset('cube', version=1, format='abc')
        cubeAsset.Release()

        self.NewScene()
        cubeAsset.Gather('Import')
        self.assertTrue( cmds.objExists(cube[0]) )

        # Create Sphere
        cmds.file(new=True, f=True)
        sphere = cmds.polySphere()
        cmds.select(sphere[0], r=True)

        # Sphere Sublayer
        sphereAsset = nerve.maya.Alembic('sphere', version=1)
        sphereAsset.Release()

        # Import Replace
        self.NewScene()
        cubeAsset.Gather('Import')
        cmds.select(cube[0], r=True)
        sphereAsset.Gather('Replace')
        self.assertTrue( cmds.objExists(sphere[0]) )

        # Reference Replace
        self.NewScene()
        cubeAsset.Gather('Reference')
        self.assertTrue( cmds.objExists( 'cube:'+cube[0] ) )
        cmds.select('cube:'+cube[0], r=True)
        sphereAsset.Gather('Replace')
        self.assertTrue(cmds.objExists('cube:'+sphere[0]))

        # Export Animation
        self.NewScene()
        cube = cmds.polyCube()
        animcurve = [{'time':1, 'value':0 }, {'time':10, 'value':5}]
        for crv in animcurve:
            cmds.setKeyframe( cube[0] + '.ty', **crv )

        cubeAnim = nerve.maya.Alembic('cubeAnim', version=1, frameRange=(1, 10))
        cubeAnim.Release()

        # Import Anim
        self.NewScene()
        cubeAnim.Gather()
        for crv in animcurve:
            cmds.currentTime(crv['time'], update=True)
            self.assertEqual( crv['value'], Node.getAttr(cube[0], 'ty') )
        return True

        # Reference Anim
        self.NewScene()
        cubeAnim.Gather('Reference')
        for crv in animcurve:
            cmds.currentTime(crv['time'], update=True)
            self.assertEqual( crv['value'], Node.getAttr('cubeAnim:'+cube[0], 'ty') )

        # Export Anim with deformation
        self.NewScene()
        plane = cmds.polyPlane(w=1, h=1, sx=2, sy=1, ax=(0,1,0))
        bend = cmds.nonLinear(type='bend')
        Node.setAttr(bend[1], 'rz', -90)
        cmds.setKeyframe(bend[0] + '.curvature', v=0, t=1)
        cmds.setKeyframe(bend[0] + '.curvature', v=-90, t=10)

        planeAsset = nerve.maya.Alembic('planeDeform', version=1, frameRange=(1, 10))
        cmds.select(plane[0], r=True)
        planeAsset.Release()

        # Import Anim with deformation
        self.NewScene()
        planeAsset.Gather('Import')
        cmds.currentTime(1, update=True)
        pos = cmds.xform(plane[0] + '.vtx[0]', q=True, ws=True, t=True)
        self.assertAlmostEqual(tuple(pos), (-0.5, 0.0, 0.5) )
        cmds.currentTime(10, update=True)
        pos = cmds.xform(plane[0] + '.vtx[0]', q=True, ws=True, t=True)
        self.assertAlmostEqual( tuple(pos), (-0.31830987334251404, 0.31830987334251404, 0.5) )
        
    def test_ShadingEngines(self):
        self.NewScene()

        cube = cmds.polyCube()
        sphere = cmds.polySphere()
        Node.setAttr(sphere[0], 'translate', (2,0,0))
        plane = cmds.polyPlane()
        Node.setAttr(plane[0], 'translate', (-2,0,0))
        Node.setAttr(plane[0], 'v', False)
        
        

        yellow = self.CreateMaterialAndAssign('lambert', cube[0], 'yellow')
        Node.setAttr(yellow, 'color', (1,1,0))
        red = self.CreateMaterialAndAssign('lambert', cube[0]+'.f[0]', 'red')
        Node.setAttr(red, 'color', (1,0,0))
        green = self.CreateMaterialAndAssign('lambert', sphere[0], 'green')
        Node.setAttr(green, 'color', (0,1,0))

        abc = nerve.maya.Alembic('cubeFaceSets', version=1)
        cmds.select([cube[0], sphere[0]], plane[0], r=True)
        abc.Release()

        if True:
            self.NewScene()
            abc.Gather()
            self.assertTrue( cmds.objExists('yellow_SG') )
            self.assertTrue( cmds.objExists('red_SG') )
            self.assertEqual( cmds.sets('yellow_SG', q=True), [cube[0] + '.f[1:5]'] )
            self.assertEqual( cmds.sets('red_SG', q=True), [cube[0] + '.f[0]'] )


def Run(test=None):
    testSuite = unittest.TestSuite()
    if not test:
        for name, obj in inspect.getmembers(sys.modules[__name__]):
            if inspect.isclass(obj) and name.startswith('Test'):
                testSuite.addTest( unittest.makeSuite( obj ) )
    else:
        if '.' in test:
            obj, func = test.split('.')
            if not hasattr(sys.modules[__name__], obj):
                cmds.warning(test + ' test class not found.')
                return False
            obj = getattr(sys.modules[__name__], obj)
            if hasattr(obj, func):
                #func = getattr(obj, func)
                testSuite.addTest( obj(func) )

        else:
            if not hasattr(sys.modules[__name__], test):
                cmds.warning(test + ' test class not found.')
                return False
            obj = getattr(sys.modules[__name__], test)
            if inspect.isclass(obj):
                testSuite.addTest( unittest.makeSuite( obj ) )

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(testSuite)

if __name__ == '__main__':
    unittest.main()
