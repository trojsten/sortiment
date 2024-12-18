from django.urls import path

from store.views import settings, storefront

app_name = "store"
urlpatterns = [
    path("", storefront.ProductListView.as_view(), name="product_list"),
    path("products/", settings.EventView.as_view(), name="product_management"),
    path("reset/", settings.ResetView.as_view(), name="reset"),
    path("add_product/", settings.AddProductView.as_view(), name="add_product"),
    path(
        "purchases/", storefront.PurchaseHistoryView.as_view(), name="purchase_history"
    ),
    path("stats/", storefront.StatsView.as_view(), name="stats"),
    path(
        "stats/<str:graph>/data", storefront.StatsDataView.as_view(), name="stats_data"
    ),
    path("checkout/", storefront.CheckoutView.as_view(), name="checkout"),
    path(
        "cart/<int:product>/remove/",
        storefront.CartRemoveView.as_view(),
        name="cart_remove",
    ),
    path("cart/<int:product>/add/", storefront.CartAddView.as_view(), name="cart_add"),
    path("products/search/", settings.SearchView.as_view(), name="product_search"),
    path("products/discard/", settings.DiscardView.as_view(), name="product_discard"),
    path("products/edit/", settings.EditProductView.as_view(), name="product_edit"),
    path(
        "products/transfer/",
        settings.ProductTransferView.as_view(),
        name="product_transfer",
    ),
    path(
        "products/import/", settings.ProductImportView.as_view(), name="product_import"
    ),
    path("products/correction/", settings.CorrectionView.as_view(), name="correction"),
    path("inventory/", settings.InventoryView.as_view(), name="inventory"),
]
