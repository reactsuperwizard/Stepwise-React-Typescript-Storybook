from datetime import timedelta

import factory.fuzzy
from django.conf import settings
from django.utils import timezone

from apps.privacy.models import DeleteAccountRequest, PrivacyPolicy, PrivacyPolicyConsent
from apps.tenants.factories import UserFactory


class PrivacyPolicyFactory(factory.django.DjangoModelFactory):
    title = factory.Sequence(lambda n: f"privacy-policy-{n}")
    text = factory.Faker('sentence')
    is_active = True

    class Meta:
        model = PrivacyPolicy


class PrivacyPolicyConsentFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    policy = factory.SubFactory(PrivacyPolicyFactory)

    class Meta:
        model = PrivacyPolicyConsent


class DeleteAccountRequestFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    is_active = True
    execute_at = factory.LazyFunction(lambda: timezone.now() + timedelta(days=settings.REMOVE_ACCOUNTS_AFTER_DAYS))

    class Meta:
        model = DeleteAccountRequest
