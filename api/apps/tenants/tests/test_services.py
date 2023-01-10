from datetime import timedelta
from typing import cast
from unittest.mock import MagicMock

import pytest
from django.contrib import auth
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.utils import timezone

from apps.core.factories import SessionRequestFactory
from apps.privacy.factories import PrivacyPolicyFactory
from apps.tenants.factories import (
    USER_PASSWORD,
    TenantFactory,
    TenantInvitationFactory,
    TenantUserRelationFactory,
    UserFactory,
)
from apps.tenants.models import TenantInvitation, TenantUserRelation
from apps.tenants.services import (
    accept_tenant_invitation,
    change_password_reset_password,
    change_user_password,
    create_tenant_user,
    decode_password_reset_token,
    expire_invitation,
    generate_password_reset_token,
    invite_tenant_user,
    login_tenant_user,
    reset_password,
    send_password_reset_email,
    send_tenant_is_ready_email,
    signup_user,
    update_user_avatar,
    update_user_profile,
)


@pytest.mark.django_db
class TestSendTenantIsReadyEmail:
    def test_unable_to_send_email_to_inactive_tenant(self):
        tenant = TenantFactory(is_active=False)

        TenantUserRelationFactory(tenant=tenant, role=TenantUserRelation.TenantUserRole.ADMIN)

        with pytest.raises(ValueError) as ex:
            send_tenant_is_ready_email(tenant)

        assert str(ex.value) == f'Unable to send the email for tenant "{tenant.name}". Inactive tenant.'

    def test_send_email_to_active_tenant(self):
        tenant = TenantFactory()
        admin = UserFactory()

        TenantUserRelationFactory(user=admin, tenant=tenant, role=TenantUserRelation.TenantUserRole.ADMIN)
        TenantUserRelationFactory(user__is_active=False, tenant=tenant, role=TenantUserRelation.TenantUserRole.ADMIN)
        TenantUserRelationFactory(tenant=tenant, role=TenantUserRelation.TenantUserRole.MEMBER)

        assert send_tenant_is_ready_email(tenant) == 1
        assert len(mail.outbox) == 1
        email = mail.outbox[0]

        assert email.subject == 'You account is ready'
        assert email.to == [admin.email]


@pytest.mark.django_db
class TestInviteTenantUser:
    def test_invite_user(self):
        tenant = TenantFactory()
        email_address = "test-invitation-email@example.com"

        invitation = invite_tenant_user(tenant, email_address)

        assert invitation.is_valid is True
        assert invitation.is_expired is False
        assert invitation.email == email_address
        assert invitation.tenant == tenant

        assert len(mail.outbox) == 1
        email = mail.outbox[0]

        assert email.subject == f"You've been invited to Stepwise by {tenant.name}"
        assert email.to == [email_address]

    def test_should_cancel_active_invitations(self):
        user = UserFactory()
        tenant = TenantFactory()

        active_invitation_1 = TenantInvitationFactory(email=user.email, tenant=tenant)
        active_invitation_2 = TenantInvitationFactory(email=user.email)
        active_invitation_3 = TenantInvitationFactory(tenant=tenant)

        new_invitation = invite_tenant_user(tenant, user.email)

        active_invitation_1.refresh_from_db()
        active_invitation_2.refresh_from_db()
        active_invitation_3.refresh_from_db()

        assert active_invitation_1.is_active is False
        assert active_invitation_2.is_active is True
        assert active_invitation_3.is_active is True

        assert active_invitation_1.is_expired is False
        assert active_invitation_2.is_expired is False
        assert active_invitation_3.is_expired is False

        assert active_invitation_1.is_valid is False
        assert active_invitation_2.is_valid is True
        assert active_invitation_3.is_valid is True

        assert new_invitation.is_active is True
        assert new_invitation.is_valid is True
        assert new_invitation.is_expired is False

    def test_should_raise_validation_error_for_inactive_tenant(self):
        tenant = TenantFactory(is_active=False)

        with pytest.raises(ValidationError, match='Unable to invite user. Inactive tenant.'):
            invite_tenant_user(tenant, "test-invitation-email@example.com")

    def test_should_raise_validation_error_for_existing_tenant_user(self):
        tenant_user = TenantUserRelationFactory()

        with pytest.raises(ValidationError, match="User already belongs to tenant"):
            invite_tenant_user(tenant_user.tenant, tenant_user.user.email)

    def test_should_raise_validation_error_for_inactive_user(self):
        user = UserFactory(is_active=False)
        tenant = TenantFactory()

        with pytest.raises(ValidationError, match="Unable to invite user. Inactive user."):
            invite_tenant_user(tenant, user.email)


