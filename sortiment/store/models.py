from django.conf import settings
from django.db import models


class Room(models.Model):
    name = models.CharField(max_length=16)


class Shop(models.Model):
    name = models.CharField(max_length=32)


class Product(models.Model):
    name = models.CharField(max_length=64)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(blank=True)
    ean = models.CharField(max_length=32, blank=True)
    sum = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name


class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    amount = models.IntegerField()
