from collections import defaultdict

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from .models import Product, Warehouse, WarehouseState, WarehouseEvent, Tag


def product_list(request):
    warehouse_id = request.GET.get("warehouse_id", 1)

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

    all_states = (WarehouseState.objects.values("product").annotate(totqty=Sum("quantity")).order_by())

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
