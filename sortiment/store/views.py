from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from sortiment.store.models import Product, Room
from sortiment.store.services.inventory import get_products_inventories


class StoreView(LoginRequiredMixin, TemplateView):
    template_name = "store/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        products = Product.objects.filter(inventory__amount__gt=0)
        pwi = get_products_inventories(products, Room.objects.first())
        ctx["items"] = pwi
        return ctx
