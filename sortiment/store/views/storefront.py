from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Tuple

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import SuspiciousOperation
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from store.cart import Cart
from store.helpers import get_dummy_barcode_data, get_warehouse
from store.models import Product, Tag, Warehouse, WarehouseEvent, WarehouseState
from users.models import CreditLog, SortimentUser


def get_inventory_state(warehouse_id: Warehouse):
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

    purchases_d = defaultdict(list)
    for event in WarehouseEvent.objects.filter(
        warehouse__exact=warehouse_id, type__exact=WarehouseEvent.EventType.PURCHASE
    ):
        purchases_d[event.product.name].append((event.timestamp, event.quantity))

    return state_d, all_state_d, purchases_d


def annotate_products(products, warehouse_id: Warehouse):
    infty_string = "&#8734;"
    now, datetime_min = timezone.now(), timezone.make_aware(datetime.min)
    state_d, all_state_d, purchases_d = get_inventory_state(warehouse_id)
    for p in products:
        p.qty = state_d[p.id] if not p.is_unlimited else infty_string
        p.totqty = all_state_d[p.id] if not p.is_unlimited else infty_string
        p.timestamp = max(purchases_d.get(p.name, [(datetime_min, 0)]))[0]
        # q will be negative, low priority will be at the top of the list
        p.priority = sum(q * 0.95 ** (now - t).days for t, q in purchases_d[p.name])


def product_list_sort_key(p):
    if p.is_unlimited or p.qty > 0:
        availability = -1
    elif p.totqty > 0:
        availability = 0
    else:
        availability = 1
    return (
        availability,
        p.priority,
        -p.timestamp.timestamp(),
        p.name,
    )


class ProductListView(LoginRequiredMixin, TemplateView):
    template_name = "store/products.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        warehouse_id = get_warehouse(self.request)

        tags = []
        for tag in Tag.objects.all():
            tags.append(
                {"name": tag.name, "active": "tag-%s" % tag.name in self.request.GET}
            )
        active_tags = [tag["name"] for tag in tags if tag["active"]]

        # only show products that have all active tags

        products = Product.objects.filter(is_dummy=False)
        for tag in active_tags:
            products = products.filter(tags__name__contains=tag)

        annotate_products(products, warehouse_id)
        products = sorted(products, key=product_list_sort_key)

        ctx["prods"] = products
        ctx["user"] = self.request.user
        ctx["tags"] = tags
        ctx["cart"] = Cart(self.request)

        return ctx


class PurchaseHistoryView(LoginRequiredMixin, TemplateView):
    template_name = "store/purchase_history.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        end = timezone.now() - timedelta(days=60)
        wh_events = (
            WarehouseEvent.objects.filter(
                user=self.request.user, type=WarehouseEvent.EventType.PURCHASE
            )
            .order_by("-timestamp")
            .select_related("product")
            .filter(timestamp__gte=end)
        )
        credit_events = CreditLog.objects.filter(
            user=self.request.user, timestamp__gte=end, is_purchase=False
        ).order_by("-timestamp")

        events = []
        for e in wh_events:
            events.append({"event": e, "timestamp": e.timestamp, "type": "product"})
        for e in credit_events:
            events.append(
                {
                    "event": e,
                    "timestamp": e.timestamp,
                    "type": "credit",
                    "message": e.message,
                }
            )

        events.sort(key=lambda x: x["timestamp"], reverse=True)
        ctx.update({"events": events, "cart": Cart(self.request)})
        return ctx


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
        ctx["total_profit"] = ctx["total_price_for_sale"] - ctx["total_price_when_buy"]
        ctx["local_profit"] = ctx["local_price_for_sale"] - ctx["local_price_when_buy"]
        ctx["top_creditors"] = list(
            SortimentUser.objects.filter(is_active=True).order_by("-credit")[:15]
        )
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


def filter_products(request) -> Tuple[bool, bool, List[Product], bool]:
    barcode = request.POST["barcode"].strip()
    commit = barcode and "commit" in request.GET

    filters = [
        lambda: (False, Product.objects.filter(barcode=barcode)),
        lambda: (
            True,
            [
                Product.generate_one_time_product(price, barcode)
                for price in [get_dummy_barcode_data(barcode)]
                if price is not None
            ],
        ),
        lambda: (
            False,
            Product.objects.filter(barcode__startswith=barcode)
            | Product.objects.filter(name__icontains=barcode),
        ),
    ]
    dummy, prods = False, []
    for f in filters:
        dummy, prods = f()
        if prods:
            break
    error = not prods
    return error, dummy, prods, commit


class ProductListSearchbox(LoginRequiredMixin, View):
    def get(self, request):
        raise SuspiciousOperation("Only POST method allowed")

    def post(self, request):
        cart = Cart(request)
        error, dummy, prods, commit = filter_products(request)
        update_prods = None
        if not error and commit:
            cart.add_product(prods[0], 1, dummy)
            update_prods = False
        else:
            warehouse_id = get_warehouse(request)
            annotate_products(prods, warehouse_id)
            prods = sorted(prods, key=product_list_sort_key)
            update_prods = True
        return render(
            request,
            "store/_barcode_response.html",
            {
                "cart": cart,
                "error": error,
                "prods": prods,
                "update_prods": update_prods,
                "clear_search": commit,
            },
        )


class CheckoutView(LoginRequiredMixin, View):
    @transaction.atomic
    def get(self, request):
        ok = Cart(request).checkout(request)
        if ok:
            messages.success(request, "Nákup bol úspešný!")
            return HttpResponseRedirect(reverse("logout"))
        else:
            raise SuspiciousOperation("Not enough credit")
