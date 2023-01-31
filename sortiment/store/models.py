from django.conf import settings
from django.db import models


class Warehouse(models.Model):
    name = models.CharField(max_length=32)


class Tag(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=128)
    barcode = models.CharField(max_length=32, unique=True)
    image = models.FileField(blank=True, null=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    is_unlimited = models.BooleanField()
    tags = models.ManyToManyField(Tag, blank=True)
    total_price = models.DecimalField(max_digits=16, decimal_places=2)


class WarehouseState(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()


class WarehouseEvent(models.Model):
    class EventType(models.IntegerChoices):
        IMPORT = 0, "import"
        PURCHASE = 1, "purchase"
        TRANSFER_IN = 2, "transfer in"
        TRANSFER_OUT = 3, "transfer out"
        DISCARD = 4, "discard"
        CORRECTION = 5, "correction"

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    type = models.IntegerField(choices=EventType.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
