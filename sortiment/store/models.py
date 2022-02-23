from django.conf import settings
from django.db import models


class Room(models.Model):
    name = models.CharField(max_length=16)


class Shop(models.Model):
    name = models.CharField(max_length=32)


class Product(models.Model):
    name = models.CharField(max_length=64)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField()
    ean = models.CharField(max_length=32)
    sum = models.DecimalField(max_digits=8, decimal_places=2)


class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    amount = models.IntegerField()


class Transaction(models.Model):
    class Types(models.TextChoices):
        SHOP_ROOM = 'SR', 'Shop > Room'
        ROOM_USER = 'RU', 'Room > User'
        ROOM_ROOM = 'RR', 'Room > Room'
        ROOM_NULL = 'RN', 'Room > Null'
        CREDIT = 'CC', 'Credit'

    type = models.CharField(max_length=2, choices=Types.choices)

    from_room = models.ForeignKey(Room, on_delete=models.CASCADE, blank=True, null=True, related_name='from_room')
    from_shop = models.ForeignKey(Shop, on_delete=models.CASCADE, blank=True, null=True, related_name='from_shop')

    to_room = models.ForeignKey(Room, on_delete=models.CASCADE, blank=True, null=True, related_name='to_room')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='to_user')

    price = models.DecimalField(max_digits=8, decimal_places=2)
    amount = models.IntegerField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
