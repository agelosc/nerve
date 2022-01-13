from django import forms
import nerve


class job_create(forms.Form):
    path = forms.CharField(label='Create Job')

    def clean_path(self):
        path_create = nerve.Path(self.cleaned_data.get('path'))

        segments = path_create.segments.copy()
        if not path_create.IsAbsolute():
            raise forms.ValidationError('Path is not absolute.')
        if not segments[0]:
            segments.pop(0)

        if segments[0][1] != ':':
            raise forms.ValidationError('Drive Letter missing.')
        if segments[0][0] not in nerve.Path.GetDrives():
            raise forms.ValidationError('Drive Letter not available.')
        segments.pop(0)
        for seg in segments:
            if not seg.isalnum() or nerve.String.IllegalCharacters(seg):
                raise forms.ValidationError('Path should only include letters or numbers.')
            if not nerve.String.isEnglish(seg):
                raise forms.ValidationError('Only English characters allowed.')

        if path_create.Exists() and nerve.Job(path_create).Exists():
            raise forms.ValidationError('Job already exists.')

        return path_create.AsString()

class job_add(forms.Form):
    path = forms.CharField(label='Add Job')

    def clean_path(self):
        path_add = nerve.Path(self.cleaned_data.get('path'))

        segments = path_add.segments.copy()
        if not path_add.IsAbsolute():
            raise forms.ValidationError('Path is not absolute.')
        if not segments[0]:
            segments.pop(0)

        if segments[0][1] != ':':
            raise forms.ValidationError('Drive Letter missing.')
        if segments[0][0] not in nerve.Path.GetDrives():
            raise forms.ValidationError('Drive Letter not available.')
        segments.pop(0)
        for seg in segments:
            if not seg.isalnum() or nerve.String.IllegalCharacters(seg):
                raise forms.ValidationError('Path should only include letters or numbers.')
            if not nerve.String.isEnglish(seg):
                raise forms.ValidationError('Only English characters allowed.')

        if not path_add.Exists():
            raise forms.ValidationError('Job does not exist.')

        return path_add.AsString()

class asset_add(forms.Form):
    job = forms.CharField(label="Job")
    path = forms.CharField( label='Path')
    #name = forms.CharField(label='Name')
    file = forms.CharField(label="File")

    FORMATS = (("One", "one"), ("Two", "two"))
    format = forms.TypedChoiceField(
        label="Format",
        choices=FORMATS,
        widget=forms.Select(attrs={'class': "form-control"})
    )

    VERSIONS = (("One", "one"), ("Two", "two"))
    version = forms.TypedChoiceField(
        label="Version",
        choices=VERSIONS,
        widget=forms.Select(attrs={'class': "form-control"})
    )
