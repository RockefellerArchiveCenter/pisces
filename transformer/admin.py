from django.contrib import admin

from .models import Agent, Identifier, SourceData, TransformRun


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    pass


@admin.register(SourceData)
class SourceDataAdmin(admin.ModelAdmin):
    pass


@admin.register(Identifier)
class IdentifierAdmin(admin.ModelAdmin):
    pass


@admin.register(TransformRun)
class TransformRunAdmin(admin.ModelAdmin):
    pass
