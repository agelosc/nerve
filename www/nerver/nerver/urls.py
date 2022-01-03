"""nerver URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.jobs, name='jobs'),
    path('assets/', views.assets, name="job"),
    path('asset_add/', views.asset_add, name="asset_add"),


    path('image/<path:path>', views.image, name="image"),

    path('job_app', views.job_app, name='job_app'),
    path('browse', views.browse, name='browse'),


    path('job_add', views.job_add, name='job_add'),
    path('job/<path:job>', views.job, name="job"),
    path('thumbnail/', views.thumbnail, name="thumbnail"),

    path('asset/<path:asset>', views.asset, name='asset')
]
