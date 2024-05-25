from adminapp.models import *


def default(request):
    cat = category.objects.all()
    return {"cat": cat}