@pytest.mark.django_db
class TestAcceptTenantInvitation:
    def test_should_accept_invitation(self):
        user = UserFactory()
        invitation = TenantInvitationFactory(email=user.email)

        tenant_user = accept_tenant_invitation(invitation)
        invitation.refresh_from_db()

        assert invitation.is_active is False
        assert tenant_user.user == user
        assert tenant_user.role == TenantUserRelation.TenantUserRole.MEMBER
        assert tenant_user.tenant == invitation.tenant

    def test_should_raise_validation_error_for_non_existing_user(self):
        invitation = TenantInvitationFactory()

        with pytest.raises(ValidationError, match="Unable to accept invitation. User does not exist."):
            accept_tenant_invitation(invitation)

    def test_should_raise_validation_error_for_inactive_user(self):
        user = UserFactory(is_active=False)
        invitation = TenantInvitationFactory(email=user.email)

        with pytest.raises(ValidationError, match="Unable to accept invitation. User is not active."):
            accept_tenant_invitation(invitation)


@pytest.mark.django_db
class TestSignupUser:
    @pytest.mark.parametrize('phone_number', ('', '+48 000 000 000'))
    def test_signup_user(self, phone_number: str):
        PrivacyPolicyFactory()
        invitation = TenantInvitationFactory()

        first_name = "John"
        last_name = "Doe"
        company_name = "Company Name"
        password = "strong password"

        tenant_user = signup_user(
            invitation=invitation,
            first_name=first_name,
            last_name=last_name,
            company_name=company_name,
            password=password,
            phone_number=phone_number,
        )

        assert tenant_user.user.username == invitation.email
        assert tenant_user.user.email == invitation.email
        assert tenant_user.user.first_name == first_name
        assert tenant_user.user.last_name == last_name
        assert tenant_user.user.company_name == company_name
        assert tenant_user.user.phone_number == phone_number
        assert tenant_user.user.check_password(password) is True
        assert tenant_user.tenant == invitation.tenant

        invitation.refresh_from_db()

        assert invitation.is_active is False
        assert invitation.is_valid is False

    def test_should_raise_validation_error_for_inactive_invitation(self):
        invitation = TenantInvitationFactory(is_active=False)

        with pytest.raises(ValidationError, match="Invitation is no longer valid."):
            signup_user(
                invitation=invitation,
                first_name="First Name",
                last_name="Last Name",
                company_name="Company Name",
                password="Password",
            )

    def test_should_raise_validation_error_for_expired_invitation(self):
        invitation = TenantInvitationFactory(expires_at=timezone.now() - timedelta(days=1))

        with pytest.raises(ValidationError, match="Invitation is no longer valid."):
            signup_user(
                invitation=invitation,
                first_name="First Name",
                last_name="Last Name",
                company_name="Company Name",
                password="Password",
            )

    def test_should_raise_validation_error_for_existing_user(self):
        user = UserFactory()
        invitation = TenantInvitationFactory(email=user.email)

        with pytest.raises(ValidationError, match="User with this email already exists."):
            signup_user(
                invitation=invitation,
                first_name="First Name",
                last_name="Last Name",
                company_name="Company Name",
                password="Password",
            )

    def test_new_password_must_meet_validator_requirements(self):
        invitation = TenantInvitationFactory()

        with pytest.raises(ValidationError) as ex:
            signup_user(
                invitation=invitation,
                first_name="First Name",
                last_name="Last Name",
                company_name="Company Name",
                password="123456",
            )

        assert ex.value.message_dict == {
            'password': [
                'This password is too short. It must contain at least 8 characters.',
                'This password is too common.',
                'This password is entirely numeric.',
            ]
        }


