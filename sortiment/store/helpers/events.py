from decimal import Decimal

from django.db.models import Sum
from store.models import Product, Warehouse, WarehouseEvent
from users.models import SortimentUser


def get_average_price(product: Product) -> Decimal:
    average_price = 0
    prices = product.warehousestate_set.aggregate(
        quantity=Sum("quantity"), price=Sum("total_price")
    )
    if prices["quantity"] is not None and prices["quantity"] > 0:
        average_price = Decimal(prices["price"] / prices["quantity"])
    return average_price


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
        price=get_average_price(product),
    )


def new_correction(
    user: SortimentUser, product: Product, warehouse: Warehouse, quantity: int
):
    avg = get_average_price(product)
    WarehouseEvent.objects.create(
        user=user,
        product=product,
        warehouse=warehouse,
        type=WarehouseEvent.EventType.CORRECTION,
        quantity=quantity,
        retail_price=avg,
        price=avg,
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
        price=get_average_price(product),
    )


def new_transfer(
    user: SortimentUser,
    product: Product,
    from_warehouse: Warehouse,
    to_warehouse: Warehouse,
    quantity: int,
):
    avg = get_average_price(product)
    WarehouseEvent.objects.create(
        user=user,
        product=product,
        warehouse=from_warehouse,
        type=WarehouseEvent.EventType.TRANSFER_OUT,
        quantity=-quantity,
        retail_price=0,
        price=avg,
    )
    WarehouseEvent.objects.create(
        user=user,
        product=product,
        warehouse=to_warehouse,
        type=WarehouseEvent.EventType.TRANSFER_IN,
        quantity=quantity,
        retail_price=0,
        price=avg,
    )
