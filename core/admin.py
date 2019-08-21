# Register your models here.
# users/admin.py
from django.contrib import admin

from .models import Feedback, User, Profile, PremiumSubscription

admin.site.register(Feedback)
admin.site.register(User)
admin.site.register(Profile)
admin.site.register(PremiumSubscription)
