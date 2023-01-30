from django.http import HttpResponse
from django.shortcuts import render
from .models import Product, Warehouse, WarehouseState

def product_list(request): # , warehouse_name):

    # TODO send state of product in selected state


    prods = Product.objects.all()
    context = {
        "prods": prods
    }
    return render(request, "store/products.html", context)


# Create your views here.
