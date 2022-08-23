from django.contrib import admin

from .models import ConfigurationChoice, ConfigurationList


class ConfigurationChoiceInline(admin.TabularInline):
    model = ConfigurationChoice


@admin.register(ConfigurationList)
class ConfigurationListAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    inlines = [ConfigurationChoiceInline]
