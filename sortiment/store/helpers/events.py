from decimal import Decimal

from store.models import Product, Warehouse, WarehouseEvent
from users.models import SortimentUser


def new_import(
    user: SortimentUser,
    product: Product,
    warehouse: Warehouse,
    quantity: int,
    price: Decimal,
):
    WarehouseEvent.objects.create(
        user=user,
        product=product,
        warehouse=warehouse,
        type=WarehouseEvent.EventType.IMPORT,
        quantity=quantity,
        retail_price=price,
        price=price,
    )


def new_purchase(
    user: SortimentUser, product: Product, warehouse: Warehouse, quantity: int
):
    WarehouseEvent.objects.create(
        user=user,
        product=product,
        warehouse=warehouse,
        type=WarehouseEvent.EventType.PURCHASE,
        quantity=-quantity,
        retail_price=product.price,
        price=product.price,
    )


def new_correction(
    user: SortimentUser, product: Product, warehouse: Warehouse, quantity: int
):
    WarehouseEvent.objects.create(
        user=user,
        product=product,
        warehouse=warehouse,
        type=WarehouseEvent.EventType.CORRECTION,
        quantity=quantity,
        retail_price=0,
        price=0,
    )


def new_discard(
    user: SortimentUser, product: Product, warehouse: Warehouse, quantity: int
):
    WarehouseEvent.objects.create(
        user=user,
        product=product,
        warehouse=warehouse,
        type=WarehouseEvent.EventType.DISCARD,
        quantity=-quantity,
        retail_price=0,
        price=0,
    )


def new_transfer(
    user: SortimentUser,
    product: Product,
    from_warehouse: Warehouse,
    to_warehouse: Warehouse,
    quantity: int,
):
    WarehouseEvent.objects.create(
        user=user,
        product=product,
        warehouse=from_warehouse,
        type=WarehouseEvent.EventType.TRANSFER_OUT,
        quantity=-quantity,
        retail_price=0,
        price=product.price,
    )
    WarehouseEvent.objects.create(
        user=user,
        product=product,
        warehouse=to_warehouse,
        type=WarehouseEvent.EventType.TRANSFER_IN,
        quantity=quantity,
        retail_price=0,
        price=product.price,
    )
