import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q, F
from django.db.models.aggregates import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.timezone import now
from django.views import View
from django.views.generic import TemplateView
from users.models import CreditLog, SortimentUser

from store.cart import Cart, CartContext
from store.helpers import get_dummy_barcode_data, get_warehouse
from store.logic import get_product_list
from store.models import Product, Tag, Warehouse, WarehouseEvent


class ProductListView(LoginRequiredMixin, CartContext, TemplateView):
    template_name = "store/products.html"

    def get_queryset(self):
        products = Product.objects.filter(is_dummy=False)

        query = self.request.GET.get("query")
        if query:
            exact = Product.objects.filter(barcode=query)
            if exact.exists():
                return exact

            dummy_price = get_dummy_barcode_data(query)
            if dummy_price:
                dummy_obj = Product.generate_one_time_product(dummy_price, query)
                return Product.objects.filter(id=dummy_obj.id)

            products = products.filter(
                Q(name__unaccent__icontains=query) | Q(barcode__startswith=query)
            )

        # only show products that have active tag
        tag = self.request.GET.get("tag")
        if tag:
            products = products.filter(tags__name=tag)

        return products

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        warehouse_id = get_warehouse(self.request)

        products = self.get_queryset()
        ctx["products"] = get_product_list(products, warehouse_id, self.request.user)
        ctx["tags"] = Tag.objects.all()
        ctx["show_dummy_hint"] = self.request.GET.get("query", "").startswith("55")

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

class StatsDataView(View):

    def get(self, request, graph):
        warehouse = get_warehouse(self.request)
        data = {}
        if graph == "products_alltime":
            data['title'] = 'Počet'
            data['type'] = 'bar'
            data['data'] = []
            res = list(
                WarehouseEvent.objects.filter(warehouse=warehouse, quantity__lte=0).values('product__name').annotate(total_count=Sum("quantity")).order_by("total_count")[:15]
            )
            for row in res:
                data['data'].append({
                    'label': row['product__name'],
                    'value': -row['total_count'],
                })
        elif graph == "products_lastmonth":
            date = now().date() - timedelta(days=30)
            data['title'] = 'Počet'
            data['type'] = 'bar'
            data['data'] = []
            res = list(
                WarehouseEvent.objects.filter(warehouse=warehouse, timestamp__gte=date, quantity__lte=0).values('product__name').annotate(
                    total_count=Sum("quantity")).order_by("total_count")[:15]
            )

            for row in res:
                data['data'].append({
                    'label': row['product__name'],
                    'value': -row['total_count'],
                })

        elif graph == "users_spending":
            date = now().date() - timedelta(days=30)
            data['title'] = '€'
            data['type'] = 'pie'
            data['data'] = []
            res = list(
                WarehouseEvent.objects.filter(warehouse=warehouse, timestamp__gte=date, quantity__lte=0).values('user__username').annotate(
                    total_spent=Sum(F('quantity') * F('price'))
                ).order_by('total_spent')
            )

            for row in res:
                data['data'].append({
                    'label': row['user__username'],
                    'value': -float(row['total_spent']),
                })

        return HttpResponse(json.dumps(data), content_type="application/json")


class CartRemoveView(LoginRequiredMixin, View):
    def post(self, request, product):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product)
        cart.remove_product(product, 1)
        return render(request, "store/_cart.html", {"cart": cart})


class CartAddView(LoginRequiredMixin, View):
    def post(self, request, product):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product)
        cart.add_product(product, 1, False)
        return render(request, "store/_cart.html", {"cart": cart})


class CheckoutView(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request):
        ok = Cart(request).checkout(request)
        if ok:
            messages.success(request, "Nákup bol úspešný!")
            logout(request)
            return redirect("user_list")
        else:
            return redirect("store:product_list")
