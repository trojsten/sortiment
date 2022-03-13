from django import forms
from django.core.exceptions import ValidationError

from sortiment.users.models import User


class CreditAdjustmentForm(forms.Form):
    amount = forms.DecimalField(decimal_places=2)

    def __init__(self, user: User, **kwargs):
        super().__init__(**kwargs)
        self.user = user

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if self.user.credit + amount < 0:
            raise ValidationError("Po úprave by si mal(a) záporný kredit.")

        return amount


