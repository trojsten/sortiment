from django.forms import CharField, ChoiceField, Form, IntegerField, ModelForm

from .models import Product


class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ["name", "barcode", "image", "price", "is_unlimited", "tags"]


class DiscardForm(Form):

    CHOICES = []
    for pr in Product.objects.all():
        CHOICES.append((pr.name, pr.name))

    barcode = CharField(label="barcode", max_length=32)
    product = ChoiceField(choices=CHOICES)
    qty = IntegerField(min_value=0)
