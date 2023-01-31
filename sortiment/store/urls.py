from django.urls import path

from . import views

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("purchases/", views.purchase_history, name="purchase_history"),
    path("cart/<int:product>/remove/", views.cart_remove, name="cart_remove"),
    path("cart/<int:product>/add/", views.cart_add, name="cart_add"),
    # path('', views.index, name='index'),
    # path('<int:question_id>/', views.detail, name='detail'),
    # ex: /polls/5/results/
    # path('<int:question_id>/results/', views.results, name='results'),
    # ex: /polls/5/vote/
    # path('<int:question_id>/vote/', views.vote, name='vote'),
]
