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
    credit = models.DecimalField(max_digits=6, decimal_places=2)
    barcode = models.CharField(max_length=32)
    REQUIRED_FIELDS = ["credit", "first_name", "last_name"]


class CreditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)

