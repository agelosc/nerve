import nerve

import sys, os
print(sys.version)
print('')

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

def LayerTests():
    layer = nerve.Layer()
    layer.Create()

    seq = nerve.Layer('SEQ')
    seq.Create()

    shot = nerve.Layer('SEQ/SHOT')
    shot.Create()

    seq2 = nerve.Layer('SEQ2')
    seq2.Create()

    shot1 = nerve.Layer('SEQ2/SHOT1')
    shot1.Create()
    shot2 = nerve.Layer('SEQ2/SHOT2')
    shot2.Create()

    assert seq.HasParentLayer() is True
    assert shot.HasParentLayer() is True

    assert layer.HasParentLayer() is False
    assert seq.HasParentLayer() is True
    assert shot.HasParentLayer() is True

    assert seq.GetParentLayer().GetName() == 'job'
    assert shot.GetParentLayer().GetName() == 'SEQ'

    assert layer.GetChildren() == ['SEQ', 'SEQ2']
    assert seq.GetChildren() == ['SHOT']

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
    asset = nerve.Asset('modelA')

    layer = nerve.USD.CreateOrOpen( asset.GetFilePath('session') )
    layer.Save()
    asset.Create()

    asset = nerve.Asset('blah/ModelB')
    layer = nerve.USD.CreateOrOpen( asset.GetFilePath('session') )
    layer.Save()
    asset.Create()

def LibTests():
    asset = nerve.Asset('modelA')
    asset.SetJobPath("$TEMP/nerve/lib")
    print(asset.GetFilePath())

    layer = nerve.USD.CreateOrOpen( asset.GetFilePath('session') )
    layer.Save()
    asset.Create()

def AppTests():
    import nerve.apps
    path = 'C:/testProj'
    if nerve.Path(path).Exists():
        nerve.Path(path).Remove(True)

    apps = ['maya', 'houdini']
    for a in apps:
        app = getattr(nerve.apps, a)(path)



        app.Create()

#PathTests()

asset = nerve.Asset('test', job='R:/lib')
print(asset.paths)

#LayerTests()
#SublayerTests()
#AssetTests()
#LibTests()
#AppTests()

'''
import tkinter as tk
from tkinter import filedialog
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename()
'''

print('######################')
print('## All Tests Passed ##')
print('######################')
