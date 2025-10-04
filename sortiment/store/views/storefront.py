import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F, Q
from django.db.models.aggregates import Sum
from django.db.models.functions import TruncMonth, TruncWeek
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

        # Basic financial stats
        ctx["total_price_when_buy"] = Warehouse.get_global_products_price_when_buy_sum()
        ctx["total_price_for_sale"] = Warehouse.get_global_products_price_for_sale_sum()
        ctx["local_price_when_buy"] = warehouse.get_products_price_when_buy_sum()
        ctx["local_price_for_sale"] = warehouse.get_products_price_for_sale_sum()
        ctx["credit_sum"] = SortimentUser.get_credit_sum()
        ctx["total_profit"] = ctx["total_price_for_sale"] - ctx["total_price_when_buy"]
        ctx["local_profit"] = ctx["local_price_for_sale"] - ctx["local_price_when_buy"]

        # User statistics
        ctx["top_creditors"] = list(
            SortimentUser.objects.filter(is_active=True).order_by("-credit")[:15]
        )
        return ctx


class StatsDataView(View):
    def get_products_data(self, warehouse, time_period):
        """Get product sales data for monthly or all-time"""
        data = {"title": "Počet kusov", "type": "bar", "data": []}

        queryset = WarehouseEvent.objects.filter(
            warehouse=warehouse, quantity__lte=0, type=WarehouseEvent.EventType.PURCHASE
        )

        if time_period == "monthly":
            queryset = queryset.filter(timestamp__gte=now().date() - timedelta(days=30))

        res = list(
            queryset.values("product__name")
            .annotate(total_count=Sum("quantity"))
            .order_by("total_count")[:15]
        )

        for row in res:
            data["data"].append(
                {
                    "label": row["product__name"],
                    "value": -row["total_count"],
                }
            )

        return data

    def get_users_spending_data(self, warehouse):
        """Get top users by spending for last month"""
        data = {"title": "€", "type": "pie", "data": []}
        date = now().date() - timedelta(days=30)

        res = list(
            WarehouseEvent.objects.filter(
                warehouse=warehouse,
                timestamp__gte=date,
                quantity__lte=0,
                type=WarehouseEvent.EventType.PURCHASE,
            )
            .values("user__username")
            .annotate(total_spent=Sum(F("quantity") * F("price")))
            .order_by("total_spent")[:10]
        )

        for row in res:
            data["data"].append(
                {
                    "label": row["user__username"],
                    "value": -float(row["total_spent"]),
                }
            )

        return data

    def get_revenue_trends_data(self, warehouse):
        """Get revenue trends over last 6 months"""
        data = {"title": "Príjmy (€)", "type": "line", "data": []}
        start_date = now().date() - timedelta(days=180)

        res = list(
            WarehouseEvent.objects.filter(
                warehouse=warehouse,
                timestamp__gte=start_date,
                quantity__lte=0,
                type=WarehouseEvent.EventType.PURCHASE,
            )
            .annotate(month=TruncMonth("timestamp"))
            .values("month")
            .annotate(revenue=Sum(F("quantity") * F("price")))
            .order_by("month")
        )

        for row in res:
            data["data"].append(
                {
                    "label": row["month"].strftime("%m/%Y"),
                    "value": -float(row["revenue"]),
                }
            )

        return data

    def get_category_sales_data(self, warehouse):
        """Get sales by product category for last month"""
        data = {"title": "Predaj podľa kategórií", "type": "pie", "data": []}
        date = now().date() - timedelta(days=30)

        res = list(
            WarehouseEvent.objects.filter(
                warehouse=warehouse,
                type=WarehouseEvent.EventType.PURCHASE,
                timestamp__gte=date,
                quantity__lte=0,
                product__tags__isnull=False,
            )
            .values("product__tags__name")
            .annotate(total_count=Sum("quantity"))
            .order_by("total_count")[:10]
        )

        for row in res:
            data["data"].append(
                {
                    "label": row["product__tags__name"] or "Bez kategórie",
                    "value": -row["total_count"],
                }
            )

        return data

    def get(self, request, graph):
        warehouse = get_warehouse(self.request)

        if graph == "products_alltime":
            data = self.get_products_data(warehouse, "alltime")
        elif graph == "products_lastmonth":
            data = self.get_products_data(warehouse, "monthly")
        elif graph == "users_spending":
            data = self.get_users_spending_data(warehouse)
        elif graph == "revenue_trends":
            data = self.get_revenue_trends_data(warehouse)
        elif graph == "category_sales":
            data = self.get_category_sales_data(warehouse)
        else:
            data = {"title": "", "type": "bar", "data": []}

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


