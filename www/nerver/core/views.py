from django.shortcuts import render
from django.views import View
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, Http404, FileResponse
from . import forms

from glob import glob
from importlib import reload
from datetime import datetime
import os, subprocess

import nerve
import nerve.apps
import nerve.django

class Action:
    @staticmethod
    def App(request):
        if "ajax" not in request.POST.keys():
            return HttpResponse('')

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

    @staticmethod
    def ajax(request):
        if not 'action' in request.POST.keys():
            return HttpResponse('action not defined.')
        
        if not hasattr(Action, request.POST['action']):
            return HttpResponse('action does not exist.')

        return getattr(Action, request.POST['action'])(request)
        
    @staticmethod
    def job_create(request):
        path = nerve.String.FileDialog(mode='dir', title='Create Job')
        if not path:
            return HttpResponse('Job Create canceled.')
        
        Job = nerve.Job( path )
        if not Job.Exists():
            Job.Create()
        Job.AddToRecent(path)
       
        return HttpResponse('')

    @staticmethod
    def job_add(request):
        path = nerve.String.FileDialog(mode='dir', title='Add Job')
        if not path:
            return HttpResponse('Job Add Canceled.')
        
        Job = nerve.Job(path)
        if not Job.Exists():
            return HttpResponse('Invalid Job path.')

        Job.AddToRecent(Job.GetDir())
        return HttpResponse('')

    @staticmethod
    def job_remove(request):
        if 'path' not in request.POST.keys():
            return HttpResponse('Job path not set')
        
        path = request.POST.get('path')
        nerve.Job.RemoveFromRecents(path)
        return HttpResponse('Job removed from recents')

    @staticmethod
    def asset_modal(request):
        job = request.POST['job']
        path = request.POST['path']
        asset = nerve.Asset(job=job, path=path)
        return render(request, 'asset.html', {'asset':asset.Serialize(deep=True)})

    @staticmethod
    def asset(request):
        args = request.POST.get('url')
        asset = nerve.Asset.url( request.POST.get('url') ).Load()
        print(asset)
        return JsonResponse( asset.data )

    @staticmethod
    def load_app(request):
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

class Job(View):
    def get(self, request, *args, **kwargs):
        job_list = []
        context = {'job_list': job_list}
        for recent in nerve.Job.GetRecent():
            Job = nerve.django.Job(recent)
            job_list.append( Job )
        response = render(request, 'jobs.html', context)
        return response

    def post(self, request, *args, **kwargs):
        job = nerve.django.Job( request.POST.get('path') )
        job.SetPrettyName( request.POST.get('name') )
        return self.get(request)

class Asset(View):
    def get(self, request):
        job = nerve.django.Job( request.GET.get('job') )
        if not job.Exists():
            context = {'msg': 'The job requested does not exist.'}
            return render(request, '404.html', context, status=404)

        args = request.GET.dict()
        args['version'] = int(args['version']) if 'version' in args.keys() else -1
        asset = nerve.django.Asset( **args )

        return render(request, "assets.html", {'asset':asset, 'job':job})

        context['job'] = Job.Serialize()
        context['asset'] = Asset.Serialize(deep=not Asset.IsGroup())

        context['asset_list'] = []
        for child in Asset.GetChildren():
            args['path'] = Asset.GetPath() + child
            Child = nerve.Asset( **args )
            context['asset_list'].append( Child.Serialize() )

        response = render(request, 'assets.html', context)
        return response

def snippets(request):
    return render(request, "snippets.html")

def image(request, path):
    return FileResponse(open(path, 'rb'))

def jobs(request):
    job_list = []
    for recent in nerve.Job.GetRecent():
        Job = nerve.Job(recent)
        job_list.append( Job.JsonEncode() )

    context = {'job_list': job_list }
    response = render(request, 'jobs.html', context)
    return response

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
            form_add = forms.job_add(request.POST)
            if form_add.is_valid():
                path = form_add.cleaned_data.get('path')
                job = nerve.Job( path )
                nerve.Job.AddToRecent(path)
                return HttpResponseRedirect('/')
        else:
            form_add = forms.job_add()

        if 'job_create' in request.POST:
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
    return HttpResponse('')
    #return render(request, "asset.html", {})

def assets(request):
    job = request.GET['job'] if 'job' in request.GET.keys() else None

    Job = nerve.Job(job)
    if not Job.Exists():
        context = {'msg': 'The job you requested was not found.'}
        return render(request, '404.html', context, status=404)

    context = {}

    args = request.GET.dict()
    context['GET'] = args
    args['version'] = request.GET['version'] if 'version' in request.GET.keys() else -1
    Asset = nerve.Asset( **args )

    context['job'] = Job.JsonEncode()
    context['asset'] = Asset.JsonEncode(usd=Asset.Exists())
    context['asset']['showbackbtn'] = True

    context['asset_list'] = []
    for child in Asset.GetChildren():
        args['path'] = Asset.GetPath() + child
        Child = nerve.Asset( **args )
        context['asset_list'].append( Child.JsonEncode()  )


    return render(request, "assets.html", context)

def asset_add(request):
    args = request.GET.dict()
    context = {}
    context['GET'] = args

    form = forms.asset_add()
    context['form'] = form
    return render(request, "asset_add.html", context)

def FileUploadTo(file, path):
    with open(str(path), 'wb+') as dest:
        for chunk in file.chunks():
            dest.write(chunk)

def cover(request):

    if 'job' not in request.GET.keys():
        return HttpResponseRedirect('/')


    job = request.GET['job']

    if 'asset' in request.GET.keys():
        pass
    if 'sublayer' in request.GET.keys():
        pass

    Job = nerve.Job(job)
    #FileUploadTo(request.FILES['file'], Job.GetFilePath('cover') )
    image = nerve.Image()
    tmp = image.GetFile()

    if not tmp.GetParent().Exists():
        tmp.Create()

    FileUploadTo(request.FILES['file'], str(tmp))
    image.Load(tmp)

    image.Square()
    image.Save()
    image.GetFile().Copy( Job.GetFilePath('cover') )

    return HttpResponse('/')

def browse(request):
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename()
    root.destroy()

    return HttpResponse(file_path)
