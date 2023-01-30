from collections import defaultdict

from django.db.models import Sum
from django.shortcuts import render

from .forms import ProductForm
from .models import Product, WarehouseState


def product_list(request):

    warehouse_id = request.GET.get("warehouse_id", 1)

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

    prods = Product.objects.all()
    for p in prods:
        p.qty = state_d[p.id]
        p.totqty = all_state_d[p.id]

    context = {"prods": prods}
    return render(request, "store/products.html", context)


def product_event(request):
    return render(request, "store/event.html", {})


def insert(request):

    f = ProductForm()
    if request.method == "POST":
        f = ProductForm(request.POST)
        if f.is_valid():
            product = f.save(commit=False)
            product.total_price = 0
            product.save()

    return render(request, "store/insert.html", {"f": f})
