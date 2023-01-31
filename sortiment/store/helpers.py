from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from ipware import get_client_ip
from store.models import Warehouse


def get_warehouse(request: HttpRequest) -> Warehouse:
    ip = get_client_ip(request)
    warehouse = Warehouse.objects.filter(ip=ip).first()
    if not warehouse:
        raise PermissionDenied()
    return warehouse
