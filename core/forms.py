from allauth.account.forms import LoginForm, SignupForm
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import User


# class MyCustomLoginForm(LoginForm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         self.fields['login'].widget.attrs['class'] = 'form-control'
#         self.fields['password'].widget.attrs['class'] = 'form-control'
#
#     def login(self, *args, **kwargs):
#         return super(MyCustomLoginForm, self).login(*args, **kwargs)
#
#
# class MyCustomSignupForm(SignupForm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         self.fields['email'].widget.attrs['class'] = 'form-control'
#         self.fields['password1'].widget.attrs['class'] = 'form-control'
#
#     def save(self, request):
#         # Ensure you call the parent classes save.
#         # .save() returns a User object.
#         user = super(MyCustomSignupForm, self).save(request)
#
#         # Add your own processing here.
#
#         # You must return the original result.
#         return user
#
#
# class CustomUserCreationForm(UserCreationForm):
#     class Meta(UserCreationForm):
#         model = User
#         fields = ('username', 'email')
#
#
# class CustomUserChangeForm(UserChangeForm):
#     class Meta:
#         model = User
#         fields = ('username', 'email')
#
#
# class FeedbackForm(forms.Form):
#     name = forms.CharField()
#     email = forms.EmailField()
#
#     message = forms.CharField(widget=forms.Textarea)
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         self.fields['name'].widget.attrs['class'] = 'form-control'
#         self.fields['email'].widget.attrs['class'] = 'form-control'
#         self.fields['message'].widget.attrs['class'] = 'form-control'

