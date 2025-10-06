from django import forms
from .models import UploadedMedia

class MediaUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedMedia
        fields = ["file"]
