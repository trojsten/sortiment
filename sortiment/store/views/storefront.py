from collections import defaultdict
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import SuspiciousOperation
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from store.cart import Cart
from store.helpers import get_dummy_barcode_data, get_warehouse
from store.models import Product, Tag, Warehouse, WarehouseEvent, WarehouseState
from users.models import CreditLog, SortimentUser


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
    products = Product.objects.filter(is_dummy=False)
    for tag in active_tags:
        products = products.filter(tags__name__contains=tag)
    for p in products:
        p.qty = state_d[p.id] if not p.is_unlimited else infty_string
        p.totqty = all_state_d[p.id] if not p.is_unlimited else infty_string

    non_zero_prods = filter(lambda p: p.is_unlimited or p.totqty > 0, products)
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
        user=request.user, timestamp__gte=end, is_purchase=False
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


class StatsView(TemplateView):
    template_name = "store/stats.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        warehouse = get_warehouse(self.request)

        ctx["total_price_when_buy"] = Warehouse.get_global_products_price_when_buy_sum()
        ctx["total_price_for_sale"] = Warehouse.get_global_products_price_for_sale_sum()
        ctx["local_price_when_buy"] = warehouse.get_products_price_when_buy_sum()
        ctx["local_price_for_sale"] = warehouse.get_products_price_for_sale_sum()
        ctx["credit_sum"] = SortimentUser.get_credit_sum()
        ctx["total_profit"] = (ctx["total_price_for_sale"] - ctx["total_price_when_buy"])
        ctx["local_profit"] = (ctx["local_price_for_sale"] - ctx["local_price_when_buy"])
        return ctx


class CartRemoveView(LoginRequiredMixin, View):
    def get(self, request, product):
        raise SuspiciousOperation("Only POST method allowed")

    def post(self, request, product):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product)
        cart.remove_product(product, 1)
        return render(request, "store/_cart.html", {"cart": cart})


class CartAddView(LoginRequiredMixin, View):
    def get(self, request, product):
        raise SuspiciousOperation("Only POST method allowed")

    def post(self, request, product):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product)
        cart.add_product(product, 1, False)
        return render(request, "store/_cart.html", {"cart": cart})


class CartAddBarcode(LoginRequiredMixin, View):
    def get(self, request):
        raise SuspiciousOperation("Only POST method allowed")
    def post(self, request):
        cart = Cart(request)
        barcode = request.POST["barcode"].strip()
        product = Product.objects.filter(barcode=barcode).first()
        error = False
        if product is None:
            price = get_dummy_barcode_data(barcode)
            if price is not None:
                product = Product.generate_one_time_product(price, barcode)
                cart.add_product(product, 1, True)
            else:
                error = True
        else:
            cart.add_product(product, 1, False)
        return render(
            request, "store/_barcode_response.html", {"cart": cart, "error": error}
        )


@login_required
@transaction.atomic
def checkout(request):
    ok = Cart(request).checkout(request)
    if ok:
        return HttpResponseRedirect(reverse("logout"))
    else:
        raise SuspiciousOperation("Not enough credit")
