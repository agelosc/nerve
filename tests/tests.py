import os, sys
sys.path.append( os.environ['NERVE_LOCAL_PATH'] + '/lib')
import unittest
import nerve

SAMPLES = nerve.Path('$NERVE_LOCAL_PATH/tests/samples/')


class testNerve(unittest.TestCase):
    def NewJob(self):
        job = nerve.Job()
        if job.Exists():
            job.Delete()
        job.Create()
        return job

    def testPath(self):
        # Expand Environmental Variables
        self.assertEqual( nerve.Path('$TEMP'), os.environ['TEMP'] )
        self.assertEqual( nerve.Path('$TEMP/A'), os.environ['TEMP']+'/A' )
        self.assertEqual( nerve.Path('/A/$TEMP'), '/A/'+os.environ['TEMP'] )

        # Separator
        path = nerve.Path('/A/B', '|')
        self.assertEqual(path.AsString(), '|A|B')
        path = nerve.Path('/A/B')
        self.assertEqual( path.AsString('|'), '|A|B')

        # Magic methods
        path = nerve.Path('/A/B')
        self.assertEqual( str(path), '/A/B' )
        self.assertEqual( path, '/A/B')
        self.assertNotEqual( path, '/C/D' )
        self.assertEqual( path + 'C', '/A/B/C')
        self.assertEqual( path + 'C/D/E/F/G', '/A/B/C/D/E/F/G')
        self.assertEqual( path + '/C', '/A/B/C')
        self.assertEqual( path + '/C/D/E/F/G', '/A/B/C/D/E/F/G')
        path = nerve.Path('A/B')
        self.assertEqual(path + 'C/D/E/F/G', 'A/B/C/D/E/F/G')
        self.assertEqual(path + '/C/D/E/F/G', 'A/B/C/D/E/F/G')


        # Object passeed as argument that expexts string type
        path = nerve.Path('/A/B')
        def GetString(path:str) -> str:
            return path
        self.assertEqual( GetString(path), '/A/B')

        # Is Absolute
        self.assertTrue( nerve.Path('/A/B').IsAbsolute() )
        self.assertFalse( nerve.Path('A/B').IsAbsolute() )
        self.assertTrue( nerve.Path('C:/A').IsAbsolute())

        # Validate path
        for path in ['A', 'R:/', 'R:/A B', 'R:/A[]']:
            self.assertFalse( nerve.Path(path).IsValid() )
        
        # Parent
        self.assertEqual(nerve.Path('/A/B').GetParent(), '/A')
        self.assertEqual(nerve.Path('/A/B/C').GetParent(2), '/A')
        self.assertTrue( nerve.Path('/A/B').HasParent() )
        self.assertFalse( nerve.Path('A').HasParent() )
        
        # Relatives
        self.assertEqual( nerve.Path('/A/B').GetRelative(-1), 'B' )
        self.assertEqual( nerve.Path('/A/B/C').GetRelative(-2), 'B/C' )
        self.assertEqual( nerve.Path('/A/B').GetRelative(1), 'A')
        self.assertEqual( nerve.Path('/A/B/C').GetRelative(2), 'A/B')

        self.assertEqual( nerve.Path('/A/B').GetHead(), 'B')
        self.assertEqual( nerve.Path('/A/B.txt').GetFileName(), 'B' )
        self.assertEqual( nerve.Path('/A/B.txt').GetExtension(), 'txt' )
        self.assertTrue( nerve.Path('/A/B').IsDir() )
        self.assertTrue( nerve.Path('/A/B.txt').IsFile() )

        self.assertTrue( nerve.Path('$TEMP').Exists() )

        # Set/Create/Remove
        path = nerve.Path( '$TEMP/nervetests' )
        self.assertFalse(path.Exists())
        path.Create()
        self.assertTrue( path.Exists() )
        path.Remove()
        self.assertFalse( path.Exists() )

        path = nerve.Path('$TEMP/nervetest.txt')
        content = 'Nerve Test File'
        path.SetContent(content)
        self.assertFalse(path.Exists())
        path.Create()
        self.assertTrue( path.Exists() )
        self.assertEqual( path.Read(), content)
        
        # Set content on another file    
        pathB = nerve.Path('$TEMP/nervetestB.txt')
        pathB.SetContent(path)
        pathB.Create()
        self.assertEqual( pathB.Read(), content )

        path.Remove()
        self.assertFalse( path.Exists() )
        pathB.Remove()
        self.assertFalse( pathB.Exists() )

        # Versions
        path = nerve.Path('/A/B_v1.txt')
        self.assertTrue(path.HasVersion())
        self.assertEqual(path.GetVersion(), 1)
        self.assertEqual(path.GetStringVersion(), 'v1')

        path = nerve.Path('/A/B_v02.txt')
        self.assertTrue( path.HasVersion() )
        self.assertEqual( path.GetVersion(), 2)
        self.assertEqual( path.GetStringVersion(), 'v02')

        path = nerve.Path('/A/B_v003.txt')
        self.assertTrue( path.HasVersion() )
        self.assertEqual( path.GetVersion(), 3)
        self.assertEqual( path.GetStringVersion(), 'v003')

        path = nerve.Path('/A/B.txt')
        self.assertFalse( path.HasVersion() )

        # Glob
        path = nerve.Path('$TMP') + 'nerve'
        path.Create()
        for name in ['A.txt', 'B.txt', 'C.txt']:
            p = path + name
            p.Create()

        files = nerve.Path.Glob( path.AsString() + '/*.txt' )
        self.assertEqual( files[0].GetHead(), 'A.txt')
        self.assertEqual( files[1].GetHead(), 'B.txt')
        self.assertEqual( files[2].GetHead(), 'C.txt')

        for name in ['A.txt', 'B.txt', 'C.txt']:
            p = path + name
            p.Remove()

        self.assertFalse(files[0].Exists())
        self.assertFalse(files[1].Exists())
        self.assertFalse(files[2].Exists())

        path = nerve.Path('/A')
        self.assertEqual( path.Trim(), nerve.Path('A') )
        path = nerve.Path('/A/B')
        self.assertEqual( path.Trim(), nerve.Path('A/B') )
        path = nerve.Path('/A/B/C')
        self.assertEqual( path.Trim(), nerve.Path('A/B/C') )        
        path = nerve.Path('/A/B/C/D')
        self.assertEqual( path.Trim(), nerve.Path('A/B/C/D') )                

    def testString(self):
        self.assertFalse(nerve.String.IllegalCharacters('abc'))
        self.assertTrue(nerve.String.IllegalCharacters('abc[]'))

        self.assertEqual( nerve.String.versionAsString(1), 'v001')
        self.assertEqual( nerve.String.versionAsInt('v001'), 1)

        self.assertEqual( nerve.String.UnCamelCase('camelCase'), 'Camel Case' )
        self.assertEqual( nerve.String.UnSnakeCase('snake_case'), 'Snake Case' )

    def testImage(self):
        image = nerve.Image(SAMPLES+'testSquare.jpg')
        self.assertEqual( image.GetSize(), (512, 512) )

        # Save As
        outimage = nerve.Path('$TEMP/testImage.png')
        image.SaveAs( outimage )
        self.assertTrue(image.GetFile().Exists())
        image.GetFile().Remove()
        self.assertFalse(image.GetFile().Exists())

        # Square Landscape
        image = nerve.Image( SAMPLES+'testLandscape.jpg')
        image.Square( outimage )
        self.assertTrue( image.GetFile().Exists() )
        self.assertEqual( image.GetSize(), (512, 512) )

        # Square Portrait
        image = nerve.Image( SAMPLES+'testPortrait.jpg')
        image.Square( outimage )
        self.assertTrue( image.GetFile().Exists() )
        self.assertEqual( image.GetSize(), (512, 512) )

        image.GetFile().Remove()
        self.assertFalse(image.GetFile().Exists())

        # Convert EXR
        image = nerve.Image( SAMPLES+'hdri/hdri.exr')
        image.SaveAs( outimage )
        self.assertTrue(image.GetFile().Exists())
        image.GetFile().Remove()
        self.assertFalse(image.GetFile().Exists())

    def testJob(self):
        job = nerve.Job()
        jobpath = nerve.Path( nerve.conf['JOB'] )
        self.assertEqual( job.GetFilePath('job'), jobpath )

    def testAsset(self):
        
        jobPath = nerve.Path('N:/jobs/test')
        os.environ['JOB'] = jobPath.AsString()
        asset = nerve.Asset('A')
        assetPath = jobPath + nerve.conf['DIR'] + 'assets'
        if assetPath.Exists():
            assetPath.Remove(True)

        # Defaults
        self.assertTrue( isinstance(asset.data['job'], nerve.Path) )
        self.assertTrue( isinstance(asset.data['path'], nerve.Path) )
        self.assertEqual( asset.data['job'], jobPath)
        self.assertEqual( asset.data['path'], 'A')

        # Versions
        self.assertEqual( asset.GetVersions(), [])

        self.assertEqual( asset.GetVersion(), 1 )
        self.assertEqual( nerve.Asset('A', version=2).GetVersion(), 2 )
        self.assertEqual( nerve.Asset('A', version=0).GetVersion(), 1 )
        self.assertEqual( nerve.Asset('A', version=-1).GetVersion(), 1 )
        self.assertEqual( nerve.Asset('A').SetVersion(2).GetVersion(), 2 )
        self.assertEqual( nerve.Asset('A').GetVersionAsString(), 'v001' )

        # Format / Extension
        self.assertEqual( nerve.Asset('A').GetExtension(), 'usd' )
        self.assertEqual( nerve.Asset('A').GetFormat(), 'usd' )
        self.assertEqual( nerve.Asset('A', format='abc').GetExtension(), 'abc')
        self.assertEqual( nerve.Asset('A', format='abc').GetFormat(), 'abc')
        self.assertEqual( nerve.Asset('A').SetFormat('abc').GetFormat(), 'abc')
        self.assertEqual( nerve.Asset('A', format='abc').SetExtension('def').GetFormat(), 'abc' )
        self.assertEqual( nerve.Asset('A', format='abc').SetExtension('def').GetExtension(), 'def' )

        # File Paths
        rootPath = jobPath + nerve.conf['DIR'] + 'assets'
        self.assertEqual( asset.GetFilePath('job'), jobPath) # job 
        self.assertEqual( asset.GetFilePath('root'), rootPath ) # root
        self.assertEqual( nerve.Asset('').GetFilePath('root'), rootPath) # root
        self.assertEqual( nerve.Asset('A/B').GetFilePath('root'), rootPath+'A') # root
        self.assertEqual( nerve.Asset('A/B/C').GetFilePath('root'), rootPath+'A/B') # root

        self.assertEqual( asset.GetFilePath(), rootPath +'A.usda' ) # main
        #self.assertEqual( nerve.Asset('').GetFilePath(), rootPath +'default.usda' ) # main
        self.assertEqual( nerve.Asset('A/B').GetFilePath(), rootPath +'A/B.usda' ) # main
        self.assertEqual( nerve.Asset('A/B/C').GetFilePath(), rootPath +'A/B/C.usda' ) # main
        self.assertEqual( nerve.Asset('A').GetFilePath('session'), rootPath + 'A/A_v001.usd' ) # session
        self.assertEqual( nerve.Asset('A', version=2).GetFilePath('session'), rootPath + 'A/A_v002.usd' ) # session
        self.assertEqual( nerve.Asset('A/B', version=0).GetFilePath('session'), rootPath + 'A/B/B_v001.usd' ) # session
        self.assertEqual( nerve.Asset('A').GetFilePath('range'), rootPath + 'A/A_v001/A_v001.{}.usd' ) # range
        self.assertEqual( nerve.Asset('A/B').GetFilePath('range'), rootPath + 'A/B/B_v001/B_v001.{}.usd' ) # range

        self.assertEqual( nerve.Asset('A').GetFilePath('cover'), rootPath + 'A.png' ) # cover

        # Create
        asset = nerve.Asset('A')
        asset.Release()
        asset = nerve.Asset('A')
        asset.Release()
        asset = nerve.Asset('A', version=2, format='usda')
        asset.Release()
        self.assertEqual( asset.GetVersions(), [1,2] )
        self.assertEqual( asset.GetFormats(), ['usd', 'usda'] )

        asset = nerve.Asset('B/C')
        asset.Release()
        self.assertEqual( nerve.Asset('B').GetChildren(), ['C'])
        asset = nerve.Asset('B/D')
        asset.Release()
        self.assertEqual( nerve.Asset('B').GetChildren(), ['C', 'D'])

    def testTest(self):
        from pxr import Usd, Sdf
        
        #print(nerve.conf)
        #job = nerve.Job('N:/jobs/test')
        #job.Create()
        pth = nerve.Path( 'N:/jobs/job.usda' )
        #pth = nerve.Path('M:/jobs/atkpln/CapnCrunch/build/elements/input/test.usda')
        print(pth)
        #tpth = nerve.Path('$TEMP/nerve/') + pth.GetHead()
        Sdf.Layer.CreateNew( pth.AsString() )
        #tpth.Copy(pth)

