import os, sys

sys.path.append( os.environ['NERVE_LOCAL_PATH'] + '/lib')

import unittest
import nerve

class Utilities(unittest.TestCase):

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
        self.assertEqual( path + '/C', '/A/B/C')

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
    
    def testString(self):
        self.assertFalse(nerve.String.IllegalCharacters('abc'))
        self.assertTrue(nerve.String.IllegalCharacters('abc[]'))

        self.assertEqual( nerve.String.versionAsString(1), 'v001')
        self.assertEqual( nerve.String.versionAsInt('v001'), 1)

        self.assertEqual( nerve.String.UnCamelCase('camelCase'), 'Camel Case' )
        self.assertEqual( nerve.String.UnSnakeCase('snake_case'), 'Snake Case' )

    def testImage(self):
        samples = nerve.Path('$NERVE_LOCAL_PATH/test/testSamples')

        image = nerve.Image(samples+'testSquare.jpg')
        self.assertEqual( image.GetSize(), (512, 512) )

        # Save As
        outimage = nerve.Path('$TEMP/testImage.png')
        image.SaveAs( outimage )
        self.assertTrue(image.GetFile().Exists())
        image.GetFile().Remove()
        self.assertFalse(image.GetFile().Exists())

        # Square Landscape
        image = nerve.Image( samples+'testLandscape.jpg')
        image.Square( outimage )
        self.assertTrue( image.GetFile().Exists() )
        self.assertEqual( image.GetSize(), (512, 512) )

        # Square Portrait
        image = nerve.Image( samples+'testPortrait.jpg')
        image.Square( outimage )
        self.assertTrue( image.GetFile().Exists() )
        self.assertEqual( image.GetSize(), (512, 512) )

        image.GetFile().Remove()
        self.assertFalse(image.GetFile().Exists())

        # Convert EXR
        image = nerve.Image( samples+'testEXR.exr')
        image.SaveAs( outimage )
        self.assertTrue(image.GetFile().Exists())
        image.GetFile().Remove()
        self.assertFalse(image.GetFile().Exists())

class Nerve(unittest.TestCase):

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

        







    

        


