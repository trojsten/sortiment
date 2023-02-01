from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, FormView, ListView

from .admin import UserCreationForm
from .forms import CreditAddAndWithdrawalForm, CreditMovementForm
from .models import SortimentUser


class UserListView(ListView):
    template_name = "users/users_list.html"
    queryset = SortimentUser.objects.order_by("-is_guest", "username")
    context_object_name = "users"


class LoginUserView(View):
    def get(self, request, user_id):
        user = SortimentUser.objects.get(id=user_id)
        login(request, user)
        return HttpResponseRedirect(reverse("store:product_list"))


class LogoutUserView(View):
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(reverse("user_list"))


class CreateUserView(CreateView):
    template_name = "users/create.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("user_list")


class CreditMovementView(FormView):
    form_class = CreditMovementForm
    template_name = "users/creditmovement.html"

    def form_valid(self, form):
        user = self.request.user
        if user.is_guest:
            return
        money = -form.cleaned_data.get("credit")
        if user.can_pay(money):
            user2 = form.cleaned_data.get("user")
            user.make_credit_operation(-money, is_purchase=False)
            user2.make_credit_operation(money, is_purchase=False)
            return HttpResponseRedirect(reverse("store:product_list"))
        else:
            form.add_error("credit", "Nemáš na to dosť peňazí")


class CreditAddWithdrawalView(FormView):
    form_class = CreditAddAndWithdrawalForm
    template_name = "users/credaddwithdrowal.html"

    def form_valid(self, form):
        user = self.request.user
        if not isinstance(user, SortimentUser) or user.is_guest:
            return
        money = form.cleaned_data.get("credit")
        if user.can_pay(money):
            user.make_credit_operation(money, is_purchase=False)
            return HttpResponseRedirect(reverse("store:product_list"))
        else:
            form.add_error("credit", "Nemáš na to dosť peňazí")
