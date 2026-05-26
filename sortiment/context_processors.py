import sortiment


def version(request):
    return {"SORTIMENT_VERSION": sortiment.VERSION}
