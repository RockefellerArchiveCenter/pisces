from django.contrib import admin

from .models import *


@admin.register(FetchRun)
class FetchRunAdmin(admin.ModelAdmin):
    pass
