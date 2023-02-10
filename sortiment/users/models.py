from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from sortiment import settings


class SortimentUserManager(BaseUserManager):
    def create_user(self, credit=0, barcode=None, password=""):
        user = self.model(credit=credit, barcode=barcode)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, credit=0, barcode=None, password=""):
        user = self.create_user(credit=credit, barcode=barcode)
        user.set_password(password)
        user.is_staff = True
        user.save(using=self._db)
        return user


class SortimentUser(AbstractUser):
    password = models.CharField(verbose_name="heslo", max_length=128, blank=True)
    first_name = models.CharField(verbose_name="meno", max_length=150)
    last_name = models.CharField(verbose_name="priezvisko", max_length=150)
    credit = models.DecimalField(
        verbose_name="kredit", max_digits=6, decimal_places=2, default=0
    )
    barcode = models.CharField(verbose_name="čiarový kód", max_length=32, blank=True)
    is_guest = models.BooleanField(default=False)
    REQUIRED_FIELDS = ["credit", "first_name", "last_name"]

    def can_pay(self, money):
        if self.is_guest:
            return True
        print(-money, self.credit, -money <= self.credit)
        return -money <= self.credit

    def make_credit_operation(self, money, is_purchase):
        if self.is_guest:
            return
        CreditLog(user=self, price=money, is_purchase=is_purchase).save()
        self.credit += money
        self.save()

    @staticmethod
    def get_credit_sum():
        return sum(user.credit for user in SortimentUser.objects.all())


class CreditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    is_purchase = models.BooleanField()

    def __str__(self):
        return (
            f"{self.user} {self.price} {self.timestamp} "
            f"{'purchase' if self.is_purchase else 'credit'}"
        )
