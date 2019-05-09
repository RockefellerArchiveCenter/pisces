from django.contrib import admin

from .models import Agent, Identifier, SourceData, Collection


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    pass


@admin.register(SourceData)
class SourceDataAdmin(admin.ModelAdmin):
    pass


@admin.register(Identifier)
class IdentifierAdmin(admin.ModelAdmin):
    pass


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    pass
