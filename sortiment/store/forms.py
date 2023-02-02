from django import forms
from django.core.exceptions import ValidationError
from django.forms import DecimalField, Form, IntegerField, ModelForm, NumberInput

from .models import Product, Warehouse, WarehouseState


class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ["name", "barcode", "image", "is_unlimited", "tags", "price"]
        labels = {
            "name": "Názov",
            "barcode": "Čiarový kód",
            "image": "Obrázok",
            "is_unlimited": "Neobmedzený predmet",
            "tags": "Tagy",
            "price": "Predajná cena",
        }
        widgets = {
            "price": NumberInput(attrs={"min": 0, "step": 0.05}),
        }


class DiscardForm(Form):
    quantity = IntegerField(min_value=0, label="Počet kusov")

    def __init__(self, warehouse, product, *args, **kwargs):
        self.warehouse = warehouse
        self.product = product
        super().__init__(*args, **kwargs)

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        ws = WarehouseState.objects.filter(
            product=self.product, warehouse=self.warehouse
        ).first()
        if not ws or ws.quantity < quantity:
            raise ValidationError("Na sklade nie je dostatočný počet kusov.")
        return quantity


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

    def __init__(self, product, *args, **kwargs):
        self.product = product
        super().__init__(*args, **kwargs)

    def clean_to_warehouse(self):
        from_warehouse = self.cleaned_data["from_warehouse"]
        to_warehouse = self.cleaned_data["to_warehouse"]
        if from_warehouse == to_warehouse:
            raise ValidationError("Nemôžeš presunúť produkty v rámci jedného skladu.")
        return to_warehouse

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        ws = WarehouseState.objects.filter(
            product=self.product,
            warehouse=self.cleaned_data["from_warehouse"],
        ).first()
        if not ws or ws.quantity < quantity:
            raise ValidationError("V zdrojovom sklade nie je dostatočny počet kusov.")
        return quantity


class CorrectionForm(Form):
    quantity = IntegerField(label="Počet kusov")
