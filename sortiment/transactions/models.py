from django.conf import settings
from django.db import models


class Transaction(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        abstract = True


class CreditTransaction(Transaction):
    """
    Represents credit adjustment transaction.
    """
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    room = models.ForeignKey("store.Room", on_delete=models.RESTRICT, related_name="+")


class ItemRestockTransaction(Transaction):
    """
    Represents restock action.
    """
    shop = models.ForeignKey("store.Shop", on_delete=models.RESTRICT, related_name="+")
    room = models.ForeignKey("store.Room", on_delete=models.RESTRICT, related_name="+")

    price = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    amount = models.IntegerField(null=True)
    product = models.ForeignKey("store.Product", on_delete=models.CASCADE)


class ItemTransferTransaction(Transaction):
    """
    Represents item transfer between two rooms (or trash).
    """
    from_room = models.ForeignKey("store.Room", on_delete=models.RESTRICT, related_name="+")
    to_room = models.ForeignKey("store.Room", on_delete=models.RESTRICT, blank=True, null=True, related_name="+")

    amount = models.IntegerField(null=True)
    product = models.ForeignKey("store.Product", on_delete=models.CASCADE)


class ItemPurchaseTransaction(Transaction):
    """
    Represents item purchase by end user.
    `price` contains price per item at the time of purchase.
    """
    room = models.ForeignKey("store.Room", on_delete=models.RESTRICT, related_name="+")

    price = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    amount = models.IntegerField(null=True)
    product = models.ForeignKey("store.Product", on_delete=models.CASCADE)

