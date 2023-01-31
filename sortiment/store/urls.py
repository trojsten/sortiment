from django.urls import path

from . import views

app_name = "store"
urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("event.html", views.product_event, name="event"),
    path("add_product", views.add_product, name="add_product"),
    path("discard", views.discard, name="discard"),
    path('purchases/', views.purchase_history, name='purchase_history'),
    path('stats/', views.stats, name='stats'),
]
