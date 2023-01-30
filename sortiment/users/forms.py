from django.forms import forms, DecimalField, ModelChoiceField

from users.models import SortimentUser


class CreditAddAndWithdrawalForm(forms.Form):
    credit = DecimalField(max_digits=6, decimal_places=2)

class CreditMovementForm(forms.Form):
    credit = DecimalField(max_digits=6, decimal_places=2, max_value=0)
    user = ModelChoiceField(queryset=SortimentUser.objects.all().order_by('username'))