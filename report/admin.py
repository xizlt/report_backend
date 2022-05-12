from django.contrib import admin
from report.models import *


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('phone', 'entity', 'name', 'loyalty_program')
    list_filter = ('phone', 'loyalty_program')
    search_fields = ('phone', 'name')


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Nomenclature)
class NomenclatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'price',)
    list_filter = ('name', 'code',)
    search_fields = ('name', 'code',)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'region',)
    list_filter = ('name', 'code', 'region',)
    search_fields = ('name', 'code',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'region', 'code_1c', 'bonuses', 'date', 'operation_type', 'event_type', 'currency',)
    list_filter = ('region', 'code_1c', 'date', 'operation_type', 'event_type', 'currency',)
    search_fields = ('code_1c',)


@admin.register(Gifts)
class GiftsAdmin(admin.ModelAdmin):
    list_display = ("id", "phone", "gift_id", "nominal", "created",)
    list_filter = ("phone", "gift_id", "nominal", "created",)
    search_fields = ('phone', 'gift_id')
