"""
URL configuration for TraceFlow project.
"""
from django.contrib import admin
from django.urls import path, include
from forensics.api import api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),  # Django Ninja API
    path('', include('forensics.urls')),  # Forensics app URLs
]
