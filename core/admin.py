# Register your models here.
# users/admin.py
from django.contrib import admin

# from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import Feedback

# class CustomUserAdmin(UserAdmin):
#     add_form = CustomUserCreationForm
#     form = CustomUserChangeForm
#     model = User
#     list_display = ['email', 'username',]
#
admin.site.register(Feedback)
