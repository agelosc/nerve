import nerve

import sys, os
print(sys.version)
print('')
print('##')

def NewJob():
    job = nerve.Job()
    if job.Exists():
        job.Delete()
    job.Create()

def PathTests():
    # Expand Environmental Variable
    assert nerve.Path('$TEMP') == os.environ['TEMP']
    assert nerve.Path('$TEMP/A') == os.environ['TEMP']+'/A'
    assert nerve.Path('/A/$TEMP') == '/A/'+os.environ['TEMP']

    # Separator
    path = nerve.Path('/A/B', '|')
    assert path.AsString() == '|A|B'
    path = nerve.Path('/A/B')
    assert path.AsString('|') == '|A|B'

    # Object passed as argument that expects string
    path = nerve.Path('/A/B')
    def GetString(path:str) -> str:
        return path

    # Magic Methods
    assert str(nerve.Path('/A/B')) == '/A/B' # __repr__
    assert nerve.Path('/A/B') == '/A/B' # __eq__
    assert nerve.Path('/A/B') != '/B/C' #__ne__
    assert nerve.Path('/A') + 'B' == '/A/B' # __add__
    assert nerve.Path('/A') + '/B' == '/A/B' # __add__

    # IsAbsolute
    assert nerve.Path('/A/B').IsAbsolute() is True
    assert nerve.Path('A/B').IsAbsolute() is False
    assert nerve.Path('R:/jobs').IsAbsolute() is True
    assert nerve.Path('/jobs').IsAbsolute() is True
    assert nerve.Path('jobs').IsAbsolute() is False

    # GetDrives
    assert 'C' in nerve.Path.GetDrives()

    # Is Path Valid
    assert nerve.Path('jobs').IsValid() is False # Is Not Absolute
    assert nerve.Path('R:/').IsValid() is False # is only root
    assert nerve.Path('R:/A B').IsValid() is False # Aphanumberic
    assert nerve.Path('R:/A[]').IsValid() is False # Illegal Characters
    assert nerve.Path('R:/Aα').IsValid() is False # is English

    assert nerve.Path('R:/jobs/nerve').IsValid() is True
    assert nerve.Path('R:/jobs/nerve/').IsValid() is True


    # GetParent
    assert nerve.Path('/A/B').GetParent() == '/A'
    assert nerve.Path('/A/B/C').GetParent(2) == '/A'

    # HasParent
    assert nerve.Path('/A/B').HasParent() is True
    assert nerve.Path('A').HasParent() is False

    # GetRelative
    assert nerve.Path('/A/B').GetRelative(-1) == 'B'
    assert nerve.Path('/A/B/C').GetRelative(-2) == 'B/C'
    assert nerve.Path('/A/B').GetRelative(1) == 'A'
    assert nerve.Path('/A/B/C').GetRelative(2) == 'A/B'

    assert nerve.Path('R:/jobs').IsAbsolute() == True

    # GetHead
    assert nerve.Path('/A/B').GetHead() == 'B'

    # GetFilename
    assert nerve.Path('/A/B.txt').GetFileName() == 'B'

    # GetExtension
    assert nerve.Path('/A/B.txt').GetExtension() == 'txt'

    # IsDir IsFile
    assert nerve.Path('/A/B').IsDir() is True
    assert nerve.Path('/A/B.txt').IsFile() is True

    # Exists
    assert nerve.Path('$TEMP').Exists() is True

    # Set/Create/Remove Folder
    path = nerve.Path('$TEMP') + '/Tests'
    path.Create()
    assert path.Exists() is True
    path.Remove()
    assert path.Exists() is False

    # Set/Create/Remove File
    path = nerve.Path('$TEMP') + '/NerveTestFile.txt'
    path.SetContent('Nerve Test File Content.')
    path.Create()
    assert path.Exists() is True

    path = nerve.Path('$TEMP') + '/NerveTestFile.txt'
    assert path.Read() == 'Nerve Test File Content.'

    # SetContent can be another file, content is copied
    pathB = nerve.Path('$TEMP') + '/NerveTestFileB.txt'
    pathB.SetContent(path)
    pathB.Create()
    assert pathB.Read() == 'Nerve Test File Content.'

    path.Remove()
    pathB.Remove()
    assert path.Exists() is False
    assert pathB.Exists() is False

    # Versions
    path = nerve.Path('/A/B_v1.txt')
    assert path.HasVersion() is True
    assert path.GetVersion() == 1
    assert path.GetStringVersion() == 'v1'

    path = nerve.Path('/A/B_v02.txt')
    assert path.HasVersion() is True
    assert path.GetVersion() == 2
    assert path.GetStringVersion() == 'v02'

    path = nerve.Path('/A/B_v003.txt')
    assert path.HasVersion() is True
    assert path.GetVersion() == 3
    assert path.GetStringVersion() == 'v003'

    path = nerve.Path('/A/B.txt')
    assert path.HasVersion() is False

    # Glob
    path = nerve.Path('$TMP') + 'nerve'
    path.Create()
    for name in ['A.txt', 'B.txt', 'C.txt']:
        p = path + name
        p.Create()

    files = nerve.Path.Glob( path.AsString() + '/*.txt' )
    assert files[0].GetHead() == 'A.txt'
    assert files[1].GetHead() == 'B.txt'
    assert files[2].GetHead() == 'C.txt'

    for name in ['A.txt', 'B.txt', 'C.txt']:
        p = path + name
        p.Remove()

    assert not files[0].Exists()
    assert not files[1].Exists()
    assert not files[2].Exists()

    print('# Passed Path Tests.')

