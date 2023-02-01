from django.contrib import admin
from store import models

admin.site.register(models.Product)
admin.site.register(models.Warehouse)
admin.site.register(models.WarehouseState)
admin.site.register(models.WarehouseEvent)
admin.site.register(models.Tag)
