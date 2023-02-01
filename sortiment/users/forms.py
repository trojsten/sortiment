from django.core.exceptions import ValidationError
from django.forms import DecimalField, ModelChoiceField, forms
from users.models import SortimentUser


class CreditAddAndWithdrawalForm(forms.Form):
    credit = DecimalField(max_digits=6, decimal_places=2, label="Kredit")


class CreditMovementForm(forms.Form):
    credit = DecimalField(max_digits=6, decimal_places=2, min_value=0, label="Kredit")
    user = ModelChoiceField(
        queryset=SortimentUser.objects.all()
        .order_by("username")
        .filter(is_guest=False),
        label="Používateľ",
    )

    def remove_user_from_choices(self, user):
        self.fields["user"].queryset = self.fields["user"].queryset.exclude(id=user.id)

    def clean(self):
        data = self.cleaned_data
        if data["user"] == data["user2"]:
            raise ValidationError("Nemôžeš poslať peniaze samému sebe.")
