from django.urls import path

from . import views

app_name = "store"
urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("products/", views.EventView.as_view(), name="product_management"),
    path("add_product/", views.AddProductView.as_view(), name="add_product"),
    path("purchases/", views.purchase_history, name="purchase_history"),
    path("stats/", views.stats, name="stats"),
    path("checkout/", views.checkout, name="checkout"),
    path("cart/<int:product>/remove/", views.cart_remove, name="cart_remove"),
    path("cart/<int:product>/add/", views.cart_add, name="cart_add"),
    path("cart/add_barcode/", views.cart_add_barcode, name="cart_add_barcode"),
    path("products/search/", views.search, name="product_search"),
    path("products/discard/", views.DiscardView.as_view(), name="product_discard"),
    path("products/transfer/", views.product_transfer, name="product_transfer"),
    path("products/import/", views.ProductImportView.as_view(), name="product_import"),
    path("inventory/", views.inventory, name="inventory"),
]
