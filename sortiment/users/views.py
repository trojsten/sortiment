from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView
from django_htmx.http import HttpResponseClientRedirect

from sortiment.users.models import User


class UserListView(ListView):
    model = User
    template_name = "users/user_list.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("store")
        return super(UserListView, self).dispatch(request, *args, **kwargs)


class LoginView(View):
    def post(self, *args, **kwargs):
        login(self.request, User.objects.get(id=kwargs["user_id"]))
        return HttpResponseClientRedirect(reverse("store"))