class NerveOLD(unittest.TestCase):
    def NewJob(self):
        job = nerve.Job()
        if job.Exists():
            job.Delete()
        job.Create()
        return job

    def testJob(self):
        # config default path
        job = nerve.Job()
        self.assertEqual(job.GetDir(), nerve.Path(nerve.conf['JOB']).AsString())

        # Custom Path
        job = nerve.Job('$TEMP/nerve2')
        self.assertEqual(job.GetDir(), nerve.Path('$TEMP/nerve2').AsString())

        # ENV path
        path = nerve.Path('$TEMP/nerve')
        os.environ['JOB'] = path.AsString()

        job = nerve.Job()
        self.assertEqual(job.GetDir(), path.AsString())

    def testAsset(self):
        job = self.NewJob()

        # Metadata
        asset = nerve.Asset('metadata', version=1, description='Metadata', format='usd', comment="USD comment v001")
        asset.Release(filepath=SAMPLES+'asset.usd')
        asset = nerve.Asset('metadata', version=2, description='Metadata Latest', format='usd', comment="USD comment v002")
        asset.Release(filepath=SAMPLES+'asset.usd')

        asset = nerve.Asset('metadata', version=2, description='Metadata Latest', format='abc', comment="ABC comment v002")
        asset.Release(filepath=SAMPLES+'asset.abc')
        
        # Format
        asset = nerve.Asset('format', version=1)
        #print(asset.GetFormat())
        
    def testAssets(self):
        self.NewJob()

        asset = nerve.Asset('A')        

        # version
        self.assertEqual(asset.data['version'], asset.GetVersion())
        self.assertEqual(asset.GetVersion(), 1)

        # path
        self.assertEqual(asset.GetPath(), 'A')
        self.assertEqual(asset.GetName(), 'A')

        # hierarchy
        

        self.assertFalse(asset.Exists())


    def testFindCover(self):
        job = nerve.Job('R:/library')
        hdri = nerve.HDRI(path='HDRI/outdoor/Sky490', version=1, job=job)
        child = nerve.HDRI(path='HDRI/outdoor/Sky490/Sky490_4K', version=1, job=job)

        self.assertTrue(hdri.Exists())
        self.assertTrue(child.Exists())

        self.assertFalse(hdri.HasCover())
        self.assertTrue(child.HasCover())

        self.assertTrue(hdri.HasChildren())
        for child in hdri.GetChildren():
            obj = hdri.GetChild( child )
            nerve.String.pprint(obj.data)
            self.assertTrue(obj.Exists())

if __name__ == '__main__':
    unittest.main()


        







    

        


