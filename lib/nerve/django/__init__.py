import nerve


class Base:
    pass

class Asset(nerve.Asset, Base):
    def __init__(self, path='', **kwargs):
        nerve.Asset.__init__(self, path, **kwargs)
        if 'version' in kwargs.keys() and kwargs['version'] == -1:
            del kwargs['version']

        self.url = kwargs
        self.url['path'] = path
        self.layerData = self.LoadCustomLayerData()
        self.formatData = self.GetFormatData()

    def GetUrl(self):
        pair = []
        for key in self.url.keys():
            pair.append('{}={}'.format(key, self.url[key]))
        return '?'+'&'.join(pair)

    def GetUrlFormat(self):
        pair = []
        for key in ['job', 'path']:
            pair.append('{}={}'.format(key, self.data[key]))
        pair.append( 'format='+self.GetFormat() )
        return '?'+'&'.join(pair)

    def GetUrlVersion(self):
        pair = []
        for key in ['job', 'path']:
            pair.append('{}={}'.format(key, self.data[key]))
        pair.append( 'version='+str(self.GetVersion()) )            
        return '?'+'&'.join(pair)

    def GetUrlVersionFormat(self):
        pair = []
        for key in ['job', 'path']:
            pair.append('{}={}'.format(key, self.data[key]))
        pair.append( 'format='+self.GetFormat() )
        pair.append( 'version'+str(self.GetVersion()) )
        return '?'+'&'.join(pair)
        

    def IsGroup(self):
        if not self.GetPath():
            return True
        return 'version' not in self.layerData.keys()

    def GetCover(self):
        return self.GetFilePath('cover').AsString()

    def GetDescription(self):
        key = 'description'
        return self.layerData[key] if key in self.layerData.keys() else ''
    
    def GetDate(self):
        key = 'date'
        return self.formatData[key] if key in self.formatData.keys() else ''

    def GetUser(self):
        key = 'user'
        return self.formatData[key] if key in self.formatData.keys() else '' 

    def GetComment(self):
        key = 'comment'
        return self.formatData[key] if key in self.formatData.keys() else ''

    def GetVersionsAsDict(self):
        data = {}
        for version in self.GetVersions():
            data[version] = nerve.String.versionAsString(version)
        return data

    def GetFormatsAsDict(self):
        data = {}
        for format in self.GetFormats():
            data[format] = nerve.Format(format).GetLong()
        return data

    def GetFormatLong(self):
        return nerve.Format( self.GetFormat() ).GetLong()

class Job(nerve.Job, Base):
    def __init__(self, job=None, **kwargs):
        nerve.Job.__init__(self, job, **kwargs)

    def GetJobPath(self):
        return self.GetFilePath('job')

    def GetCover(self):
        return self.GetFilePath('cover').AsString()

    

        

    
