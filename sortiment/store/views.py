from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .cart import Cart
from .models import Product, Tag, WarehouseEvent, WarehouseState


def product_list(request):
    warehouse_id = request.GET.get("warehouse_id", 1)

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
        p.qty = state_d[p.id]
        p.totqty = all_state_d[p.id]

    context = {
        "prods": prods,
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
                    "quantity": event.quantity,
                    "price": event.price,
                    "date": event.timestamp.date(),
                    "time": event.timestamp.time(),
                }
            )
        context["history"] = history

    return render(request, "store/purchase_history.html", context)


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
