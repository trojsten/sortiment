from django.urls import path

from . import views

app_name = "store"
urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("products/", views.product_management, name="product_management"),
    path("add_product/", views.add_product, name="add_product"),
    path("discard/", views.discard, name="discard"),
    path("purchases/", views.purchase_history, name="purchase_history"),
    path("stats/", views.stats, name="stats"),
    path("checkout/", views.checkout, name="checkout"),
    path("cart/<int:product>/remove/", views.cart_remove, name="cart_remove"),
    path("cart/<int:product>/add/", views.cart_add, name="cart_add"),
    path("cart/add_barcode/", views.cart_add_barcode, name="cart_add_barcode"),
    path("products/search/", views.search, name="product_search"),
    path("products/import/", views.product_import, name="product_import"),
    path("products/transfer/", views.product_transfer, name="product_transfer"),
    path("inventory/", views.inventory, name="inventory"),
]