@pytest.mark.django_db
class TestLoginTenantUser:
    @pytest.mark.parametrize('remember_me', (True, False))
    def test_should_login_tenant_user(self, remember_me: bool):
        tenant_user = TenantUserRelationFactory()
        tenant_user.user.set_password("test-password")
        tenant_user.user.save()
        request = cast(HttpRequest, SessionRequestFactory())

        logged_in_tenant_user = login_tenant_user(
            request=request,
            tenant_id=tenant_user.tenant.pk,
            email=tenant_user.user.email,
            password="test-password",
            remember_me=remember_me,
        )

        assert logged_in_tenant_user.user.is_authenticated is True
        assert logged_in_tenant_user.user.pk == tenant_user.user.pk

        assert request.session.get_expire_at_browser_close() is not remember_me
        user = auth.get_user(request)
        assert user.is_authenticated

    def test_should_raise_validation_error_for_inactive_user(self):
        tenant_user = TenantUserRelationFactory(user__is_active=False)
        tenant_user.user.set_password("test-password")
        tenant_user.user.save()

        with pytest.raises(ValidationError, match="Invalid credentials."):
            login_tenant_user(
                request=cast(HttpRequest, SessionRequestFactory()),
                tenant_id=tenant_user.tenant.pk,
                email=tenant_user.user.email,
                password="test-password",
                remember_me=False,
            )

    def test_should_raise_validation_error_for_inactive_tenant(self):
        tenant_user = TenantUserRelationFactory(tenant__is_active=False)
        tenant_user.user.set_password("test-password")
        tenant_user.user.save()

        with pytest.raises(ValidationError, match="Unable to login. Inactive tenant."):
            login_tenant_user(
                request=cast(HttpRequest, SessionRequestFactory()),
                tenant_id=tenant_user.tenant.pk,
                email=tenant_user.user.email,
                password="test-password",
                remember_me=False,
            )

    def test_should_raise_validation_error_for_non_tenant_user(self):
        tenant_user = TenantUserRelationFactory()
        tenant_user.user.set_password("test-password")

        another_tenant = TenantFactory()

        with pytest.raises(ValidationError, match="Invalid credentials."):
            login_tenant_user(
                request=cast(HttpRequest, SessionRequestFactory()),
                tenant_id=another_tenant.pk,
                email=tenant_user.user.email,
                password="test-password",
                remember_me=True,
            )

    def test_should_raise_validation_error_for_invalid_credentials(self):
        tenant_user = TenantUserRelationFactory()
        tenant_user.user.set_password("test-password")

        with pytest.raises(ValidationError, match="Invalid credentials."):
            login_tenant_user(
                request=cast(HttpRequest, SessionRequestFactory()),
                tenant_id=tenant_user.tenant.pk,
                email=tenant_user.user.email,
                password="wrong-password",
                remember_me=True,
            )


@pytest.mark.django_db
class TestCreateTenantUser:
    def test_should_create_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()

        tenant_user = create_tenant_user(tenant=tenant, user=user)

        assert tenant_user.pk is not None
        assert tenant_user.tenant == tenant
        assert tenant_user.user == user

    def test_should_not_create_tenant_user_for_already_existing_tenant_user(self):
        tenant_user = TenantUserRelationFactory()

        with pytest.raises(ValidationError, match="User already belongs to tenant."):
            create_tenant_user(tenant=tenant_user.tenant, user=tenant_user.user)


@pytest.mark.django_db
class TestExpireInvitation:
    def test_should_expire_invitation(self):
        invitation = TenantInvitationFactory()

        assert invitation.is_expired is False

        expired_invitation = expire_invitation(invitation)

        assert expired_invitation.pk == invitation.pk
        assert expired_invitation.is_expired is False
        assert expired_invitation.is_valid is False
        assert expired_invitation.status == TenantInvitation.InvitationStatus.EXPIRED


@pytest.mark.django_db
class TestChangeUserPassword:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = UserFactory()

    def test_old_password_must_be_valid(self):
        with pytest.raises(ValidationError) as ex:
            change_user_password(
                request=MagicMock(),
                user=self.user,
                old_password="wrong old password",
                new_password="new_password1",
            )

        assert ex.value.message_dict == {'old_password': ['Old password is not correct']}

    def test_new_password_must_meet_validator_requirements(self):
        with pytest.raises(ValidationError) as ex:
            change_user_password(
                request=MagicMock(),
                user=self.user,
                old_password=USER_PASSWORD,
                new_password="123456",
            )

        assert ex.value.message_dict == {
            'new_password': [
                'This password is too short. It must contain at least 8 characters.',
                'This password is too common.',
                'This password is entirely numeric.',
            ]
        }

    def test_change_password(self):
        new_password = 'new password'
        change_user_password(
            request=MagicMock(),
            user=self.user,
            old_password=USER_PASSWORD,
            new_password=new_password,
        )

        self.user.refresh_from_db()

        assert self.user.check_password(new_password)


