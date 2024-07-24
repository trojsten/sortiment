from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

from django.contrib.auth.models import AbstractUser, User
from django.db.models import Sum
from django.utils import timezone

from store.models import Product, Warehouse, WarehouseEvent, WarehouseState


@dataclass
class InventoryQuantities:
    local: int
    total: int


def get_inventory_quantities(warehouse: Warehouse) -> dict[int, InventoryQuantities]:
    quantities = defaultdict(lambda: InventoryQuantities(0, 0))

    local_states = WarehouseState.objects.filter(warehouse=warehouse)
    for state in local_states:
        quantities[state.product_id].local = state.quantity

    global_states = WarehouseState.objects.values("product_id").annotate(
        total=Sum("quantity")
    )
    for state in global_states:
        quantities[state["product_id"]].total = state["total"]

    return quantities


def get_purchases(warehouse: Warehouse) -> dict[int, list[WarehouseEvent]]:
    purchases = defaultdict(list)

    cutoff = timezone.now() - timedelta(days=60)
    events = WarehouseEvent.objects.filter(
        warehouse=warehouse,
        type=WarehouseEvent.EventType.PURCHASE,
        timestamp__gte=cutoff,
    ).order_by("-timestamp")
    for event in events:
        purchases[event.product_id].append(event)

    return purchases


@dataclass
class AnnotatedProduct:
    product: Product
    local_quantity: int = 0
    total_quantity: int = 0
    last_purchase: datetime | None = None
    global_priority: float = 0
    user_priority: float = 0


def get_priority_value(e: WarehouseEvent):
    return -e.quantity * 0.95 ** (timezone.now() - e.timestamp).days


def annotate_products(
    products: Iterable[Product], warehouse: Warehouse, user: AbstractUser | None = None
) -> list[AnnotatedProduct]:
    quantities = get_inventory_quantities(warehouse)
    purchases = get_purchases(warehouse)

    annotated: list[AnnotatedProduct] = []
    for p in products:
        ap = AnnotatedProduct(p)

        if not p.is_unlimited:
            ap.local_quantity = quantities[p.id].local
            ap.total_quantity = quantities[p.id].total

        purchase_log = purchases[p.id]
        if purchase_log:
            ap.last_purchase = purchase_log[0].timestamp

            ap.global_priority = sum(map(get_priority_value, purchase_log))
            user_purchases = list(filter(lambda e: e.user_id == user.id, purchase_log))
            if user_purchases:
                ap.user_priority = sum(map(get_priority_value, user_purchases))

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
        p.user_priority,
        p.global_priority,
        p.last_purchase if p.last_purchase else datetime.min,
        p.product.name,
    )


def get_product_list(
    products: Iterable[Product], warehouse: Warehouse, user: User | None = None
) -> list[AnnotatedProduct]:
    annotated = annotate_products(products, warehouse, user)
    return sorted(annotated, key=product_sort_key, reverse=True)
