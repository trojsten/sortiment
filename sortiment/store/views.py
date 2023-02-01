from collections import defaultdict
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from users.models import CreditLog, SortimentUser

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
    prods = Product.objects.filter(is_dummy=False)
    for tag in active_tags:
        prods = prods.filter(tags__name__contains=tag)
    for p in prods:
        p.qty = state_d[p.id] if not p.is_unlimited else infty_string
        p.totqty = all_state_d[p.id] if not p.is_unlimited else infty_string

    non_zero_prods = filter(lambda p: p.is_unlimited or p.totqty > 0, prods)
    non_zero_prods = sorted(non_zero_prods, key=lambda x: x.name)
    non_zero_prods = sorted(
        non_zero_prods, key=lambda x: not (isinstance(x.qty, int) and x.qty > 0)
    )

    context = {
        "prods": non_zero_prods,
        "user": request.user,
        "tags": tags,
        "cart": Cart(request),
    }
    return render(request, "store/products.html", context)


def purchase_history(request):
    end = timezone.now() - timedelta(days=60)
    wh_events = (
        WarehouseEvent.objects.filter(
            user=request.user, type=WarehouseEvent.EventType.PURCHASE
        )
        .order_by("-timestamp")
        .filter(timestamp__gte=end)
    )
    credit_events = CreditLog.objects.filter(
        user=request.user, timestamp__gte=end
    ).order_by("-timestamp")

    events = []
    for e in wh_events:
        events.append({"event": e, "timestamp": e.timestamp, "type": "product"})
    for e in credit_events:
        events.append({"event": e, "timestamp": e.timestamp, "type": "credit"})

    events.sort(key=lambda x: x["timestamp"], reverse=True)
    return render(
        request,
        "store/purchase_history.html",
        {"events": events, "cart": Cart(request)},
    )


def product_management(request):
    return render(request, "products/home.html")


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
    form = DiscardForm(wh, None)

    product = request.GET.get("product")
    if product:
        product = get_object_or_404(Product, id=product)

        if request.method == "POST":
            form = DiscardForm(wh, product, request.POST)
            if form.is_valid():
                WarehouseEvent(
                    product=product,
                    warehouse=wh,
                    quantity=-form.cleaned_data["quantity"],
                    price=0,
                    type=WarehouseEvent.EventType.DISCARD,
                    user=request.user,
                ).save()

                return redirect("store:product_discard")

    return render(request, "products/discard.html", {"form": form, "product": product})


def product_import(request):
    product = request.GET.get("product")
    if product:
        product = get_object_or_404(Product, id=product)
        wh = get_warehouse(request)
        total = product.warehousestate_set.aggregate(
            quantity=Sum("quantity"), price=Sum("total_price")
        )
        if not total["quantity"]:
            total = {"quantity": 0, "price": 0}

        if request.method == "POST":
            form = InsertForm(request.POST)
            if form.is_valid():
                WarehouseEvent(
                    product=product,
                    warehouse=wh,
                    quantity=form.cleaned_data["quantity"],
                    price=form.cleaned_data["unit_price"],
                    type=WarehouseEvent.EventType.IMPORT,
                    user=request.user,
                ).save()

                product.price = form.cleaned_data["sell_price"]
                product.save()

        form = InsertForm(initial={"sell_price": product.price})
    else:
        form = None
        product = None
        wh = None
        total = {}
    return render(
        request,
        "products/import.html",
        {"form": form, "product": product, "warehouse": wh, "total": total},
    )


def stats(request):

    warehouse = get_warehouse(request)

    context = {
        "total_price_when_buy": Warehouse.get_global_products_price_when_buy_sum(),
        "total_price_for_sale": Warehouse.get_global_products_price_for_sale_sum(),
        "local_price_when_buy": warehouse.get_products_price_when_buy_sum(),
        "local_price_for_sale": warehouse.get_products_price_for_sale_sum(),
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


def inventory(request):
    warehouses = Warehouse.objects.all()
    products = []

    for p in Product.objects.all():
        stock = []
        for w in warehouses:
            stock_count = WarehouseState.objects.filter(warehouse=w, product=p).first()
            stock.append(stock_count.quantity if stock_count else 0)
        total = sum(stock)
        if p.is_dummy:
            continue
        if total > 0 and not p.is_unlimited:
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
        request, "products/_search.html", {"products": products, "query": query}
    )
