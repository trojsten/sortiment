from django.contrib.auth import login
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .admin import UserCreationForm
from .forms import CreditMovementForm, CreditAddAndWithdrawalForm
from .models import SortimentUser

def user_list(request):
    context = {'users': SortimentUser.objects.all().order_by('username')}
    return render(request, 'users/list.html', context)


def login_user(request, user_id):
    user = SortimentUser.objects.get(id=user_id)
    login(request, user)
    return HttpResponseRedirect(reverse('product_list'))

def create_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('list'))
    else:
        form = UserCreationForm()
    context = {'form': form}
    return render(request, 'users/create.html', context)

def credit(request):
    if request.method == 'POST':
        credit_movement_form = CreditMovementForm(request.POST)
        if credit_movement_form.is_valid():
            user = request.user
            if not isinstance(user, SortimentUser):
                return
            money = credit_movement_form.cleaned_data.get('credit')
            if user.can_pay(money):
                user2 = credit_movement_form.cleaned_data.get('user')
                user.make_credit_operation(money)
                user2.make_credit_operation(-money)
                return HttpResponseRedirect(reverse('product_list'))
            else:
                credit_movement_form.add_error('credit', 'Nemáš na to dosť peňazí')

        credit_add_and_withdrawal_form = CreditAddAndWithdrawalForm(request.POST)
        if credit_add_and_withdrawal_form.is_valid():
            user = request.user
            if not isinstance(user, SortimentUser):
                return
            money = credit_add_and_withdrawal_form.cleaned_data.get('credit')
            if user.can_pay(money):
                user.make_credit_operation(money)
                return HttpResponseRedirect(reverse('product_list'))
            else:
                credit_add_and_withdrawal_form.add_error('credit', 'Nemáš na to dosť peňazí')
    else:
        credit_add_and_withdrawal_form = CreditAddAndWithdrawalForm()

        credit_movement_form = CreditMovementForm()

    context = {'credit_movement_form': credit_movement_form,
               'credit_add_and_withdrawal_form': credit_add_and_withdrawal_form}
    return render(request, 'users/credit_movement.html', context)