from django.contrib import admin

from .models import FetchRun


@admin.register(FetchRun)
class FetchRunAdmin(admin.ModelAdmin):
    pass
