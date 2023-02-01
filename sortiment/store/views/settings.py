from collections import defaultdict

from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, TemplateView
from store.forms import (
    CorrectionForm,
    DiscardForm,
    InsertForm,
    ProductForm,
    TransferForm,
)
from store.helpers import get_warehouse
from store.helpers.events import new_correction, new_discard, new_import, new_transfer
from store.models import Product, Warehouse, WarehouseState
from store.views.mixins import StaffRequiredMixin


class ProductMixin:
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["product"] = self.product
        return ctx

    def dispatch(self, request, *args, **kwargs):
        product = request.GET.get("product")
        self.product = get_object_or_404(Product, id=product) if product else None
        return super().dispatch(request, *args, **kwargs)


class EventView(StaffRequiredMixin, TemplateView):
    template_name = "products/home.html"


class AddProductView(StaffRequiredMixin, CreateView):
    template_name = "products/create.html"
    form_class = ProductForm
    success_url = reverse_lazy("store:add_product")

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Produkt uložený.")
        return super().form_valid(form)


class EditProductView(StaffRequiredMixin, ProductMixin, FormView):
    template_name = "products/edit.html"
    form_class = ProductForm
    success_url = reverse_lazy("store:product_edit")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["instance"] = self.product
        return kw

    def form_valid(self, form):
        form.save()

        messages.success(self.request, "Produkt uložený.")
        return super().form_valid(form)


class CorrectionView(StaffRequiredMixin, ProductMixin, FormView):
    template_name = "products/correction.html"
    form_class = CorrectionForm
    success_url = reverse_lazy("store:correction")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        state = WarehouseState.objects.filter(
            warehouse=get_warehouse(self.request), product=self.product
        ).first()
        kw["initial"] = {"quantity": state.quantity if state else 0}
        return kw

    @transaction.atomic
    def form_valid(self, form):
        warehouse = get_warehouse(self.request)
        state = WarehouseState.objects.filter(
            warehouse=warehouse, product=self.product
        ).first()
        old_quantity = state.quantity if state else 0

        new_correction(
            self.request.user,
            self.product,
            warehouse,
            form.cleaned_data["quantity"] - old_quantity,
        )
        messages.success(self.request, "Korekcia skladu bola úspešná.")
        return super().form_valid(form)


class DiscardView(StaffRequiredMixin, ProductMixin, FormView):
    template_name = "products/discard.html"
    form_class = DiscardForm
    success_url = reverse_lazy("store:product_discard")

    def form_valid(self, form):
        new_discard(
            self.request.user,
            self.product,
            get_warehouse(self.request),
            form.cleaned_data["quantity"],
        )
        messages.success(self.request, "Vyradenie tovaru bolo úspešné.")
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["warehouse"] = get_warehouse(self.request)
        kwargs["product"] = self.product
        return kwargs


class ProductImportView(StaffRequiredMixin, ProductMixin, FormView):
    template_name = "products/import.html"
    form_class = InsertForm
    success_url = reverse_lazy("store:product_import")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.product:
            ctx["warehouse"] = get_warehouse(self.request)
            total = self.product.warehousestate_set.aggregate(
                quantity=Sum("quantity"), price=Sum("total_price")
            )
            if total["quantity"] is None:
                total = {"quantity": 0, "price": 0}
            ctx["total"] = total
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        if self.product:
            initial["sell_price"] = self.product.price
        return initial

    def form_valid(self, form):
        new_import(
            self.request.user,
            self.product,
            get_warehouse(self.request),
            form.cleaned_data["quantity"],
            form.cleaned_data["unit_price"],
        )
        self.product.price = form.cleaned_data["sell_price"]
        self.product.save()

        messages.success(self.request, "Príjem tovaru bol úspešný.")
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        product = request.GET.get("product")
        self.product = get_object_or_404(Product, id=product) if product else None
        return super().dispatch(request, *args, **kwargs)


class ProductTransferView(StaffRequiredMixin, FormView):
    template_name = "products/transfer.html"
    form_class = TransferForm
    success_url = reverse_lazy("store:product_transfer")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["product"] = self.product
        return ctx

    @transaction.atomic
    def form_valid(self, form):
        new_transfer(
            self.request.user,
            self.product,
            form.cleaned_data["from_warehouse"],
            form.cleaned_data["to_warehouse"],
            form.cleaned_data["quantity"],
        )
        messages.success(self.request, "Presun bol úspešný.")
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["product"] = self.product
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        product = request.GET.get("product")
        self.product = get_object_or_404(Product, id=product) if product else None
        return super().dispatch(request, *args, **kwargs)


class InventoryView(StaffRequiredMixin, TemplateView):
    template_name = "store/inventory.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        warehouses = Warehouse.objects.all()
        products = Product.objects.filter(is_dummy=False, is_unlimited=False).all()
        states = WarehouseState.objects.filter(product__in=products).all()
        state_map = defaultdict(lambda: 0)
        for s in states:
            state_map[(s.product_id, s.warehouse_id)] = s.quantity
        rows = []

        for p in products:
            stock = []
            for w in warehouses:
                stock.append(state_map[(p.id, w.id)])
            total = sum(stock)

            if total > 0:
                rows.append(
                    {
                        "name": p.name,
                        "barcode": p.barcode,
                        "price": p.price,
                        "stock": stock,
                        "total": total,
                    }
                )

        ctx["warehouses"] = warehouses
        ctx["wh_count"] = len(warehouses) + 1
        ctx["rows"] = rows
        return ctx


class SearchView(StaffRequiredMixin, TemplateView):
    template_name = "products/_search.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        query = self.request.GET.get("q")
        if query:
            ctx["products"] = Product.objects.filter(
                Q(barcode=query) | Q(name__icontains=query)
            )[0:10]
        ctx["query"] = query
        return ctx
