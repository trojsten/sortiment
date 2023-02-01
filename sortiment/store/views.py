from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, FormView, TemplateView
from users.models import SortimentUser

from .cart import Cart
from .forms import DiscardForm, InsertForm, ProductForm, TransferForm
from .helpers import get_dummy_barcode_data, get_warehouse
from .models import Product, Tag, Warehouse, WarehouseEvent, WarehouseState


def product_list(request):
    warehouse_id = get_warehouse(request)

    tags = []
    for tag in Tag.objects.all():
        tags.append({"name": tag.name, "active": "tag-%s" % tag.name in request.GET})
    active_tags = [tag["name"] for tag in tags if tag["active"]]

    w_states = WarehouseState.objects.filter(warehouse__exact=warehouse_id)
    state_d = defaultdict(lambda: 0)
    for st in w_states:
        state_d[st.product_id] = st.quantity

    all_states = (
        WarehouseState.objects.values("product")
        .annotate(totqty=Sum("quantity"))
        .order_by()
    )

    all_state_d = defaultdict(lambda: 0)
    for st in all_states:
        all_state_d[st["product"]] = st["totqty"]

    # only show products that have all active tags

    infty_string = "&#8734;"
    prods = Product.objects.all()
    for tag in active_tags:
        prods = prods.filter(tags__name__contains=tag)
    for p in prods:
        p.qty = state_d[p.id] if not p.is_unlimited else infty_string
        p.totqty = all_state_d[p.id] if not p.is_unlimited else infty_string

    non_zero_prods = filter(lambda p: p.is_unlimited or p.totqty > 0, prods)
    non_zero_prods = sorted(non_zero_prods, key=lambda x: x.name)
    non_zero_prods = sorted(
        non_zero_prods, key=lambda x: not (isinstance(x.qty, int) and x.qty != 0)
    )

    context = {
        "prods": non_zero_prods,
        "user": request.user,
        "tags": tags,
        "cart": Cart(request),
    }
    return render(request, "store/products.html", context)


def purchase_history(request):
    context = {"logged_in": request.user.is_authenticated}

    if request.user.is_authenticated:
        events = WarehouseEvent.objects.filter(
            user=request.user, type=WarehouseEvent.EventType.PURCHASE
        )
        events = events.order_by("-timestamp")
        history = []
        for event in events:
            history.append(
                {
                    "product": event.product,
                    "quantity": abs(event.quantity),
                    "price": event.price,
                    "date": event.timestamp.date(),
                    "time": event.timestamp.time(),
                }
            )
        context["history"] = history

    return render(request, "store/purchase_history.html", context)


class EventView(TemplateView):
    template_name = "store/event.html"


class AddProductView(CreateView):
    template_name = "store/add_product.html"
    form_class = ProductForm
    success_url = reverse_lazy("store:add_product")

    def form_valid(self, form):
        product = form.save(commit=False)
        product.price = form.cleaned_data["price"]
        product.save()

        return super().form_valid(form)


class DiscardView(FormView):

    template_name = "store/discard.html"
    form_class = DiscardForm
    success_url = reverse_lazy("store:discard")

    def form_valid(self, form):
        wh = get_warehouse(self.request)
        WarehouseEvent(
            product=form.cleaned_data["product"],
            warehouse=wh,
            quantity=-form.cleaned_data["qty"],
            price=0,
            type=WarehouseEvent.EventType.DISCARD,
            user=self.user,
        ).save()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["warehouse"] = get_warehouse(self.request)
        return kwargs


class ProductImportView(FormView):

    template_name = "products/import.html"
    form_class = InsertForm
    success_url = reverse_lazy("store:product_import")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.product_id:
            product = get_object_or_404(Product, id=self.product_id)
            context["product"] = product
            context["warehouse"] = get_warehouse(self.request)
            context["total"] = product.warehousestate_set.aggregate(
                quantity=Sum("quantity"), price=Sum("total_price")
            )
        else:
            context["form"] = None
        return context

    def form_valid(self, form):
        product = get_object_or_404(Product, id=self.product_id)
        WarehouseEvent(
            product=product,
            warehouse=get_warehouse(self.request),
            quantity=form.cleaned_data["quantity"],
            price=form.cleaned_data["unit_price"],
            type=WarehouseEvent.EventType.IMPORT,
            user=self.request.user,
        ).save()

        product.warehousestate_set.aggregate(
            quantity=Sum("quantity"), price=Sum("total_price")
        )
        product.price = form.cleaned_data["sell_price"]
        product.save()

        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        self.product_id = request.GET.get("product")
        return super().dispatch(request, *args, **kwargs)


