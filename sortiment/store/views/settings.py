from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, TemplateView
from store.forms import DiscardForm, InsertForm, ProductForm, TransferForm
from store.helpers import get_warehouse
from store.models import Product, Warehouse, WarehouseEvent, WarehouseState
from store.views.mixins import StaffRequiredMixin


class EventView(StaffRequiredMixin, TemplateView):
    template_name = "products/home.html"


class AddProductView(StaffRequiredMixin, CreateView):
    template_name = "store/add_product.html"
    form_class = ProductForm
    success_url = reverse_lazy("store:add_product")

    def form_valid(self, form):
        product = form.save(commit=False)
        product.price = form.cleaned_data["price"]
        product.save()

        return super().form_valid(form)


class DiscardView(StaffRequiredMixin, FormView):
    template_name = "products/discard.html"
    form_class = DiscardForm
    success_url = reverse_lazy("store:discard")

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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["warehouse"] = get_warehouse(self.request)
        kwargs["product"] = self.product
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["product"] = self.product
        return ctx

    def dispatch(self, request, *args, **kwargs):
        product = request.GET.get("product")
        self.product = get_object_or_404(Product, id=product) if product else None
        return super().dispatch(request, *args, **kwargs)


class ProductImportView(StaffRequiredMixin, FormView):
    template_name = "products/import.html"
    form_class = InsertForm
    success_url = reverse_lazy("store:product_import")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["product"] = self.product
        if self.product:
            ctx["warehouse"] = get_warehouse(self.request)
            ctx["total"] = self.product.warehousestate_set.aggregate(
                quantity=Sum("quantity"), price=Sum("total_price")
            )
        return ctx

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


@login_required
@transaction.atomic
def product_transfer(request):
    form = TransferForm(None)
    product = request.GET.get("product")
    if product:
        product = get_object_or_404(Product, id=product)

        if request.method == "POST":
            form = TransferForm(product, request.POST)
            if form.is_valid():
                WarehouseEvent(
                    product=product,
                    warehouse=form.cleaned_data["from_warehouse"],
                    quantity=-form.cleaned_data["quantity"],
                    price=0,
                    type=WarehouseEvent.EventType.TRANSFER_OUT,
                    user=request.user,
                ).save()

                WarehouseEvent(
                    product=product,
                    warehouse=form.cleaned_data["to_warehouse"],
                    quantity=form.cleaned_data["quantity"],
                    price=0,
                    type=WarehouseEvent.EventType.TRANSFER_IN,
                    user=request.user,
                ).save()

                return redirect("store:product_transfer")

    return render(request, "products/transfer.html", {"form": form, "product": product})


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
