from django.contrib.auth import login
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .admin import UserCreationForm
from .models import SortimentUser

def user_list(request):
    context = {'users': SortimentUser.objects.all().order_by('username')}
    return render(request, 'users/list.html', context)


def login_user(request, user_id):
    user = SortimentUser.objects.get(id=user_id)
    login(request, user)
    return HttpResponseRedirect(reverse('product_list'))

def create_user(request):
    print("nieco", flush=True)
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # form.cleaned_data
            print("save", flush=True)
            form.credit = 0
            form.save()
            return HttpResponseRedirect(reverse('list'))
        else:
            print("not save", flush=True)
    else:
        form = UserCreationForm()
    context = {'form': form}
    return render(request, 'users/create.html', context)