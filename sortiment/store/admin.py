from django.contrib import admin
from django.contrib.admin import ModelAdmin
from store import models
from store.models import Reset


class ProductAdmin(ModelAdmin):
    list_display = (
        "name",
        "barcode",
        "price",
        "is_unlimited",
        "is_dummy",
    )
    list_filter = (
        "is_unlimited",
        "is_dummy",
    )


class WarehouseAdmin(ModelAdmin):
    list_display = (
        "name",
        "ip",
    )


class WarehouseState(ModelAdmin):
    list_display = (
        "warehouse",
        "product",
        "quantity",
        "total_price",
    )


class WarehouseEventAdmin(ModelAdmin):
    list_display = (
        "product",
        "warehouse",
        "quantity",
        "price",
        "timestamp",
        "type",
        "user",
    )
    list_filter = ("type",)


@admin.register(Reset)
class ResetAdmin(admin.ModelAdmin):
    list_display = ["created_at", "user", "price_diff"]


admin.site.register(models.Product, ProductAdmin)
admin.site.register(models.Warehouse, WarehouseAdmin)
admin.site.register(models.WarehouseState, WarehouseState)
admin.site.register(models.WarehouseEvent, WarehouseEventAdmin)
admin.site.register(models.Tag)
