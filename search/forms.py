

from django import forms

from articles.models import Article


class SearchForm(forms.ModelForm):
    birth_country = forms.ModelChoiceField(
        queryset=Article.objects.all(),
    )

    class Meta:
        model = Article
        fields = ('__all__')

