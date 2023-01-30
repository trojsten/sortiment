from django.urls import path

from . import views

app_name = "store"
urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("event.html", views.product_event, name="event"),
    path("insert.html", views.insert, name="insert"),
]
