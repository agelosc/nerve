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

class Base(unittest.TestCase):
    def NewScene(self):
        cmds.file(new=True, f=True)
    
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

        

        return result

    def CreateLambert(self, name, assign=None):
        mat = cmds.shadingNode('lambert', asShader=True, name=name)
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name+'_SG')
        cmds.connectAttr(mat + '.outColor', sg + '.surfaceShader', f=True)
        if assign:
            cmds.sets(assign, e=True, forceElement=sg)
        return mat 

class Maya(Base):
    @unittest.skip('skip')
    def test_Job(self):
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

class MayaNode(Base):
    @unittest.skip("skip")    
    def test_GetShadingEngines(self):
        self.NewScene()

        cube = cmds.polyCube()
        yellow = self.CreateLambert('A', cube[0])
        red = self.CreateLambert('B', cube[0] +'.f[0]')

        sgs = nerve.maya.Node.GetShadingEngines(cube[0])
        self.assertEqual( len(sgs), 2  )
        self.assertIn( 'A_SG', sgs)
        self.assertIn( 'B_SG', sgs)

    @unittest.skip("skip")    
    def test_GetMaterials(self):
        self.NewScene()

        cube = cmds.polyCube()
        yellow = self.CreateLambert('A', cube[0])
        red = self.CreateLambert('B', cube[0] +'.f[0]')

        materials = nerve.maya.Node.GetMaterials(cube[0])
        self.assertEqual( len(materials), 2  )
        self.assertIn( 'A', materials)
        self.assertIn( 'B', materials)           

