from django import forms
from django.forms import CharField, Form, IntegerField, ModelForm

from .models import Product


class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ["name", "barcode", "image", "price", "is_unlimited", "tags"]


class DiscardForm(Form):
    barcode = CharField(label="barcode", max_length=32)
    product = forms.ModelChoiceField(queryset=Product.objects.all())
    qty = IntegerField(min_value=0)
