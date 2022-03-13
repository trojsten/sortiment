from django.http import HttpRequest

from sortiment.store.models import Room


def get_room_from_request(request: HttpRequest) -> Room:
    """
    Returns Room object from request.
    """
    return Room.objects.first()     # TODO: Return real room
