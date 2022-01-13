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

    nerve.String.pprint(context)

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
