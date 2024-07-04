from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models.functions import Lower
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, FormView, ListView
from store.cart import CartContext

from sortiment.turbo import Form422Mixin

from .admin import UserCreationForm
from .forms import CreditChangeForm, CreditMovementForm
from .models import SortimentUser


class UserListView(ListView):
    template_name = "users/users_list.html"
    queryset = SortimentUser.objects.filter(is_active=True).order_by(
        "-is_guest", Lower("username")
    )
    context_object_name = "users"


class LoginUserView(View):
    def get(self, request, user_id):
        user = SortimentUser.objects.get(id=user_id)
        login(request, user)
        return HttpResponseRedirect(reverse("store:product_list"))


class LogoutUserView(View):
    def post(self, request):
        logout(request)
        return HttpResponseRedirect(reverse("user_list"))


class CreateUserView(Form422Mixin, CreateView):
    template_name = "users/create.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("user_list")

    def form_valid(self, form):
        messages.success(self.request, "Používateľ bol vytvorený.")
        return super().form_valid(form)


class CreditMovementView(LoginRequiredMixin, CartContext, Form422Mixin, FormView):
    form_class = CreditMovementForm
    template_name = "users/credit_movement.html"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    @transaction.atomic
    def form_valid(self, form):
        user = self.request.user
        money = form.cleaned_data.get("credit")
        user2 = form.cleaned_data.get("user")
        message = form.cleaned_data.get("message")
        message = f"{user}: {message}"
        user.make_credit_operation(-money, is_purchase=False, message=message)
        user2.make_credit_operation(money, is_purchase=False, message=message)
        messages.success(self.request, "Kredit bol presunutý.")
        return HttpResponseRedirect(reverse("store:product_list"))


class CreditChangeView(LoginRequiredMixin, CartContext, Form422Mixin, FormView):
    form_class = CreditChangeForm
    template_name = "users/credit_change.html"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    @transaction.atomic
    def form_valid(self, form):
        user = self.request.user
        money = form.cleaned_data.get("credit")
        user.make_credit_operation(money, is_purchase=False)
        if money > 0:
            messages.success(self.request, "Kredit bol nabitý.")
        else:
            messages.success(self.request, "Kredit bol vybratý.")
        return HttpResponseRedirect(reverse("store:product_list"))
