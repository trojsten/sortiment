from django import forms
from django.core.exceptions import ValidationError
from django.forms import CharField, Form, IntegerField, ModelForm

from .models import Product, WarehouseState


class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ["name", "barcode", "image", "price", "is_unlimited", "tags"]


class DiscardForm(Form):
    barcode = CharField(label="barcode", max_length=32)
    product = forms.ModelChoiceField(queryset=Product.objects.all())
    qty = IntegerField(min_value=0)
    # TODO prepojenie barcode a product

    def __init__(self, warehouse, *args, **kwargs):
        self.wh = warehouse
        super().__init__(*args, **kwargs)

    def clean_qty(self):
        qty = self.cleaned_data["qty"]
        ws = WarehouseState.objects.filter(
            product=self.cleaned_data["product"], warehouse=self.wh
        )
        # TODO make prod+ws unique
        if ws[0].quantity < qty:
            raise ValidationError(
                "Not possible to discard more items that is in warehouse."
            )
        return qty
