from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from users.models import SortimentUser

from .cart import Cart
from .forms import DiscardForm, ProductForm, TransferForm
from .forms import InsertForm
from .helpers import get_warehouse
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

    prods = Product.objects.all()
    for tag in active_tags:
        prods = prods.filter(tags__name__contains=tag)
    for p in prods:
        p.qty = state_d[p.id] if not p.is_unlimited else "&#8734;"
        p.totqty = all_state_d[p.id] if not p.is_unlimited else "&#8734;"

    non_zero_prods = filter(lambda p: p.is_unlimited or p.totqty > 0, prods)

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


def product_event(request):
    return render(request, "store/event.html", {})


def add_product(request):
    f = ProductForm()
    if request.method == "POST":
        f = ProductForm(request.POST)
        if f.is_valid():
            product = f.save(commit=False)
            product.price = f.cleaned_data["price"]
            product.save()

    return render(request, "store/add_product.html", {"f": f})


def discard(request):
    wh = get_warehouse(request)

    f = DiscardForm(wh)
    if request.method == "POST":
        f = DiscardForm(wh, request.POST)
        if f.is_valid():

            WarehouseEvent(
                product=f.cleaned_data["product"],
                warehouse=wh,
                quantity=-f.cleaned_data["qty"],
                price=0,
                type=WarehouseEvent.EventType.DISCARD,
                user=request.user,
            ).save()

    return render(request, "store/discard.html", {"f": f})


def insert(request):

    # TODO prepojenie barcode a product, prepojenie total a unit price

    wh = get_warehouse(request)

    f = InsertForm()
    if request.method == "POST":
        f = InsertForm(request.POST)
        if f.is_valid():

            WarehouseEvent(
                product=f.cleaned_data["product"],
                warehouse=wh,
                quantity=f.cleaned_data["qty"],
                price=f.cleaned_data["unit_price"],
                type=WarehouseEvent.EventType.IMPORT,
                user=request.user,
            ).save()

    return render(request, "store/insert.html", {"f": f})


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
    cart.add_product(product, 1)
    return render(request, "store/_cart.html", {"cart": cart})


@require_POST
@login_required
def cart_add_barcode(request):
    cart = Cart(request)
    product = Product.objects.get(barcode=request.POST["barcode"])
    if product is None:
        pass
    cart.add_product(product, 1)
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
