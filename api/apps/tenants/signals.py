from axes.signals import user_locked_out
from django.dispatch import receiver
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request


@receiver(user_locked_out)
def raise_permission_denied(*args, **kwargs):
    if isinstance(kwargs['request'], Request):
        # throw PermissionDenied only for requests from DRF
        raise PermissionDenied("Too many failed login attempts")
