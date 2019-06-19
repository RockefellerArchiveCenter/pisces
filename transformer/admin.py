from django.contrib import admin

from .models import *


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    pass


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
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


@admin.register(Object)
class ObjectAdmin(admin.ModelAdmin):
    pass


@admin.register(FetchRun)
class FetchRunAdmin(admin.ModelAdmin):
    pass


@admin.register(TransformRun)
class TransformRunAdmin(admin.ModelAdmin):
    pass
