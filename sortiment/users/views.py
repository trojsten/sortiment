from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .admin import UserCreationForm
from .forms import CreditAddAndWithdrawalForm, CreditMovementForm
from .models import SortimentUser


def user_list(request):
    context = {"users": SortimentUser.objects.all().order_by("-is_guest", "username")}
    return render(request, "users/users_list.html", context)


def login_user(request, user_id):
    user = SortimentUser.objects.get(id=user_id)
    login(request, user)
    return HttpResponseRedirect(reverse("store:product_list"))


def logout_user(request):
    logout(request)
    return HttpResponseRedirect(reverse("user_list"))


def create_user(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("user_list"))
    else:
        form = UserCreationForm()
    context = {"form": form}
    return render(request, "users/create.html", context)


def credit(request):
    if request.method == "POST":
        credit_movement_form = CreditMovementForm(request.POST)
        if credit_movement_form.is_valid():
            user = request.user
            if not isinstance(user, SortimentUser) or user.is_guest:
                return
            money = credit_movement_form.cleaned_data.get("credit")
            if user.can_pay(money):
                user2 = credit_movement_form.cleaned_data.get("user")
                if user2.id == user.id:
                    credit_movement_form.add_error("user", "Nemôžeš poslať peniaze samému sebe.")
                else:
                    user.make_credit_operation(-money, is_purchase=False)
                    user2.make_credit_operation(money, is_purchase=False)
                    return HttpResponseRedirect(reverse("store:product_list"))
            else:
                credit_movement_form.add_error("credit", "Nemáš na to dosť peňazí")

        credit_add_and_withdrawal_form = CreditAddAndWithdrawalForm(request.POST)
        if credit_add_and_withdrawal_form.is_valid():
            user = request.user
            if not isinstance(user, SortimentUser) or user.is_guest:
                return
            money = credit_add_and_withdrawal_form.cleaned_data.get("credit")
            if user.can_pay(money):
                user.make_credit_operation(money, is_purchase=False)
                return HttpResponseRedirect(reverse("store:product_list"))
            else:
                credit_add_and_withdrawal_form.add_error(
                    "credit", "Nemáš na to dosť peňazí"
                )
    else:
        credit_add_and_withdrawal_form = CreditAddAndWithdrawalForm()

        credit_movement_form = CreditMovementForm()
        credit_movement_form.remove_user_from_choices(request.user)

    context = {
        "credit_movement_form": credit_movement_form,
        "credit_add_and_withdrawal_form": credit_add_and_withdrawal_form,
    }
    return render(request, "users/credit_movement.html", context)
