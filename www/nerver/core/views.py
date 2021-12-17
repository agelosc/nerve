from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, Http404, FileResponse
from . import forms

from glob import glob
from importlib import reload
from datetime import datetime
import os, subprocess

import nerve
import nerve.apps

def image(request, path):
    return FileResponse(open(path, 'rb'))

def index(request):

    job_list = []
    for recent in nerve.Job.GetRecent():
        data = {}
        Job = nerve.Job(recent)
        data['path'] = recent
        data['name'] = nerve.Path(recent).GetHead()
        data['hasCover'] = Job.GetCoverPath().Exists()
        data['cover'] = Job.GetCoverPath()

        job_list.append(data)

    context = {'job_list': job_list }
    return render(request, 'jobs.html', context)

def job_app(request):
    if "ajax" in request.POST.keys():
        path = request.POST['path']
        app = request.POST['app']

        if app == 'explore':
            subprocess.Popen( ['start', path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT , shell=True)
            return HttpResponse('')

        if hasattr(nerve.apps, app):
            appobj = getattr(nerve.apps, app)(path).Load()
            date = datetime.now().strftime('%a %d %b %y %H:%M:%S')
            return HttpResponse('[{0}] Loading {1}...'.format(date, app))

        return HttpResponse('')

def job_add(request):
    if request.method == 'POST':
        if 'job_add' in request.POST:
            print("JOB_ADD")
            form_add = forms.job_add(request.POST)
            if form_add.is_valid():
                path = form_add.cleaned_data.get('path')
                job = nerve.Job( path )
                nerve.Job.AddToRecent(path)
                return HttpResponseRedirect('/')
        else:
            form_add = forms.job_add()

        if 'job_create' in request.POST:
            print("JOB_CREATE")
            form_create = forms.job_create(request.POST)
            if form_create.is_valid():
                path = form_create.cleaned_data.get('path')
                job = nerve.Job( path )
                job.Create()
                nerve.Job.AddToRecent(path)
                return HttpResponseRedirect('/')
        else:
            form_create = forms.job_create()
    else:
        form_add = forms.job_add()
        form_create = forms.job_create()

    return render(request, 'job_add.html', {'form_add':form_add, 'form_create':form_create } )

def job(request, job):
    j = nerve.Job(job)
    if not j.Exists():
        context = {'msg': 'The job you requested was not found.'}
        return render(request, '404.html', context, status=404)

    context = {'job':job}
    return render(request, "job.html", context)

def asset(request, asset):
    return render(request, "asset.html", {})

def GetAssetData(Asset, details=False):
    data = {}
    allformats = nerve.GetFormats()

    data['exists'] = Asset.Exists()
    data['name'] = Asset.GetName()
    data['path'] = Asset.GetPath().AsString()
    data['file'] = Asset.GetFilePath().AsString()
    data['format'] = allformats[Asset.GetFormat()]
    data['hasChildren'] = Asset.HasChildren()
    #print(Asset.GetChildren())
    data['hasParent'] = data['path'] == ''
    data['parent'] = nerve.Path(data['path']).GetParent().AsString()
    data['versions'] = [ (v, nerve.versionAsString(v)) for v in Asset.GetVersions(fromDisk=True) ]

    data['version'] = Asset.GetVersion()
    data['versionAsString'] = Asset.GetVersionAsString()

    data['formats'] = []

    if(details):
        assetData = Asset.GetAssetInfo()
        data['description'] = assetData['description'] if 'description' in assetData.keys() else ''
        data['date'] = assetData['date']
        data['user'] = assetData["user"]
        for asset_format in Asset.GetFormats():
            if asset_format in allformats.keys():
                data['formats'].append( (asset_format,allformats[asset_format]) )

        #data['formats'] = Asset.GetFormats()
    #nerve.pprint(data)

    return data

def assets(request, job):
    Job = nerve.Job(job)
    if not Job.Exists():
        context = {'msg': 'The job you requested was not found.'}
        return render(request, '404.html', context, status=404)

    path = request.GET['path'] if 'path' in request.GET.keys() else ''
    version = request.GET['version'] if 'version' in request.GET.keys() else -1
    format = request.GET['format'] if 'format' in request.GET.keys() else 'usd'

    Asset = nerve.Asset(job=job, path=path, version=version)

    context = {}
    context['job'] = job
    context['asset'] = {'exists':False }
    if Asset.Exists():
        context['asset'] = GetAssetData(Asset, details=True)

    context['asset_list'] = []
    for child in Asset.GetChildren():
        Child = nerve.Asset( job=job, path=Asset.GetPath()+child, version=version )
        context['asset_list'].append( GetAssetData(Child) )

    return render(request, "assets.html", context)

def FileUploadTo(file, path):
    with open(str(path), 'wb+') as dest:
        for chunk in file.chunks():
            dest.write(chunk)

def thumbnail(request):

    if 'job' not in request.GET.keys():
        return HttpResponseRedirect('/')
    job = request.GET['job']

    if 'asset' in request.GET.keys():
        pass

    if 'sublayer' in request.GET.keys():
        pass

    Job = nerve.Job(job)
    FileUploadTo(request.FILES['file'], Job.GetCoverPath() )

    return HttpResponse('/')
