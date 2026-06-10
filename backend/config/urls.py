"""
Root URL Configuration — Phase 2.

Added: media file serving for development.
In production, a real web server (nginx) handles media files instead.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]

# Serve uploaded media files during development.
# static() returns URL patterns that map MEDIA_URL → MEDIA_ROOT.
# This only activates when DEBUG = True — safe for dev, not for production.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
