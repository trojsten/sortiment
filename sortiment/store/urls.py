from django.urls import path

from . import views

app_name = "store"
urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("event.html", views.product_event, name="event"),
    path("add_product.html", views.add_product, name="add_product"),
    path("discard.html", views.discard, name="discard"),

]