@pytest.mark.django_db
def test_generate_password_reset_token():
    user = UserFactory()

    uid, token = generate_password_reset_token(user)

    assert decode_password_reset_token(uid=uid, token=token) == user


@pytest.mark.django_db
def test_send_password_reset_email():
    tenant = TenantFactory()
    user = UserFactory()

    assert send_password_reset_email(tenant=tenant, user=user) == 1

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    assert email.subject == 'Password reset'
    assert email.to == [user.email]


@pytest.mark.django_db
class TestResetPassword:
    def test_reset_password_for_nonexistent_user(self):
        tenant = TenantFactory()
        user = UserFactory()

        reset_passwords = reset_password(tenant=tenant, email=user.email)

        assert reset_passwords == 0

    def test_reset_password_for_active_user(self):
        tenant_user = TenantUserRelationFactory()
        reset_passwords = reset_password(tenant=tenant_user.tenant, email=tenant_user.user.email)

        assert reset_passwords == 1

    def test_reset_password_for_inactive_user(self):
        tenant_user = TenantUserRelationFactory(user__is_active=False)
        reset_passwords = reset_password(tenant=tenant_user.tenant, email=tenant_user.user.email)

        assert reset_passwords == 0


@pytest.mark.django_db
class TestDecodePasswordResetToken:
    def test_invalid_token(self):
        with pytest.raises(ValidationError) as ex:
            decode_password_reset_token(uid='uid', token='token')

        assert ex.value.message == 'Invalid token'

    def test_valid_token(self):
        user = UserFactory()
        uid, token = generate_password_reset_token(user)

        decoded_user = decode_password_reset_token(uid=uid, token=token)

        assert decoded_user == user

    def test_expired_token(self):
        user = UserFactory()
        uid, token = generate_password_reset_token(user)

        user.set_password('new password')
        user.save()

        with pytest.raises(ValidationError) as ex:
            decode_password_reset_token(uid=uid, token=token)

        assert ex.value.message == 'Expired token'


@pytest.mark.django_db
class TestChangePasswordResetPassword:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = UserFactory()
        self.uid, self.token = generate_password_reset_token(self.user)

    def test_password_must_meet_validator_requirements(self):
        with pytest.raises(ValidationError) as ex:
            change_password_reset_password(uid=self.uid, token=self.token, password='123456')

        assert ex.value.message_dict == {
            'password': [
                'This password is too short. It must contain at least 8 characters.',
                'This password is too common.',
                'This password is entirely numeric.',
            ]
        }

    def test_change_password(self):
        password = '8HoF4cb8Mb4ER2GqhZVQ'
        change_password_reset_password(uid=self.uid, token=self.token, password=password)

        self.user.refresh_from_db()

        assert self.user.check_password(password)


@pytest.mark.django_db
class TestUpdateUserProfile:
    @pytest.mark.parametrize(
        "update_user_profile_kwargs",
        (
            {
                "first_name": "new first name",
                "last_name": "new last name",
                "company_name": "new company name",
            },
            {
                "first_name": "new first name",
                "last_name": "new last name",
                "company_name": "new company name",
                "phone_number": "+48999000999",
            },
        ),
    )
    def test_should_update_user_profile(self, update_user_profile_kwargs: dict[str, str]):
        user = UserFactory(phone_number="+48000000000")

        updated_user = update_user_profile(
            user=user,
            **update_user_profile_kwargs,
        )

        assert updated_user.pk == user.pk
        assert updated_user.first_name == update_user_profile_kwargs["first_name"]
        assert updated_user.last_name == update_user_profile_kwargs["last_name"]
        assert updated_user.company_name == update_user_profile_kwargs["company_name"]
        assert updated_user.phone_number == update_user_profile_kwargs.get("phone_number", "")


@pytest.mark.django_db
class TestUpdateUserAvatar:
    def test_should_update_user_avatar(self):
        user = UserFactory()
        uploaded_file = SimpleUploadedFile(name="filename.png", content=b"test-file-content", content_type="image/png")

        updated_user = update_user_avatar(
            user,
            uploaded_file,
        )

        assert updated_user.pk == user.pk
        assert updated_user.profile_image.file.read() == b"test-file-content"