class WarehouseTransactionHistoryView(TemplateView):
    template_name = "store/warehouse_history.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        warehouse = get_warehouse(self.request)
        end = timezone.now() - timedelta(days=60)

        filter_type = self.request.GET.get("filter", "all")

        events = []

        if filter_type in ["all", "warehouse"]:
            wh_events = (
                WarehouseEvent.objects.filter(warehouse=warehouse)
                .order_by("-timestamp")
                .select_related("product", "user")
                .filter(timestamp__gte=end)
            )
            for e in wh_events:
                events.append(
                    {"event": e, "timestamp": e.timestamp, "type": "warehouse"}
                )

        if filter_type in ["all", "credit"]:
            credit_events = (
                CreditLog.objects.filter(
                    warehouse=warehouse, timestamp__gte=end, is_purchase=False
                )
                .order_by("-timestamp")
                .select_related("user")
            )
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

        ctx.update(
            {
                "events": events,
                "filter": filter_type,
                "warehouse": warehouse,
            }
        )
        return ctx


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


class PurchaseStatsDataView(LoginRequiredMixin, View):
    def get_spending_data(self, user, period_type):
        """Get spending data grouped by week or month"""
        data = {"title": "€", "type": "line", "data": []}

        if period_type == "weeks":
            start_date = now().date() - timedelta(weeks=12)
            trunc_func = TruncWeek("timestamp")
            date_format = "%d.%m.%Y"
        else:  # months
            start_date = now().date() - timedelta(days=365)
            trunc_func = TruncMonth("timestamp")
            date_format = "%m/%Y"

        res = list(
            WarehouseEvent.objects.filter(
                user=user,
                type=WarehouseEvent.EventType.PURCHASE,
                timestamp__gte=start_date,
                quantity__lte=0,
            )
            .annotate(period=trunc_func)
            .values("period")
            .annotate(spent=Sum(F("quantity") * F("price")))
            .order_by("period")
        )

        for row in res:
            data["data"].append(
                {
                    "label": row["period"].strftime(date_format),
                    "value": -float(row["spent"]),
                }
            )

        return data

    def get_products_data(self, user, time_period):
        """Get product purchase data for monthly or all-time"""
        data = {"title": "Počet", "type": "bar", "data": []}

        queryset = WarehouseEvent.objects.filter(
            user=user,
            type=WarehouseEvent.EventType.PURCHASE,
            quantity__lte=0,
        )

        if time_period == "monthly":
            queryset = queryset.filter(timestamp__gte=now().date() - timedelta(days=30))

        res = list(
            queryset.values("product__name")
            .annotate(total_count=Sum("quantity"))
            .order_by("total_count")[:15]
        )

        for row in res:
            data["data"].append(
                {
                    "label": row["product__name"],
                    "value": -row["total_count"],
                }
            )

        return data

    def get(self, request, graph):
        user = request.user

        if graph == "spend_weeks":
            data = self.get_spending_data(user, "weeks")
        elif graph == "spend_months":
            data = self.get_spending_data(user, "months")
        elif graph == "products_monthly":
            data = self.get_products_data(user, "monthly")
        elif graph == "products_alltime":
            data = self.get_products_data(user, "alltime")
        else:
            data = {"title": "", "type": "bar", "data": []}

        return HttpResponse(json.dumps(data), content_type="application/json")
