import re

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import DecimalField, Form, IntegerField, ModelForm, NumberInput

from .models import Product, ProductEAN, Warehouse, WarehouseState

EAN_SPLIT_RE = re.compile(r"[\s,]+")


class ProductForm(ModelForm):
    eans = forms.CharField(
        label="EAN kódy",
        help_text="Zadaj jeden alebo viac EAN kódov, každý na samostatný riadok.",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Jeden EAN na riadok"}),
    )

    class Meta:
        model = Product
        fields = ["name", "image", "is_unlimited", "tags", "price"]
        widgets = {
            "price": NumberInput(attrs={"min": 0, "step": 0.01}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["eans"].initial = "\n".join(self.instance.ean_codes)

    def clean_eans(self):
        raw = self.cleaned_data["eans"]
        codes = [code for code in EAN_SPLIT_RE.split(raw) if code]
        if not codes:
            raise ValidationError("Zadaj aspoň jeden EAN kód.")

        seen = set()
        for code in codes:
            if len(code) > 32:
                raise ValidationError(
                    f"EAN kód {code} je príliš dlhý (max. 32 znakov)."
                )
            if code in seen:
                raise ValidationError(f"EAN kód {code} je zadaný viackrát.")
            seen.add(code)

        existing = ProductEAN.objects.filter(code__in=codes)
        if self.instance.pk:
            existing = existing.exclude(product=self.instance)
        if existing.exists():
            code = existing.first().code
            raise ValidationError(f"EAN kód {code} už patrí inému produktu.")

        return codes

    @transaction.atomic
    def save(self, commit=True):
        product = super().save(commit=commit)
        if commit:
            codes = self.cleaned_data["eans"]
            product.eans.exclude(code__in=codes).delete()
            existing = set(product.eans.values_list("code", flat=True))
            ProductEAN.objects.bulk_create(
                [
                    ProductEAN(product=product, code=code)
                    for code in codes
                    if code not in existing
                ]
            )
        return product


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
    unit_price = DecimalField(
        label="Jednotková nákupná cena", min_value=0, step_size=0.01
    )
    sell_price = DecimalField(label="Predajná cena", min_value=0, step_size=0.01)


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
