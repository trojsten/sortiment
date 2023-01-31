from django.urls import path

from . import views

app_name = "store"
urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("event.html", views.product_event, name="event"),
    path("add_product", views.add_product, name="add_product"),
    path("insert.html", views.insert, name="insert"),
    path("discard", views.discard, name="discard"),
    path("purchases/", views.purchase_history, name="purchase_history"),
    path("stats/", views.stats, name="stats"),
    path("cart/<int:product>/remove/", views.cart_remove, name="cart_remove"),
    path("cart/<int:product>/add/", views.cart_add, name="cart_add"),
]