def ImageTests():
    image = nerve.Image()
    file = image.GetFile()
    assert file is not None
    image.Load('C:/users/lemon/Desktop/test.jpg')

    print('# Passed Image tests')

def ShotTests():
    job = nerve.Shot()
    job.Create()

    seq = nerve.Shot('SEQ')
    seq.Create()

    
    shot = nerve.Shot('SEQ/SHOT')
    shot.Create()

    seq2 = nerve.Shot('SEQ2')
    seq2.Create()
        

    shot1 = nerve.Shot('SEQ2/SHOT1')
    shot1.Create()
    shot2 = nerve.Shot('SEQ2/SHOT2')
    shot2.Create()

    assert seq.HasParentShot() is True
    assert shot.HasParentShot() is True

    assert job.HasParentShot() is False
    assert seq.HasParentShot() is True
    assert shot.HasParentShot() is True

    assert seq.GetParentShot().GetName() == 'job'
    assert shot.GetParentShot().GetName() == 'SEQ'

    assert job.GetChildren() == ['SEQ', 'SEQ2']
    assert seq.GetChildren() == ['SHOT']

    print('Passed all Shot Tests')

def SublayerTests():

    sublayer = nerve.Sublayer('test', layer='SEQ/SHOT', version=1)

    # Clean Previous Files
    if sublayer.GetFilePath().Exists():
        sublayer.GetFilePath().Remove()
    if sublayer.GetFilePath('session').GetParent().Exists():
        sublayer.GetFilePath('session').GetParent().Remove(recursive=True)

    layer = nerve.USD.CreateOrOpen( sublayer.GetFilePath('session') )
    layer.Save()
    sublayer.Create()
    assert sublayer.GetVersions() == [1]
    assert sublayer.GetFormats() == ['usd']

    sublayer = nerve.Sublayer('test', layer='SEQ/SHOT', format='abc', version=1)
    sublayer.GetFilePath('session').Create()
    sublayer.Create()
    assert sublayer.GetFormats() == ['abc', 'usd']

    sublayer = nerve.Sublayer('test', layer='SEQ/SHOT', format='abc', version=2)
    sublayer.GetFilePath('session').Create()
    sublayer.Create()
    assert sublayer.GetFormats() == ['abc']

    layer = nerve.Layer('SEQ/SHOT')
    assert layer.GetSublayers() == ['test']

def AssetTests():

    # Simple Asset
    asset = nerve.Asset('test')
    asset.CreateDummySession()
    asset.Create()
    assert asset.GetFilePath().Exists() is True
    assert asset.Exists() == True
    
    # Asset with parent
    assert asset.HasParent() is False
    asset = nerve.Asset('parent/child')
    asset.CreateDummySession()
    asset.Create()
    assert asset.HasParent() is True
    parent = asset.GetParent()

    AssetTestsOLD()

    print('# Passed Asset tests')

def AssetTestsOLD():
    # Create test asset modelA
    asset = nerve.Asset('modelA', version=1)
    layer = nerve.USD.CreateOrOpen( asset.GetFilePath('session') )
    layer.Save()
    asset.Create()
    assert asset.Exists() is True
    assert asset.HasParent() is False

    # Create test asset modelB
    asset = nerve.Asset('blah/ModelB', version=1)
    layer = nerve.USD.CreateOrOpen( asset.GetFilePath('session') )
    layer.Save()

    asset.Create()
    assert asset.Exists() is True
    assert asset.HasParent() is True

    # Create test asset modelC
    asset = nerve.Asset('ModelC', description='DESC', version=1, frameRange=(1,10), comment='Comment!')
    layer = nerve.USD.CreateOrOpen( asset.GetFilePath('session') )
    layer.Save()
    asset.Create()
    assert asset.Exists() is True
    assert asset.HasParent() is False

    asset = nerve.Asset('ModelC', version=1)
    assert asset.GetDescription() == 'DESC'

    job = nerve.Job('$TEMP/nerve2')
    if not job.Exists():
        job.Create()
    
    asset = nerve.Asset( 'grp/asset', version=1, job=job.GetDir())
    asset.CreateDummySession()
    asset.Create()
    assert asset.GetFilePath('session').Exists() is True

    asset = nerve.Asset('modelA')
    asset.SetJob("$TEMP/nerve/lib")
    assert asset.GetFilePath() == 'C:/Users/lemon/AppData/Local/Temp/nerve/lib/nerve/assets/modelA.usda'

    layer = nerve.USD.CreateOrOpen( asset.GetFilePath('session') )
    layer.Save()
    asset.Create()

def AppTests():
    import nerve.apps
    job = nerve.Job()

    apps = ['maya', 'houdini']
    for appname in apps:
        app = getattr(nerve.apps, appname)(job.GetDir())
        app.Create()

def JobTests():
    job = nerve.Job()

    if job.Exists():
        job.Delete()

    assert job.Exists() is False

    job.Create()
    assert job.Exists() is True

    assert job.GetAssets() == []

    job = nerve.Job('$TEMP/nerve2')
    job.Create()
    assert job.Exists() is True
    job.Delete()
    assert job.Exists() is False

    print('# Passed all Job tests')

def FormatTests():
    pass


def HDRITests():
    hdri = nerve.HDRI('hdri')
    hdri.Export('C:/users/lemon/Desktop/sunset.hdr')

    print('# Passed All HDRI tests')

NewJob()

#PathTests()
#ImageTests()
#JobTests()
#AssetTests()
#AssetTestsOLD()
#ShotTests()
#SublayerTests()
#AssetTests()
HDRITests()


#AppTests()


#print('#')
print('# ALL TESTS PASSED.')
print('##')
