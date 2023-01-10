import logging
from typing import Tuple, Type

from django.db import models

logger = logging.getLogger(__name__)


def add_staff_permissions(model: Type[models.Model], permissions: Tuple[str, ...]) -> None:
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    logger.info(f'Adding staff permissions for model {model._meta.object_name}')

    staff_member_group, created = Group.objects.get_or_create(name="Staff Member")

    for permission in permissions:
        staff_member_group.permissions.add(
            Permission.objects.get(
                content_type=ContentType.objects.get_for_model(model), codename=f'{permission}_{model._meta.model_name}'
            )
        )
        logger.info(f'Added permission to {permission}')
