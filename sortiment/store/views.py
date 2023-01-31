from collections import defaultdict

from django.db.models import Sum
from django.shortcuts import render

from users.models import SortimentUser
from .forms import DiscardForm, ProductForm
from .helpers import get_warehouse
from .models import Product, Warehouse, WarehouseState, WarehouseEvent, Tag


def product_list(request):

    warehouse_id = get_warehouse(request)

    tags = []
    for tag in Tag.objects.all():
        tags.append({
            "name": tag.name,
            "active": "tag-%s" % tag.name in request.GET
        })
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
        p.qty = state_d[p.id]
        p.totqty = all_state_d[p.id]

    context = {
        "prods": prods,
        'user': request.user,
        "tags": tags,
    }
    return render(request, "store/products.html", context)


def purchase_history(request):

    context = {
        "logged_in": request.user.is_authenticated
    }

    if request.user.is_authenticated:
        events = WarehouseEvent.objects.filter(user=request.user, type=WarehouseEvent.EventType.PURCHASE)
        events = events.order_by("-timestamp")
        history = []
        for event in events:
            history.append({
                "product": event.product,
                "quantity": event.quantity,
                "price": event.price,
                "date": event.timestamp.date(),
                "time": event.timestamp.time()
            })
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
            product.total_price = 0
            product.save()

    return render(request, "store/add_product.html", {"f": f})


def discard(request):

    f = DiscardForm()
    if request.method == "POST":
        f = DiscardForm(request.POST)
        if f.is_valid():
            f_product = f.save(commit=False)
            product = Product.objects.filter(barcode=f_product.barcode)
            product.total_price -= f_product.qty * product.price

    return render(request, "store/discard.html", {"f": f})


def stats(request):

    context = {
        "total_price_when_buy": Warehouse.get_global_products_price_when_buy_sum(),
        "total_price_for_sale": Warehouse.get_global_products_price_when_buy_sum(),
        "local_price_when_buy": get_warehouse(request).get_global_products_price_when_buy_sum(),
        "local_price_for_sale": get_warehouse(request).get_global_products_price_when_buy_sum(),
        "credit_sum": SortimentUser.get_credit_sum()
    }
    context["total_profit"] = context["total_price_for_sale"] - context["total_price_when_buy"]
    context["local_profit"] = context["local_price_for_sale"] - context["local_price_when_buy"]

    return render(request, "store/stats.html", context)
