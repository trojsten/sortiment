from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

from django.contrib.auth.models import User
from django.db.models import F, FloatField, Max, Q, Sum
from django.db.models.functions import ExtractDay
from django.utils import timezone

from store.models import Product, Warehouse, WarehouseEvent, WarehouseState


@dataclass
class InventoryQuantities:
    local: int
    total: int


def get_inventory_quantities(warehouse: Warehouse) -> dict[int, InventoryQuantities]:
    quantities = defaultdict(lambda: InventoryQuantities(0, 0))

    states = WarehouseState.objects.values("product_id").annotate(
        local=Sum("quantity", filter=Q(warehouse=warehouse), default=0),
        total=Sum("quantity"),
    )

    for state in states:
        quantities[state["product_id"]] = InventoryQuantities(
            state["local"], state["total"]
        )

    return quantities


@dataclass
class PurchaseStats:
    global_priority: float = 0
    user_priority: float = 0
    last_purchase: datetime = datetime.min


def get_purchases(warehouse: Warehouse, user: User) -> dict[int, PurchaseStats]:
    purchases = defaultdict(lambda: PurchaseStats())

    cutoff = timezone.now() - timedelta(days=60)

    events = (
        WarehouseEvent.objects.filter(
            warehouse=warehouse,
            type=WarehouseEvent.EventType.PURCHASE,
            timestamp__gte=cutoff,
        )
        .values("product_id")
        .annotate(
            global_priority=Sum(
                -F("quantity")
                * 0.95 ** ExtractDay(timezone.now().date() - F("timestamp")),
                output_field=FloatField(),
            ),
            user_priority=Sum(
                -F("quantity")
                * 0.95 ** ExtractDay(timezone.now().date() - F("timestamp")),
                output_field=FloatField(),
                filter=Q(user=user),
                default=0,
            ),
            last_purchase=Max("timestamp"),
        )
    )

    for event in events:
        purchases[event["product_id"]] = PurchaseStats(
            event["global_priority"], event["user_priority"], event["last_purchase"]
        )

    return purchases


@dataclass
class AnnotatedProduct:
    product: Product
    stats: PurchaseStats
    local_quantity: int = 0
    total_quantity: int = 0


def get_priority_value(e: WarehouseEvent):
    return -e.quantity * 0.95 ** (timezone.now() - e.timestamp).days


def annotate_products(
    products: Iterable[Product], warehouse: Warehouse, user: User
) -> list[AnnotatedProduct]:
    quantities = get_inventory_quantities(warehouse)
    purchases = get_purchases(warehouse, user)

    annotated: list[AnnotatedProduct] = []
    for p in products:
        ap = AnnotatedProduct(p, purchases[p.id])

        if not p.is_unlimited:
            ap.local_quantity = quantities[p.id].local
            ap.total_quantity = quantities[p.id].total

        annotated.append(ap)
    return annotated


def product_sort_key(p: AnnotatedProduct):
    if p.product.is_unlimited or p.local_quantity > 0:
        availability = 1
    elif p.total_quantity > 0:
        availability = 0
    else:
        availability = -1

    return (
        availability,
        p.stats.user_priority,
        p.stats.global_priority,
        p.stats.last_purchase,
        p.product.name,
    )


def get_product_list(
    products: Iterable[Product], warehouse: Warehouse, user: User
) -> list[AnnotatedProduct]:
    annotated = annotate_products(products, warehouse, user)
    return sorted(annotated, key=product_sort_key, reverse=True)
