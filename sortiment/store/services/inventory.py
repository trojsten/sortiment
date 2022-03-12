from dataclasses import dataclass
from typing import Optional, Iterable, Any

from django.db.models import QuerySet

from sortiment.store.models import Product, Room, Inventory


@dataclass
class ProductWithInventory:
    product: Product
    local_inventory: int = 0
    global_inventory: int = 0


def get_products_inventories(queryset: QuerySet, local: Optional[Room] = None) -> list[ProductWithInventory]:
    queryset = queryset.prefetch_related("inventory_set")
    output: list[ProductWithInventory] = []

    for product in queryset:
        pwi = ProductWithInventory(product)
        inventories = product.inventory_set.all()
        pwi.global_inventory = sum(map(lambda x: x.amount, inventories))
        pwi.local_inventory = sum(map(lambda x: x.amount, filter(lambda x: x.room == local, inventories)))
        output.append(pwi)

    sort_products_inventories(output)
    return output


def sort_products_inventories(products: list[ProductWithInventory]):
    # sort alphabetically
    products.sort(key=lambda x: x.product.name)

    # sort unavailable last
    products.sort(key=lambda x: 0 if x.local_inventory > 0 else 1)

