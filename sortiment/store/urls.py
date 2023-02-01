from django.urls import path
from store.views import settings, storefront

app_name = "store"
urlpatterns = [
    path("", storefront.product_list, name="product_list"),
    path("products/", settings.EventView.as_view(), name="product_management"),
    path("add_product/", settings.AddProductView.as_view(), name="add_product"),
    path("purchases/", storefront.purchase_history, name="purchase_history"),
    path("stats/", storefront.StatsView.as_view(), name="stats"),
    path("checkout/", storefront.checkout, name="checkout"),
    path(
        "cart/<int:product>/remove/",
        storefront.CartRemoveView.as_view(),
        name="cart_remove",
    ),
    path("cart/<int:product>/add/", storefront.CartAddView.as_view(), name="cart_add"),
    path(
        "cart/add_barcode/",
        storefront.CartAddBarcode.as_view(),
        name="cart_add_barcode",
    ),
    path("products/search/", settings.SearchView.as_view(), name="product_search"),
    path("products/discard/", settings.DiscardView.as_view(), name="product_discard"),
    path("products/transfer/", settings.product_transfer, name="product_transfer"),
    path("products/edit/", settings.EditProductView.as_view(), name="product_edit"),
    path(
        "products/import/", settings.ProductImportView.as_view(), name="product_import"
    ),
    path("inventory/", settings.InventoryView.as_view(), name="inventory"),
]
