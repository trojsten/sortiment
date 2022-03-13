from dataclasses import dataclass
from typing import Optional

from sortiment.store.models import Product


@dataclass
class CartProduct:
    product: Product
    amount: int

    @property
    def total(self):
        return self.product.price * self.amount


class Cart:
    def __init__(self):
        self.products: list[CartProduct] = []

    def to_cookie(self) -> dict:
        return {x.product.id: x.amount for x in self.products}

    @classmethod
    def from_cookie(cls, cookie: Optional[dict]):
        if cookie is None:
            return cls()

        ids = cookie.keys()
        products = {x.id: x for x in Product.objects.filter(id__in=ids).all()}
        cart = cls()
        cart.products = [CartProduct(products[int(k)], v) for k, v in cookie.items()]
        return cart

    def total(self):
        return sum([x.total for x in self.products])

    def add(self, product: Product, n: int = 1):
        for i, cp in enumerate(self.products):
            if cp.product == product:
                self.products[i].amount += n
                return

        self.products.append(CartProduct(product, n))

    def sub(self, product: Product, n: int = 1):
        for i, cp in enumerate(self.products):
            if cp.product == product:
                self.products[i].amount -= n
                if self.products[i].amount <= 0:
                    del self.products[i]
                break

    def __iter__(self):
        self._i = 0
        return self

    def __next__(self):
        if self._i >= len(self.products):
            raise StopIteration()
        p = self.products[self._i]
        self._i += 1
        return p

