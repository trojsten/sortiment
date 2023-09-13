from django.core.exceptions import ValidationError
from django.forms import CharField, DecimalField, ModelChoiceField, forms
from users.models import SortimentUser


class CreditChangeForm(forms.Form):
    credit = DecimalField(max_digits=6, decimal_places=2, label="Dobiť kredit")

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        if self.user.is_guest:
            self.add_error("credit", "Guest nemôže pracovať s kreditom.")

        return self.cleaned_data

    def clean_credit(self):
        credit = self.cleaned_data["credit"]
        if not self.user.can_pay(-credit):
            raise ValidationError("Nemáš dostatok kreditu.")
        return credit


class CreditMovementForm(forms.Form):
    credit = DecimalField(max_digits=6, decimal_places=2, min_value=0, label="Kredit")
    user = ModelChoiceField(
        queryset=SortimentUser.objects.all()
        .order_by("username")
        .filter(is_guest=False),
        label="Používateľ",
    )
    message = CharField(max_length=128, label="Správa")

    def remove_user_from_choices(self, user):
        self.fields["user"].queryset = self.fields["user"].queryset.exclude(id=user.id)

    def clean(self):
        data = self.cleaned_data
        if self.user.is_guest:
            self.add_error("credit", "Guest nemôže pracovať s kreditom.")
        if self.user == data["user"]:
            self.add_error("user", "Nemôžeš poslať peniaze samému sebe.")
        return data

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_credit(self):
        credit = self.cleaned_data["credit"]
        if not self.user.can_pay(-credit):
            raise ValidationError("Nemáš dostatok kreditu.")
        return credit
