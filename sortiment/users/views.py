from django.contrib.auth import login
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import SortimentUser

def user_list(request):
    context = {'users': SortimentUser.objects.all()}
    return render(request, 'users/list.html', context)

def login_user(request, user_id):
    user = SortimentUser.objects.get(id=user_id)
    login(request, user)
    return HttpResponseRedirect(reverse('product_list'))