class MayaMaterial(Base):
    @unittest.skip("skip")    
    def test_concrete(self):
        self.NewScene()
        net = self.CreateLambertNetwork()

        # set values
        matdata = {'translucence':0.1, 'translucenceDepth':0.2, 'ambientColor':(0.1, 0.2, 0.3) } 
        for attr,val in matdata.items():
            nerve.maya.Node.setAttr(net['mat'], attr, val)
        ccdata = {'hueShift':0.1, 'satGain':0.2, 'valGain':0.3, 'colGain':(0.2, 0.3, 0.1), 'colGamma':(0.46, 0.46, 0.46) }
        for attr,val in ccdata.items():
            nerve.maya.Node.setAttr(net['cc'], attr, val)
        srdata = {'min':(1,2,3), 'max':(4,5,6), 'oldMin':(7,8,9), 'oldMax':(10,11,12)}
        for attr,val in srdata.items():
            nerve.maya.Node.setAttr(net['setRange'], attr, val)

        cmds.select(net['mat'], r=True)
        material = nerve.maya.Material('lambert', version=1)
        material.Release(abstract=False)

        self.NewScene()
        # Create clashing node name
        cmds.shadingNode('setRange', asUtility=True, name='colorTex')
        material.Gather()

        for attr,val in matdata.items():
            self.assertTrue( nerve.maya.Node.getAttr(net['mat'], attr), val )
        for attr, val in ccdata.items():
            self.assertTrue( nerve.maya.Node.getAttr(net['cc'], attr), val )
        for attr, val in srdata.items():
            self.assertTrue( nerve.maya.Node.getAttr(net['setRange'], attr), val ) 

    @unittest.skip("skip")
    def test_concreteWithNamespace(self):
        self.NewScene()
        ns = 'NS'
        cmds.namespace(add=ns)
        cmds.namespace(setNamespace=ns)
        net = self.CreateLambertNetwork()

        cmds.select(net['mat'], r=True)
        material = nerve.maya.Material('lambert', version=1)
        material.Release(abstract=False)

        self.NewScene()
        material.Gather()

        for key,name in net.items():
            self.assertFalse( cmds.objExists( name) )
            self.assertTrue( cmds.objExists( nerve.maya.Node.CleanName(name)) )  

    @unittest.skip("skip")
    def test_simpleAbstract(self):
        # Release Lambert Abstract
        self.NewScene()
        mat = nerve.maya.Node.create('lambert')
        matdata = {'color':(1.0,1.0,0.0), 'diffuse':0.435}
        for key,val in matdata.items():
            nerve.maya.Node.setAttr(mat, key, val)

        cmds.select(mat, r=True)
        material = nerve.maya.Material('lambert', version=1)
        material.Release(concrete=False)

        # Gather Lambert
        self.NewScene()
        material.Gather()
        self.assertTrue( cmds.objExists(mat) )
        for key,val in matdata.items():
            self.assertAlmostEqual( nerve.maya.Node.getAttr(mat, key), val )

        # Gather usdPreviewSurface
        self.NewScene()
        material.Gather(shader='usdPreviewSurface')
        self.assertEqual( nerve.maya.Node.getAttr(mat, 'diffuseColor'), matdata['color'])

        # Gather RedshiftMaterial
        self.NewScene()
        material.Gather(shader='RedshiftMaterial')

        # Release RedshiftMaterial
        mat = nerve.maya.Node.create('RedshiftMaterial')
        matdata = {'diffuse_color': (1,1,0), 'diffuse_weight':0.23}
        for key,val in matdata.items():
            nerve.maya.Node.setAttr( mat, key, val)

        cmds.select(mat, r=True)
        material.Release()

        # Gather Lambert
        self.NewScene()
        material.Gather()
        self.assertEqual(nerve.maya.Node.getAttr(mat, 'color'), matdata['diffuse_color'])
        self.assertAlmostEqual(nerve.maya.Node.getAttr(mat, 'diffuse'), matdata['diffuse_weight'])

        # Gather standardSurface
        self.NewScene()
        material.Gather(shader='standardSurface')
        self.assertEqual(nerve.maya.Node.getAttr(mat, 'baseColor'), matdata['diffuse_color'])
        self.assertAlmostEqual(nerve.maya.Node.getAttr(mat, 'base'), matdata['diffuse_weight'])
    
    @unittest.skip("skip")
    def test_abstractWithTextures(self):
        self.NewScene()
        net = self.CreateLambertNetwork()
        
        cmds.select(net['mat'], r=True)
        material = nerve.maya.Material('abstractWithTextures', version=1)
        material.Release(concrete=False)

        self.NewScene()
        material.Gather(shader='RedshiftMaterial')
    
    @unittest.skip("skip")
    def test_convert(self):
        # Simple Lambert
        self.NewScene()
        mat = self.CreateLambert('lambert')
        nerve.maya.Node.setAttr(mat, 'color', (1,1,0))
        nerve.maya.Node.setAttr(mat, 'diffuse', 0.72)

        cmds.select(mat, r=True)
        material = nerve.maya.Material().Convert('RedshiftMaterial')[0]

        self.assertEqual( nerve.maya.Node.getAttr(material, 'diffuse_color'), (1,1,0) )
        self.assertAlmostEqual( nerve.maya.Node.getAttr(material, 'diffuse_weight'), 0.72 )
        
        # Lambert With Textures
        self.NewScene()
        net = self.CreateLambertNetwork()

        cmds.select(net['mat'], r=True)
        material = nerve.maya.Material().Convert('RedshiftMaterial')[0]
        self.assertTrue( cmds.isConnected(net['cc']+'.outColor', material+'.diffuse_color') )
        self.assertTrue( cmds.isConnected(net['reverse']+'.outputX', material+'.diffuse_weight') )

    @unittest.skip("skip")
    def test_allConcrete(self):
        self.NewScene()
        material = nerve.maya.Material('material', version=1)
        mattypes = material.GetMaterialTypes()
        for mattype in mattypes:
            #self.NewScene()
            mat = nerve.maya.Node.create(mattype)
            table = material.GetMaterialTable( mattype )
            data = {}
            for grp in table.keys():
                data[grp] = {}
                for key, attr in table[grp].items():
                    rand = nerve.maya.Node.GetRandomValue( mat, attr )
                    data[grp][attr] = rand
                    nerve.maya.Node.setAttr( mat, attr, rand )
            
            cmds.select(mat, r=True)
            material.Release(abstract=False)

            self.NewScene()
            newmat = material.Gather(shader=mattype)[0]
            for grp in data.keys():
                for attr, val in data[grp].items():
                    attrdata = nerve.maya.Node.GetAttrData(newmat, attr)
                    if attrdata['type'] == 'float':
                        self.assertAlmostEqual( nerve.maya.Node.getAttr(newmat, attr), val, 2 )
                    elif attrdata['type'] == 'vector':
                        for i in range(3):
                            self.assertAlmostEqual( nerve.maya.Node.getAttr(newmat, attr)[i], val[i], 2  )
                    else:
                        self.assertEqual( nerve.maya.Node.getAttr(newmat, attr), val  )
    
    @unittest.skip("skip")
    def test_allAbstract(self):
        self.NewScene()
        material = nerve.maya.Material('material', version=1)
        mattypes = material.GetMaterialTypes()
        for mattype in mattypes:
            #self.NewScene()
            mat = nerve.maya.Node.create(mattype)
            table = material.GetMaterialTable( mattype )
            data = {}
            for grp in table.keys():
                data[grp] = {}
                for key, attr in table[grp].items():
                    rand = nerve.maya.Node.GetRandomValue( mat, attr )
                    data[grp][attr] = rand
                    nerve.maya.Node.setAttr( mat, attr, rand )
            
            cmds.select(mat, r=True)
            material.Release(concrete=False)
            
            for imattype in mattypes:
                self.NewScene()
                newmat = material.Gather(shader=imattype)[0]
                print('Gathering {} as abstract {}...'.format(mattype, imattype))

                ctable = material.GetMaterialConvertTable( mattype, imattype)
                for grp in ctable.keys():
                    for key, val in ctable[grp].items():
                        if not (val['src'] and val['dest']):
                            continue
                        expectedVal = data[grp][ val['src'] ]
                        currentVal = nerve.maya.Node.getAttr( newmat, val['dest'] )
                        # Skip type mistmatch
                        if type(expectedVal) != type(currentVal):
                            continue

                        attrdata = nerve.maya.Node.GetAttrData(newmat, val['dest'])

                        if attrdata['type'] == 'float':
                            # skip tests that exceed range
                            if 'min' in attrdata.keys() and expectedVal < attrdata['min']:
                                continue
                            if 'max' in attrdata.keys() and expectedVal > attrdata['max']:
                                continue              
                            self.assertAlmostEqual( expectedVal, currentVal, 2 )
                        elif attrdata['type'] == 'vector':
                            for i in range(3):
                                self.assertAlmostEqual( expectedVal[i], currentVal[i], 2  )
                        else:
                            self.assertEqual( expectedVal, currentVal  )            

    @unittest.skip('skip')
    def test_allConvert(self):
        self.NewScene()
        material = nerve.maya.Material('material', version=1)
        mattypes = material.GetMaterialTypes()
        for mattype in mattypes:
            for imattype in mattypes:
                if imattype == mattype:
                    continue
                self.NewScene()
                mat = nerve.maya.Node.create(mattype)
                table = material.GetMaterialTable( mattype )

                data = {}
                for grp in table.keys():
                    data[grp] = {}
                    for key, attr in table[grp].items():
                        rand = nerve.maya.Node.GetRandomValue( mat, attr )
                        data[grp][attr] = rand
                        nerve.maya.Node.setAttr( mat, attr, rand )

                print('Converting {} to {}'.format(mattype, imattype))
                cmds.select(mat, r=True)
                newmat = material.Convert(imattype)[0]

                ctable = material.GetMaterialConvertTable( mattype, imattype)
                for grp in ctable.keys():
                    for key, val in ctable[grp].items():
                        if not (val['src'] and val['dest']):
                            continue
                        expectedVal = data[grp][ val['src'] ]
                        currentVal = nerve.maya.Node.getAttr( newmat, val['dest'] )
                        # Skip type mistmatch
                        if type(expectedVal) != type(currentVal):
                            continue

                        attrdata = nerve.maya.Node.GetAttrData(newmat, val['dest'])

                        if attrdata['type'] == 'float':
                            # skip tests that exceed range
                            if 'min' in attrdata.keys() and expectedVal < attrdata['min']:
                                continue
                            if 'max' in attrdata.keys() and expectedVal > attrdata['max']:
                                continue              
                            self.assertAlmostEqual( expectedVal, currentVal, 2 )
                        elif attrdata['type'] == 'vector':
                            for i in range(3):
                                self.assertAlmostEqual( expectedVal[i], currentVal[i], 2  )
                        else:
                            self.assertEqual( expectedVal, currentVal  ) 

    @unittest.skip('skip')
    def test_AbstractBumpMap(self):
        self.NewScene()
        mat = nerve.maya.Node.create('lambert')
        sg = nerve.maya.Node.create('shadingGroup')
        bump = nerve.maya.Node.create('bump2d')
        tex = nerve.maya.Node.create('file')
        disp = nerve.maya.Node.create('displacementShader')
        dtex = nerve.maya.Node.create('file')

        cmds.setAttr(tex+'.fileTextureName', 'bump.jpg', type='string')
        cmds.setAttr(bump+'.bumpDepth', 0.033)
        cmds.setAttr(dtex + '.fileTextureName', 'disp.jpg', type='string')
        cmds.setAttr(disp + '.scale', 0.5)

        cmds.connectAttr(tex + '.outAlpha', bump + '.bumpValue', f=True)
        cmds.connectAttr(bump + '.outNormal', mat + '.normalCamera', f=True)
        cmds.connectAttr(mat + '.outColor', sg + '.surfaceShader', f=True)
        cmds.connectAttr(disp + '.displacement', sg + '.displacementShader', f=True)
        cmds.connectAttr(dtex + '.outColor', disp + '.vectorDisplacement', f=True)

        cmds.select(mat, r=True)
        material = nerve.maya.Material('bump', version=1)
        material.Release(concrete=False)
        self.NewScene()
        material.Gather(shader='RedshiftMaterial')
        #nerve.String.pprint( material.ConvertToAbstract(mat)['bump'] )
    
    @unittest.skip('skip')
    def test_ConvertBumpMap(self):
        self.NewScene()
        doDisplacement = True
        mat = nerve.maya.Node.create('lambert')
        sg = nerve.maya.Node.create('shadingGroup')
        bump = nerve.maya.Node.create('bump2d')
        tex = nerve.maya.Node.create('file')
        if doDisplacement:
            disp = nerve.maya.Node.create('displacementShader')
            dtex = nerve.maya.Node.create('file')

        cmds.setAttr(tex+'.fileTextureName', 'bump.jpg', type='string')
        cmds.setAttr(tex+'.colorSpace', 'Raw', type='string')

        cmds.setAttr(bump+'.bumpDepth', 0.033)
        cmds.setAttr(bump+'.bumpInterp',2)
        if doDisplacement:
            cmds.setAttr(dtex + '.fileTextureName', 'disp.jpg', type='string')
            cmds.setAttr(disp + '.scale', 0.5)

        cmds.connectAttr(tex + '.outAlpha', bump + '.bumpValue', f=True)
        cmds.connectAttr(bump + '.outNormal', mat + '.normalCamera', f=True)
        cmds.connectAttr(mat + '.outColor', sg + '.surfaceShader', f=True)
        if doDisplacement:
            cmds.connectAttr(disp + '.displacement', sg + '.displacementShader', f=True)
            cmds.connectAttr(dtex + '.outColor', disp + '.vectorDisplacement', f=True)

        cmds.select(mat, r=True)
        data = nerve.maya.Material().ConvertToAbstract(mat)
        #nerve.String.pprint(data['bump'])
        nerve.maya.Material().Convert('RedshiftMaterial')
    
    #@unittest.skip('skip')
    def test_ConvertNoBumpMap(self):
        self.NewScene()
        net = self.CreateLambertNetwork()

        #cmds.select(net['mat'], r=True)
        #nerve.maya.Material().Convert('RedshiftMaterial')

    @unittest.skip('skip')
    def test_HasDisplacement(self):
        self.NewScene()
        mat = nerve.maya.Node.create('lambert')
        sg = nerve.maya.Node.create('shadingGroup')
        bump = nerve.maya.Node.create('bump2d')
        tex = nerve.maya.Node.create('file')
        disp = nerve.maya.Node.create('displacementShader')
        dtex = nerve.maya.Node.create('file')

        cmds.setAttr(tex+'.fileTextureName', 'bump.jpg', type='string')
        cmds.setAttr(bump+'.bumpDepth', 0.033)
        cmds.setAttr(dtex + '.fileTextureName', 'disp.jpg', type='string')
        cmds.setAttr(disp + '.scale', 0.5)

        cmds.connectAttr(tex + '.outAlpha', bump + '.bumpValue', f=True)
        cmds.connectAttr(bump + '.outNormal', mat + '.normalCamera', f=True)
        cmds.connectAttr(mat + '.outColor', sg + '.surfaceShader', f=True)
        cmds.connectAttr(disp + '.displacement', sg + '.displacementShader', f=True)
        cmds.connectAttr(dtex + '.outColor', disp + '.vectorDisplacement', f=True)

        cmds.select(mat, r=True)
        material = nerve.maya.Material('test', version=1)
        data = material.ConvertToAbstract(mat)
        self.assertTrue(material.AbstractHasDisplacement(data))

        self.NewScene()
        mat = nerve.maya.Node.create('lambert')
        sg = nerve.maya.Node.create('shadingGroup')
        bump = nerve.maya.Node.create('bump2d')
        tex = nerve.maya.Node.create('file')
        #disp = nerve.maya.Node.create('displacementShader')
        #dtex = nerve.maya.Node.create('file')

        cmds.setAttr(tex+'.fileTextureName', 'bump.jpg', type='string')
        cmds.setAttr(bump+'.bumpDepth', 0.033)
        #cmds.setAttr(dtex + '.fileTextureName', 'disp.jpg', type='string')
        #cmds.setAttr(disp + '.scale', 0.5)

        cmds.connectAttr(tex + '.outAlpha', bump + '.bumpValue', f=True)
        cmds.connectAttr(bump + '.outNormal', mat + '.normalCamera', f=True)
        cmds.connectAttr(mat + '.outColor', sg + '.surfaceShader', f=True)
        #cmds.connectAttr(disp + '.displacement', sg + '.displacementShader', f=True)
        #cmds.connectAttr(dtex + '.outColor', disp + '.vectorDisplacement', f=True)

        cmds.select(mat, r=True)
        material = nerve.maya.Material('test', version=1)
        data = material.ConvertToAbstract(mat)
        self.assertFalse(material.AbstractHasDisplacement(data))        



def Run():
    testSuite = unittest.TestSuite()
    testSuite.addTest( unittest.makeSuite(Maya))
    testSuite.addTest( unittest.makeSuite(MayaNode))
    testSuite.addTest( unittest.makeSuite(MayaMaterial) )
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(testSuite)