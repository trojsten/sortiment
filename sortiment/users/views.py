from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, FormView
from django_htmx.http import HttpResponseClientRedirect

from sortiment.store.models import Room
from sortiment.store.services.room import get_room_from_request
from sortiment.transactions.models import CreditTransaction
from sortiment.users.forms import CreditAdjustmentForm
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


class CreditView(LoginRequiredMixin, FormView):
    template_name = "users/settings/credit.html"
    form_class = CreditAdjustmentForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        u: User = self.request.user
        u.credit += form.cleaned_data["amount"]
        u.save()

        tx = CreditTransaction()
        tx.actor = u
        tx.room = get_room_from_request(self.request)
        tx.price = form.cleaned_data["amount"]
        tx.save()

        return redirect("settings_credit")

