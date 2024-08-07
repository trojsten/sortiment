from django.conf import settings
from django.db import models


class Warehouse(models.Model):
    name = models.CharField(max_length=32)
    ip = models.GenericIPAddressField(unique=True)

    def __str__(self):
        return self.name

    def get_products_price_for_sale_sum(self):
        return sum(
            state.quantity * state.product.price
            for state in WarehouseState.objects.filter(warehouse=self, quantity__gt=0)
            if not state.product.is_dummy and not state.product.is_unlimited
        )

    def get_products_price_when_buy_sum(self):
        return sum(
            state.total_price
            for state in WarehouseState.objects.filter(warehouse=self, quantity__gt=0)
            if not state.product.is_dummy and not state.product.is_unlimited
        )

    @staticmethod
    def get_global_products_price_for_sale_sum():
        return sum(
            state.quantity * state.product.price
            for state in WarehouseState.objects.filter(quantity__gt=0)
            if not state.product.is_dummy
            and not state.product.is_unlimited
            and state.quantity > 0
        )

    @staticmethod
    def get_global_products_price_when_buy_sum():
        return sum(
            state.total_price
            for state in WarehouseState.objects.filter(quantity__gt=0)
            if not state.product.is_dummy and not state.product.is_unlimited
        )


class Tag(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Product(models.Model):
    id: int
    name = models.CharField(max_length=128, verbose_name="názov")
    barcode = models.CharField(max_length=32, unique=True, verbose_name="čiarový kód")
    image = models.FileField(null=True, verbose_name="obrázok")
    price = models.DecimalField(
        max_digits=6, decimal_places=2, verbose_name="predajná cena"
    )
    is_unlimited = models.BooleanField(verbose_name="neobmedzený predmet")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="tagy")
    is_dummy = models.BooleanField(default=False, verbose_name="jednorazový predmet")

    def __str__(self):
        return f"{self.name} ({self.price} €)"

    @staticmethod
    def generate_one_time_product(price, barcode):
        product, created = Product.objects.get_or_create(
            price=price,
            name="Jednorazová položka",
            is_unlimited=True,
            barcode=barcode,
            is_dummy=True,
        )
        return product


class WarehouseState(models.Model):
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, verbose_name="sklad"
    )
    warehouse_id: int
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name="produkt"
    )
    product_id: int
    quantity = models.IntegerField(verbose_name="počet")
    total_price = models.DecimalField(
        max_digits=16, decimal_places=2, default=0, verbose_name="skladová cena"
    )

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

    type = models.IntegerField(choices=EventType.choices, verbose_name="typ dokladu")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name="produkt"
    )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, verbose_name="sklad"
    )

    quantity = models.IntegerField(verbose_name="počet")
    price = models.DecimalField(
        max_digits=6, decimal_places=2, verbose_name="skladová cena / ks"
    )
    retail_price = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="odbytová cena / ks"
    )

    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="dátum a čas")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="používateľ",
    )

    def __str__(self):
        return f"{self.warehouse}; {self.product}; {self.timestamp}"

    def save(self, *args, **kwargs):
        ws = WarehouseState.objects.filter(
            product=self.product, warehouse=self.warehouse
        ).first()

        if not ws:
            ws = WarehouseState(
                quantity=0,
                total_price=0,
                warehouse=self.warehouse,
                product=self.product,
            )

        ws.quantity = ws.quantity + self.quantity
        ws.total_price = ws.total_price + self.price * self.quantity
        ws.save()

        super().save(*args, **kwargs)

    @property
    def abs_quantity(self):
        return abs(self.quantity)

    @property
    def abs_price(self):
        return abs(self.result_price)

    @property
    def result_price(self):
        return abs(self.abs_quantity * self.retail_price)


class Reset(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
    price_diff = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    # positive diff means profit

    def __str__(self) -> str:
        return f"Reset @ {self.created_at}"
