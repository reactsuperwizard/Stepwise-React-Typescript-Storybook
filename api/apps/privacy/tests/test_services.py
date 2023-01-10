import pytest
from django.core import mail
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.privacy.factories import DeleteAccountRequestFactory, PrivacyPolicyConsentFactory, PrivacyPolicyFactory
from apps.privacy.models import PrivacyPolicy, PrivacyPolicyConsent
from apps.privacy.services import (
    accept_active_policy,
    activate_policy,
    create_delete_account_request,
    delete_account,
    is_user_consent_valid,
)
from apps.tenants.factories import TenantUserRelationFactory, UserFactory
from apps.tenants.models import TenantUserRelation


@pytest.mark.django_db
class TestIsUserConsentValid:
    def test_should_be_valid(self):
        consent = PrivacyPolicyConsentFactory()

        is_valid = is_user_consent_valid(consent.user)

        assert is_valid is True

    def test_should_not_be_valid_for_outdated_consent(self):
        PrivacyPolicyFactory(is_active=True)
        consent = PrivacyPolicyConsentFactory(policy__is_active=False)

        is_valid = is_user_consent_valid(consent.user)

        assert is_valid is False

    def test_should_not_be_valid_for_revoked_consent(self):
        consent = PrivacyPolicyConsentFactory(revoked_at=timezone.now())

        is_valid = is_user_consent_valid(consent.user)

        assert is_valid is False


@pytest.mark.django_db
class TestAcceptActivePolicy:
    def test_should_accept_active_policy(self):
        user = UserFactory()
        active_policy = PrivacyPolicyFactory()
        PrivacyPolicyFactory(is_active=False)

        consent = accept_active_policy(user)

        assert consent.revoked_at is None
        assert consent.user == user
        assert consent.policy == active_policy

    def test_should_accept_policy_and_revoke_outdated_consents(self):
        active_policy = PrivacyPolicyFactory()
        outdated_policy = PrivacyPolicyFactory(is_active=False)
        outdated_consent = PrivacyPolicyConsentFactory(policy=outdated_policy)

        consent = accept_active_policy(outdated_consent.user)

        assert consent.revoked_at is None
        assert consent.user == outdated_consent.user
        assert consent.policy == active_policy

        outdated_consent.refresh_from_db()
        assert outdated_consent.revoked_at is not None
        assert outdated_consent.revoked_reason == PrivacyPolicyConsent.RevokedReason.UPDATED

    def test_should_accept_the_same_policy(self):
        active_policy = PrivacyPolicyFactory()
        outdated_consent = PrivacyPolicyConsentFactory(
            policy=active_policy, revoked_reason=PrivacyPolicyConsent.RevokedReason.UPDATED, revoked_at=timezone.now()
        )

        consent = accept_active_policy(outdated_consent.user)

        assert consent.user == outdated_consent.user
        assert consent.revoked_at is None

    def test_should_raise_does_not_exist_for_no_active_policy(self):
        user = UserFactory()

        with pytest.raises(PrivacyPolicy.DoesNotExist):
            accept_active_policy(user)

    def test_should_raise_validation_error_for_existing_consent(self):
        active_policy = PrivacyPolicyFactory()
        consent = PrivacyPolicyConsentFactory(policy=active_policy)

        with pytest.raises(ValidationError, match="Unable to accept Privacy Policy. Consent already given."):
            accept_active_policy(consent.user)


@pytest.mark.django_db
class TestActivatePolicy:
    def test_should_activate_policy(self):
        active_policy = PrivacyPolicyFactory()
        new_policy = PrivacyPolicyFactory(is_active=False)

        user = UserFactory()
        tenant_active_user_1, _ = TenantUserRelationFactory.create_batch(2, user=user)
        TenantUserRelationFactory(tenant__is_active=False)
        TenantUserRelationFactory(user__is_active=False)

        new_active_policy = activate_policy(new_policy)
        assert new_active_policy.is_active is True
        assert new_active_policy.pk == new_policy.pk

        active_policy.refresh_from_db()
        assert active_policy.is_active is False

        assert len(mail.outbox) == 1
        email = mail.outbox[0]

        assert email.subject == "Privacy policy has changed."
        assert email.to == [tenant_active_user_1.user.email]

    def should_raise_validation_error_for_active_policy(self):
        active_policy = PrivacyPolicyFactory()

        with pytest.raises(ValidationError, match="Policy is already active."):
            activate_policy(active_policy)


@pytest.mark.django_db
class TestCreateDeleteAccountRequest:
    def test_should_create_delete_account_request(self):
        user = UserFactory()

        delete_account_request = create_delete_account_request(user)

        assert delete_account_request.is_active is True
        assert delete_account_request.user == user
        assert len(mail.outbox) == 1
        email = mail.outbox[0]

        assert email.subject == "You have requested us to delete your account."
        assert email.to == [user.email]

        user.refresh_from_db()
        assert user.is_active is False


@pytest.mark.django_db
class TestDeleteAccount:
    def test_should_delete_account(self):
        user = UserFactory(phone_number="+48000000000")
        TenantUserRelationFactory(user=user)
        user_pk = user.pk
        user_email = user.email
        delete_account_request = DeleteAccountRequestFactory(user=user)

        executed_delete_account_request = delete_account(delete_account_request)
        user.refresh_from_db()

        assert executed_delete_account_request.is_active is False

        assert user.pk == user_pk
        assert user.email == f"deleted-user-{user.pk}@example.com"
        assert user.username == f"deleted-user-{user.pk}@example.com"
        assert user.first_name == ""
        assert user.last_name == ""
        assert user.phone_number == ""
        assert user.is_active is False

        assert len(mail.outbox) == 1
        email = mail.outbox[0]

        assert email.subject == "Your account has been deleted."
        assert email.to == [user_email]

        assert TenantUserRelation.objects.filter(user=user).exists() is False

    def test_should_raise_value_error_for_inactive_request(self):
        delete_account_request = DeleteAccountRequestFactory(is_active=False)

        with pytest.raises(ValueError, match="Delete account request is not active."):
            delete_account(delete_account_request)
