from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from sortiment import settings


class SortimentUserManager(BaseUserManager):
    def create_user(self, credit=0, barcode=None, password=""):
        user = self.model(
            credit=credit,
            barcode=barcode
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, credit=0, barcode=None, password=""):
        user = self.create_user(
            credit=credit,
            barcode=barcode
        )
        user.set_password(password)
        user.is_staff = True
        user.save(using=self._db)
        return user


class SortimentUser(AbstractUser):
    password = models.CharField("password", max_length=128, blank=True)
    first_name = models.CharField("first name", max_length=150)
    last_name = models.CharField("last name", max_length=150)
    credit = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    barcode = models.CharField(max_length=32, blank=True)
    REQUIRED_FIELDS = ["credit", "first_name", "last_name"]

    def can_pay(self, money):
        return -money <= self.credit

    def make_credit_operation(self, money):
        CreditLog(user=self, price=money).save()
        self.credit += money
        self.save()


class CreditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.user} {self.price} {self.timestamp}"

