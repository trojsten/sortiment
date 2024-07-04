import re

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from ipware import get_client_ip

from store.models import Warehouse


def get_warehouse(request: HttpRequest) -> Warehouse:
    ip, _ = get_client_ip(request)
    warehouse = Warehouse.objects.filter(ip=ip).first()
    if not warehouse:
        raise PermissionDenied()
    return warehouse


def get_dummy_barcode_data(barcode):
    if re.match("^5{6}[0-9]{5}$", barcode):
        return int(barcode[6:]) / 100
    return None
