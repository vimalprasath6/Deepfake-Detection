from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import index1_view, upload_file, analyze_file, analyze_media
from Application.views import analyze_url  # Import your view


urlpatterns = [
    path("", index1_view, name="index"),
    path("upload/", upload_file, name="upload_file"),
    path("analyze/", analyze_file, name="analyze_file"),
    path("deepfake/analyze/", analyze_media, name="analyze_media"),
    path("analyze_url/", analyze_url, name="analyze_url"),  # Make sure this exists!
]

# Serve media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
