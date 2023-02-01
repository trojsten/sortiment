from collections import defaultdict

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
from store.models import Product, Warehouse, WarehouseEvent, WarehouseState
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
        product = form.save(commit=False)
        product.price = form.cleaned_data["price"]
        product.save()

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
        new_quantity = form.cleaned_data["quantity"]

        state = WarehouseState.objects.filter(
            warehouse=warehouse, product=self.product
        ).first()
        old_quantity = state.quantity if state else 0
        if old_quantity != 0:
            price = state.total_price / old_quantity
        else:
            price = 0

        WarehouseEvent(
            warehouse=warehouse,
            product=self.product,
            quantity=new_quantity - old_quantity,
            type=WarehouseEvent.EventType.CORRECTION,
            price=price,
            user=self.request.user,
        ).save()

        return super().form_valid(form)


class DiscardView(StaffRequiredMixin, ProductMixin, FormView):
    template_name = "products/discard.html"
    form_class = DiscardForm
    success_url = reverse_lazy("store:product_discard")

    def form_valid(self, form):
        wh = get_warehouse(self.request)
        WarehouseEvent(
            product=self.product,
            warehouse=wh,
            quantity=-form.cleaned_data["quantity"],
            price=0,
            type=WarehouseEvent.EventType.DISCARD,
            user=self.request.user,
        ).save()
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
        WarehouseEvent(
            product=self.product,
            warehouse=get_warehouse(self.request),
            quantity=form.cleaned_data["quantity"],
            price=form.cleaned_data["unit_price"],
            type=WarehouseEvent.EventType.IMPORT,
            user=self.request.user,
        ).save()

        self.product.price = form.cleaned_data["sell_price"]
        self.product.save()

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
        from_warehouse = form.cleaned_data["from_warehouse"]
        warehouse_state = WarehouseState.objects.get(
            warehouse=from_warehouse, product=self.product
        )
        price = warehouse_state.total_price / warehouse_state.quantity
        WarehouseEvent(
            product=self.product,
            warehouse=from_warehouse,
            quantity=-form.cleaned_data["quantity"],
            price=price,
            type=WarehouseEvent.EventType.TRANSFER_OUT,
            user=self.request.user,
        ).save()

        to_warehouse = form.cleaned_data["to_warehouse"]
        WarehouseEvent(
            product=self.product,
            warehouse=to_warehouse,
            quantity=form.cleaned_data["quantity"],
            price=price,
            type=WarehouseEvent.EventType.TRANSFER_IN,
            user=self.request.user,
        ).save()
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
