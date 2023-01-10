import random

import factory.fuzzy
from django.utils import timezone

from apps.kims.models import KimsAPI, Tag, TagDataType, TagValue, Vessel


class KimsAPIFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: f"username-{n}")
    password = factory.Sequence(lambda n: f'password-{n}')
    base_url = factory.Sequence(lambda n: f'https://example.com/Routing/{n}/')

    class Meta:
        model = KimsAPI


class VesselFactory(factory.django.DjangoModelFactory):
    kims_api = factory.SubFactory(KimsAPIFactory)
    name = factory.Sequence(lambda n: f"vessel-{n}")
    kims_vessel_id = factory.Sequence(lambda n: f'kims-vessel-id-{n}')
    tags_synced_at = None
    is_active = True

    class Meta:
        model = Vessel


class TagFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"emp-{n}")
    vessel = factory.SubFactory(VesselFactory)
    data_type = 'Double'
    deleted = False

    class Meta:
        model = Tag


def generate_tag_value(tag: Tag) -> float | bool:
    match tag.data_type:
        case TagDataType.DOUBLE:
            return round(random.uniform(0, 1000), 2)
        case TagDataType.OBJECT:
            return random.getrandbits(1)
        case TagDataType.BOOLEAN:
            return random.choice([1.0, 0.0])
        case TagDataType.SINGLE:
            return round(random.uniform(0, 1000), 2)
        case TagDataType.INT_32:
            return round(random.uniform(0, 1000), 2)

    raise ValueError(f"Unknown tag data type {tag.data_type}.")


class TagValueFactory(factory.django.DjangoModelFactory):
    tag = factory.SubFactory(TagFactory)
    mean = factory.LazyAttribute(lambda tag_value: str(generate_tag_value(tag_value.tag)))
    average = factory.LazyAttribute(lambda tag_value: str(generate_tag_value(tag_value.tag)))
    date = factory.LazyFunction(lambda: timezone.now().replace(minute=0, second=0, microsecond=0))

    class Meta:
        model = TagValue
