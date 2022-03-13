from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import BadRequest
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView

from sortiment.store.models import Product, Room
from sortiment.store.services.cart import Cart
from sortiment.store.services.inventory import get_products_inventories


class StoreView(LoginRequiredMixin, TemplateView):
    template_name = "store/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        products = Product.objects.filter(inventory__amount__gt=0)
        pwi = get_products_inventories(products, Room.objects.first())
        ctx["items"] = pwi
        ctx["cart"] = Cart.from_cookie(self.request.session.get("cart"))
        return ctx


@login_required
def cart_add(request, product):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    cart = Cart.from_cookie(request.session.get("cart"))
    product = get_object_or_404(Product, id=product)
    cart.add(product)

    request.session["cart"] = cart.to_cookie()
    return render(request, "store/_cart.html", {"cart": cart})


@login_required
def cart_scan(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    cart = Cart.from_cookie(request.session.get("cart"))
    # TODO: Room filter
    product = Product.objects.filter(ean=request.POST.get("ean"), inventory__amount__gt=0).first()
    if product:
        cart.add(product)

    request.session["cart"] = cart.to_cookie()
    return render(request, "store/_cart.html", {"cart": cart})


@login_required
def cart_remove(request, product):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    cart = Cart.from_cookie(request.session.get("cart"))
    product = get_object_or_404(Product, id=product)
    cart.sub(product)

    request.session["cart"] = cart.to_cookie()
    return render(request, "store/_cart.html", {"cart": cart})
