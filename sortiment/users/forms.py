from django.forms import forms, DecimalField


class CreditMovementForm(forms.Form):
    credit = DecimalField(max_digits=6, decimal_places=2)
