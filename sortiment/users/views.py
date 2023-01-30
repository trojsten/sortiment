from django.contrib.auth import login
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .admin import UserCreationForm
from .forms import CreditMovementForm
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
        form = CreditMovementForm(request.POST)
        if form.is_valid():
            user = request.user
            if not isinstance(user, SortimentUser):
                return
            money = form.cleaned_data.get('credit')
            if user.can_pay(money):
                print('plati')
                user.make_credit_operation(money)
                return HttpResponseRedirect(reverse('product_list'))
            else:
                print('NEplati')
                form.add_error('credit', 'Nemáš na to dosť peňazí')
                return render(request, 'users/credit_movement.html', {'form': form})
    else:
        form = CreditMovementForm()
    context = {'form': form}
    return render(request, 'users/credit_movement.html', context)