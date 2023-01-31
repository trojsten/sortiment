from dataclasses import dataclass

from django.http import HttpRequest
from store.models import Product


@dataclass
class CartItem:
    product: Product
    quantity: int

    @property
    def total_price(self):
        return self.product.price * self.quantity


class Cart:
    def __init__(self, request: HttpRequest):
        self.request = request
        self.items: list[CartItem] = []
        self._load_session()

    def _load_session(self):
        cart = self.request.session.get("cart", [])
        products = Product.objects.filter(id__in=[i["product"] for i in cart]).all()
        product_map = {p.id: p for p in products}
        self.items.clear()

        for item in cart:
            if item["product"] not in product_map:
                continue
            if item["quantity"] <= 0:
                continue
            self.items.append(CartItem(product_map[item["product"]], item["quantity"]))

    def _save_session(self):
        data = []
        for item in self.items:
            if item.quantity <= 0:
                continue
            data.append({"product": item.product.id, "quantity": item.quantity})
        self.request.session["cart"] = data

    def add_product(self, product: Product, quantity: int = 1):
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0.")

        for i in range(len(self.items)):
            item = self.items[i]
            if item.product == product:
                self.items[i].quantity += quantity
                self._save_session()
                return

        self.items.append(CartItem(product, quantity))
        self._save_session()

    def remove_product(self, product: Product, quantity: int = 1):
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0.")

        for i in range(len(self.items)):
            item = self.items[i]
            if item.product == product:
                item.quantity -= quantity
                self.items[i] = item
                if item.quantity <= 0:
                    del self.items[i]
                break

        self._save_session()

    @property
    def total_price(self):
        return sum([i.total_price for i in self.items])
