"""sortiment URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from users import views

urlpatterns = [
    path("", views.UserListView.as_view(), name="user_list"),
    path("login/<int:user_id>/", views.LoginUserView.as_view(), name="login"),
    path("logout/", views.LogoutUserView.as_view(), name="logout"),
    path("create/", views.CreateUserView.as_view(), name="create"),
    path("creditmovement/", views.CreditMovementView.as_view(), name="creditmovement"),
    path(
        "credaddwithdrowal/",
        views.CreditChangeView.as_view(),
        name="credaddwithdrowal",
    ),
]
