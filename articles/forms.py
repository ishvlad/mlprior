from django import forms


class AddBlogPostForm(forms.Form):
    title = forms.CharField(max_length=100)
    url = forms.URLField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['title'].widget.attrs['class'] = 'form-control'
        self.fields['url'].widget.attrs['class'] = 'form-control'
