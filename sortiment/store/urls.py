from django.urls import path

from . import views
from .views import AddProductView, DiscardView, EventView, ProductImportView

app_name = "store"
urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("event/", EventView.as_view(), name="event"),
    path("add_product/", AddProductView.as_view(), name="add_product"),
    path("discard/", DiscardView.as_view(), name="discard"),
    path("transfer/", views.transfer, name="transfer"),
    path("purchases/", views.purchase_history, name="purchase_history"),
    path("stats/", views.stats, name="stats"),
    path("checkout/", views.checkout, name="checkout"),
    path("cart/<int:product>/remove/", views.cart_remove, name="cart_remove"),
    path("cart/<int:product>/add/", views.cart_add, name="cart_add"),
    path("cart/add_barcode/", views.cart_add_barcode, name="cart_add_barcode"),
    path("products/search/", views.search, name="product_search"),
    path("products/import/", ProductImportView.as_view(), name="product_import"),
    path("inventory/", views.inventory, name="inventory"),
]