def stats(request):

    context = {
        "total_price_when_buy": Warehouse.get_global_products_price_when_buy_sum(),
        "total_price_for_sale": Warehouse.get_global_products_price_when_buy_sum(),
        "local_price_when_buy": get_warehouse(
            request
        ).get_global_products_price_when_buy_sum(),
        "local_price_for_sale": get_warehouse(
            request
        ).get_global_products_price_when_buy_sum(),
        "credit_sum": SortimentUser.get_credit_sum(),
    }
    context["total_profit"] = (
        context["total_price_for_sale"] - context["total_price_when_buy"]
    )
    context["local_profit"] = (
        context["local_price_for_sale"] - context["local_price_when_buy"]
    )

    return render(request, "store/stats.html", context)


@require_POST
@login_required
def cart_remove(request, product):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product)
    cart.remove_product(product, 1)
    return render(request, "store/_cart.html", {"cart": cart})


@require_POST
@login_required
def cart_add(request, product):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product)
    cart.add_product(product, 1, False)
    return render(request, "store/_cart.html", {"cart": cart})


@require_POST
@login_required
def cart_add_barcode(request):
    cart = Cart(request)
    barcode = request.POST["barcode"].strip()
    product = Product.objects.filter(barcode=barcode).first()
    if product is None:
        price = get_dummy_barcode_data(barcode)
        if price is not None:
            product = Product.generate_one_time_product(price, barcode)
            cart.add_product(product, 1, True)
    else:
        cart.add_product(product, 1, False)
    return render(request, "store/_cart.html", {"cart": cart})


@login_required
@transaction.atomic
def checkout(request):
    ok = Cart(request).checkout(request)
    if ok:
        return HttpResponseRedirect(reverse("logout"))
    else:
        raise SuspiciousOperation("Not enough credit")


@login_required
@transaction.atomic
def transfer(request):
    form = TransferForm()
    if request.method == "POST":
        form = TransferForm(request.POST)
        if form.is_valid():
            WarehouseEvent(
                product=form.cleaned_data["product"],
                warehouse=form.cleaned_data["from_warehouse"],
                quantity=-form.cleaned_data["qty"],
                price=0,
                type=WarehouseEvent.EventType.TRANSFER_OUT,
                user=request.user,
            ).save()

            WarehouseEvent(
                product=form.cleaned_data["product"],
                warehouse=form.cleaned_data["to_warehouse"],
                quantity=-form.cleaned_data["qty"],
                price=0,
                type=WarehouseEvent.EventType.TRANSFER_IN,
                user=request.user,
            ).save()

    return render(request, "store/transfer.html", {"form": form})


def inventory(request):
    warehouses = Warehouse.objects.all()
    products = []

    for p in Product.objects.all():
        stock = []
        for w in warehouses:
            stockCount = WarehouseState.objects.filter(warehouse=w, product=p).first()
            if stockCount:
                stock.append(stockCount.quantity)
            else:
                stock.append(0)
        total = sum(stock)
        if total > 0:
            products.append(
                {
                    "name": p.name,
                    "barcode": p.barcode,
                    "price": p.price,
                    "stock": stock,
                    "total": total,
                }
            )

    context = {
        "warehouses": warehouses,
        "wh_count": len(warehouses) + 1,
        "products": products,
    }

    return render(request, "store/inventory.html", context)


def search(request):
    query = request.GET.get("q", "")
    products = []
    if query:
        products = Product.objects.filter(Q(barcode=query) | Q(name__icontains=query))[
            0:10
        ]
    return render(
        request, "products/search.html", {"products": products, "query": query}
    )
