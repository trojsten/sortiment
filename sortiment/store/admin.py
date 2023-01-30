from django.contrib import admin
from .models import *

admin.site.register(Product)
admin.site.register(Warehouse)
admin.site.register(WarehouseState)
admin.site.register(WarehouseEvent)
admin.site.register(Tag)