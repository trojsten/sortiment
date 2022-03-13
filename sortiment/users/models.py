from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    credit = models.DecimalField(max_digits=8, decimal_places=2, default=0)
