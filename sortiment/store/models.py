from django.conf import settings
from django.db import models


class Warehouse(models.Model):
    name = models.CharField(max_length=32)
    ip = models.GenericIPAddressField(unique=True)

    def get_products_price_for_sale_sum(self):
        return sum(
            state.quantity * state.product.price
            for state in WarehouseState.objects.filter(warehouse=self)
        )

    def get_products_price_when_buy_sum(self):
        return sum(
            state.total_price for state in WarehouseState.objects.filter(warehouse=self)
        )

    @staticmethod
    def get_global_products_price_for_sale_sum():
        return sum(
            state.quantity * state.product.price
            for state in WarehouseState.objects.all()
        )

    @staticmethod
    def get_global_products_price_when_buy_sum():
        return sum(state.total_price for state in WarehouseState.objects.all())

    def __str__(self):
        return f"{self.name}; {self.ip}"


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

    def __str__(self):
        return f"{self.name}; {self.price}"

    def buy(self, quantity, warehouse, user):
        WarehouseEvent(product=self,
                       warehouse=warehouse,
                       quantity=-quantity,
                       price=self.price,
                       type=WarehouseEvent.EventType.PURCHASE,
                       user=user).save()
        user.credit -= self.price*quantity
        user.save()


class WarehouseState(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["warehouse", "product"], name="whstate_wh_prod_unique"
            )
        ]

    def __str__(self):
        return f"{self.warehouse}; {self.product}; {self.quantity}"


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

    def save(self, *args, **kwargs):

        ws = WarehouseState.objects.filter(
            product=self.product, warehouse=self.warehouse
        ).first()

        if not ws:
            ws = WarehouseState()
            ws.quantity = 0
            ws.total_price = 0
            ws.warehouse = self.warehouse
            ws.product = self.product

        ws.quantity = ws.quantity + self.quantity
        ws.total_price = ws.total_price + self.price * self.quantity
        ws.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.warehouse}; {self.product}; {self.timestamp}"
