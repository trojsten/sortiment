from django import forms
from django.core.exceptions import ValidationError
from django.forms import CharField, DecimalField, Form, IntegerField, ModelForm

from .models import Product, Warehouse, WarehouseState


class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ["name", "barcode", "image", "is_unlimited", "tags"]

    price = forms.DecimalField(min_value=0)


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
        if ws[0].quantity < qty:
            raise ValidationError(
                "Not possible to discard more items that is in warehouse."
            )
        return qty


class InsertForm(Form):
    quantity = IntegerField(label="Počet kusov", min_value=0)
    unit_price = DecimalField(label="Jednotková cena", min_value=0)
    sell_price = DecimalField(label="Predajná cena", min_value=0)


class TransferForm(Form):
    from_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.all(), label="Zdrojový sklad"
    )
    to_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.all(), label="Cieľový sklad"
    )
    quantity = IntegerField(min_value=0, label="Počet kusov")

    def clean_to_warehouse(self):
        from_warehouse = self.cleaned_data["from_warehouse"]
        to_warehouse = self.cleaned_data["to_warehouse"]
        if from_warehouse == to_warehouse:
            raise ValidationError("Nemôžeš presunúť produkty v rámci jedného skladu.")
        return from_warehouse

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        ws = WarehouseState.objects.filter(
            product=self.cleaned_data["product"],
            warehouse=self.cleaned_data["from_warehouse"],
        ).first()
        if not ws or ws.quantity < quantity:
            raise ValidationError("V zdrojovom sklade nie je dostatočny počet kusov.")
        return quantity
