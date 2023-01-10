from datetime import timedelta
from unittest import mock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient

from apps.privacy.factories import PrivacyPolicyFactory
from apps.tenants.factories import (
    USER_PASSWORD,
    TenantFactory,
    TenantInvitationFactory,
    TenantUserRelationFactory,
    UserFactory,
)
from apps.tenants.models import TenantInvitation, TenantUserRelation, User, UserRole
from apps.tenants.serializers import MeSerializer
from apps.tenants.services import generate_password_reset_token


@pytest.fixture
def password() -> str:
    return "password"


@pytest.fixture
def tenant_user(password: str) -> TenantUserRelation:
    tenant_user_relation = TenantUserRelationFactory(user__password=password)
    return tenant_user_relation


@pytest.fixture
def user_without_tenant() -> User:
    user = UserFactory()
    return user


@pytest.mark.django_db
class TestLoginApi:
    def test_should_login_user(self, api_client: APIClient, tenant_user: TenantUserRelation, password: str):
        url = reverse('tenants:login', kwargs={"tenant_id": tenant_user.tenant.pk})
        data = {
            "email": tenant_user.user.email,
            "password": password,
        }
        response = api_client.post(url, data)

        expected_response = {
            "id": tenant_user.user.pk,
            "first_name": tenant_user.user.first_name,
            "last_name": tenant_user.user.last_name,
            "role": tenant_user.user.role,
            "privacy_policy_consent_valid": False,
            'email': tenant_user.user.email,
            'profile_image': '',
            "company_name": tenant_user.user.company_name,
            "company": {"id": tenant_user.user.company.pk, "name": tenant_user.user.company.name},
            "phone_number": None,
        }
        assert response.status_code == 200
        assert response.data == expected_response

    def test_should_not_login_user_with_invalid_credentials(
        self, api_client: APIClient, tenant_user: TenantUserRelation
    ):
        url = reverse('tenants:login', kwargs={"tenant_id": tenant_user.tenant.pk})
        data = {
            "email": tenant_user.user.email,
            "password": "absolutely-wrong-password",
        }
        response = api_client.post(url, data)

        expected_response = {
            "detail": {
                "non_field_errors": [
                    "Invalid credentials.",
                ]
            }
        }
        assert response.status_code == 400
        assert response.data == expected_response

    def test_should_not_login_inactive_user(
        self, api_client: APIClient, tenant_user: TenantUserRelation, password: str
    ):
        tenant_user.user.is_active = False
        tenant_user.user.save()

        url = reverse('tenants:login', kwargs={"tenant_id": tenant_user.tenant.pk})
        data = {
            "email": tenant_user.user.email,
            "password": password,
        }
        response = api_client.post(url, data)

        expected_response = {
            "detail": {
                "non_field_errors": [
                    "Invalid credentials.",
                ]
            }
        }
        assert response.status_code == 400
        assert response.data == expected_response

    def test_should_not_login_user_without_access_to_tenant(
        self, api_client: APIClient, tenant_user: TenantUserRelation, user_without_tenant: User
    ):
        url = reverse('tenants:login', kwargs={"tenant_id": tenant_user.tenant.pk})
        data = {
            "email": user_without_tenant.email,
            "password": "wrong-password",
        }

        expected_response = {
            "detail": {
                "non_field_errors": [
                    "Invalid credentials.",
                ]
            }
        }
        response = api_client.post(url, data)
        assert response.status_code == 400
        assert response.data == expected_response

    def test_should_not_login_user_to_inactive_tenant(
        self, api_client: APIClient, tenant_user: TenantUserRelation, password: str
    ):
        tenant_user.tenant.is_active = False
        tenant_user.tenant.save()

        url = reverse('tenants:login', kwargs={"tenant_id": tenant_user.tenant.pk})
        data = {
            "email": tenant_user.user.email,
            "password": password,
        }

        expected_response = {
            "detail": {
                "non_field_errors": [
                    "Unable to login. Inactive tenant.",
                ]
            }
        }
        response = api_client.post(url, data)
        assert response.status_code == 400
        assert response.data == expected_response

    @override_settings(AXES_FAILURE_LIMIT=2)
    def test_should_lock_out_user_after_number_of_failed_attempts(
        self, api_client: APIClient, tenant_user: TenantUserRelation
    ):
        url = reverse('tenants:login', kwargs={"tenant_id": tenant_user.tenant.pk})
        data = {
            "email": tenant_user.user.email,
            "password": "absolutely-wrong-password",
        }
        first_response = api_client.post(url, data)

        assert first_response.status_code == 400
        assert first_response.data == {
            "detail": {
                "non_field_errors": [
                    "Invalid credentials.",
                ]
            }
        }

        second_response = api_client.post(url, data)

        assert second_response.status_code == 403
        assert second_response.data == {
            'detail': ErrorDetail(string='Too many failed login attempts', code='permission_denied')
        }

    @override_settings(AXES_FAILURE_LIMIT=1, DRF_RECAPTCHA_TESTING=True)
    def test_user_should_solve_captcha_after_being_locked_out(
        self, api_client: APIClient, tenant_user: TenantUserRelation, password: str
    ):
        login_url = reverse('tenants:login', kwargs={"tenant_id": tenant_user.tenant.pk})
        data = {
            "email": tenant_user.user.email,
            "password": "absolutely-wrong-password",
        }
        response = api_client.post(login_url, data)

        assert response.status_code == 403

        data = {
            **data,
            "password": password,
        }
        response = api_client.post(login_url, data)

        assert response.status_code == 400
        assert response.data == {
            'detail': {'recaptcha': [ErrorDetail(string='This field is required.', code='required')]}
        }

        data = {
            **data,
            "recaptcha": "solved_recaptcha",
        }
        response = api_client.post(login_url, data)

        assert response.status_code == 200


@pytest.mark.django_db
class TestLogoutApi:
    def test_should_logout_tenant_user(self, api_client: APIClient, tenant_user: TenantUserRelation):
        url = reverse('tenants:logout', kwargs={"tenant_id": tenant_user.tenant.pk})

        api_client.force_login(tenant_user.user)

        assert '_auth_user_id' in api_client.session

        response = api_client.post(url)

        assert '_auth_user_id' not in api_client.session
        assert response.status_code == 204
        assert response.data is None

    def test_should_be_forbidden_for_anonymous_user(self, api_client: APIClient, tenant_user: TenantUserRelation):
        url = reverse('tenants:logout', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.post(url)

        expected_response = {"detail": 'Authentication credentials were not provided.'}
        assert response.status_code == 403
        assert response.data == expected_response

    def test_should_be_forbidden_for_non_tenant_user(
        self, api_client: APIClient, tenant_user: TenantUserRelation, user_without_tenant: User
    ):
        url = reverse('tenants:logout', kwargs={"tenant_id": tenant_user.tenant.pk})
        api_client.force_authenticate(user_without_tenant)
        response = api_client.post(url)

        expected_response = {"detail": 'You do not have permission to perform this action.'}
        assert response.status_code == 403
        assert response.data == expected_response


@pytest.mark.django_db
class TestLockedApi:
    def test_user_should_not_be_locked(self, api_client: APIClient, tenant_user: TenantUserRelation):
        url = reverse('tenants:locked', kwargs={"tenant_id": tenant_user.tenant.pk})

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {'locked': False}

    @override_settings(AXES_FAILURE_LIMIT=1)
    def test_user_should_be_locked_after_failed_logins(self, api_client: APIClient, tenant_user: TenantUserRelation):
        login_url = reverse('tenants:login', kwargs={"tenant_id": tenant_user.tenant.pk})
        data = {
            "email": tenant_user.user.email,
            "password": "absolutely-wrong-password",
        }
        login_response = api_client.post(login_url, data)

        assert login_response.status_code == 403

        locked_url = reverse('tenants:locked', kwargs={"tenant_id": tenant_user.tenant.pk})
        locked_response = api_client.get(locked_url)

        assert locked_response.status_code == 200
        assert locked_response.data == {'locked': True}


@pytest.mark.django_db
class TestMeApi:
    def test_should_retrieve_tenant_user(self, api_client: APIClient, tenant_user: TenantUserRelation):
        url = reverse('tenants:me', kwargs={"tenant_id": tenant_user.tenant.pk})
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == MeSerializer(tenant_user.user).data

    def test_should_be_forbidden_for_anonymous_user(self, api_client: APIClient, tenant_user: TenantUserRelation):
        url = reverse('tenants:me', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.get(url)

        expected_response = {"detail": 'Authentication credentials were not provided.'}
        assert response.status_code == 403
        assert response.data == expected_response

    def test_should_be_forbidden_for_non_tenant_user(
        self, api_client: APIClient, tenant_user: TenantUserRelation, user_without_tenant: User
    ):
        url = reverse('tenants:me', kwargs={"tenant_id": tenant_user.tenant.pk})
        api_client.force_authenticate(user_without_tenant)
        response = api_client.get(url)

        expected_response = {"detail": 'You do not have permission to perform this action.'}
        assert response.status_code == 403
        assert response.data == expected_response


@pytest.mark.django_db
class TestTenantDetailsApi:
    def test_should_retrieve_tenant_details(self, api_client: APIClient, tenant_user: TenantUserRelation):
        url = reverse('tenant_details', kwargs={"subdomain": tenant_user.tenant.subdomain})
        response = api_client.get(url)

        expected_response = {
            "id": tenant_user.tenant.pk,
            "name": tenant_user.tenant.name,
            "subdomain": tenant_user.tenant.subdomain,
        }
        assert response.status_code == 200
        assert response.data == expected_response

    def test_should_be_not_found_for_non_existing_domain(self, api_client: APIClient):
        url = reverse('tenant_details', kwargs={"subdomain": "this-domain-does-not-exist@example.com"})
        response = api_client.get(url)

        expected_response = {"detail": 'Not found.'}
        assert response.status_code == 404
        assert response.data == expected_response


@pytest.mark.django_db
class TestTenantInvitationDetailsApi:
    def test_should_retrieve_new_user_tenant_invitation(self, api_client: APIClient):
        invitation = TenantInvitationFactory()
        url = reverse(
            'tenants:invitation_details', kwargs={"tenant_id": invitation.tenant.pk, "token": invitation.token}
        )
        response = api_client.get(url)

        expected_response = {
            "status": TenantInvitation.InvitationStatus.NEW_USER,
        }
        assert response.status_code == 200
        assert response.data == expected_response

    def test_should_retrieve_existing_user_tenant_invitation(
        self, api_client: APIClient, tenant_user: TenantUserRelation
    ):
        invitation = TenantInvitationFactory(email=tenant_user.user.email)
        url = reverse(
            'tenants:invitation_details', kwargs={"tenant_id": invitation.tenant.pk, "token": invitation.token}
        )
        response = api_client.get(url)

        expected_response = {
            "status": TenantInvitation.InvitationStatus.EXISTING_USER,
        }
        assert response.status_code == 200
        assert response.data == expected_response

    def test_should_retrieve_expired_tenant_invitation(self, api_client: APIClient):
        invitation = TenantInvitationFactory(expires_at=timezone.now() - timedelta(days=1))
        url = reverse(
            'tenants:invitation_details', kwargs={"tenant_id": invitation.tenant.pk, "token": invitation.token}
        )
        response = api_client.get(url)

        expected_response = {
            "status": 'EXPIRED',
        }
        assert response.status_code == 200
        assert response.data == expected_response

    def test_should_retrieve_inactive_tenant_invitation(self, api_client: APIClient):
        invitation = TenantInvitationFactory(is_active=False)
        url = reverse(
            'tenants:invitation_details', kwargs={"tenant_id": invitation.tenant.pk, "token": invitation.token}
        )
        response = api_client.get(url)

        expected_response = {
            "status": 'EXPIRED',
        }
        assert response.status_code == 200
        assert response.data == expected_response

    def test_should_be_not_found_for_non_existing_token(self, api_client: APIClient):
        tenant = TenantFactory()
        url = reverse('tenants:invitation_details', kwargs={"tenant_id": tenant.pk, "token": "non-existing-token"})
        response = api_client.get(url)

        expected_response = {"detail": 'Not found.'}
        assert response.status_code == 404
        assert response.data == expected_response

    def test_should_be_not_found_for_non_existing_tenant(self, api_client: APIClient):
        invitation = TenantInvitationFactory()
        url = reverse('tenants:invitation_details', kwargs={"tenant_id": 999, "token": invitation.token})
        response = api_client.get(url)

        expected_response = {"detail": 'Not found.'}
        assert response.status_code == 404
        assert response.data == expected_response


@pytest.mark.django_db
class TestTenantInvitationAcceptApi:
    def test_should_accept_invitation_for_existing_user(self, api_client: APIClient, tenant_user: TenantUserRelation):
        invitation = TenantInvitationFactory(email=tenant_user.user.email)

        url = reverse(
            'tenants:invitation_accept', kwargs={"tenant_id": invitation.tenant.pk, "token": invitation.token}
        )
        response = api_client.post(url)

        assert response.status_code == 204
        assert response.data is None

        tenant_user_exists = TenantUserRelation.objects.filter(user=tenant_user.user, tenant=invitation.tenant).exists()
        assert tenant_user_exists is True

    def test_should_be_not_found_for_non_existing_token(self, api_client: APIClient):
        tenant = TenantFactory()
        url = reverse('tenants:invitation_accept', kwargs={"tenant_id": tenant.pk, "token": "non-existing-token"})
        response = api_client.post(url)

        expected_response = {"detail": 'Not found.'}
        assert response.status_code == 404
        assert response.data == expected_response

    def test_should_be_not_found_for_non_existing_tenant(self, api_client: APIClient):
        invitation = TenantInvitationFactory()
        url = reverse('tenants:invitation_accept', kwargs={"tenant_id": 999, "token": invitation.token})
        response = api_client.post(url)

        expected_response = {"detail": 'Not found.'}
        assert response.status_code == 404
        assert response.data == expected_response


@pytest.mark.django_db
class TestTenantInvitationSignupApi:
    @pytest.fixture
    def signup_data(self) -> dict[str, str]:
        return {
            "first_name": "John",
            "last_name": "Doe",
            "company_name": "Company Name",
            "password": "test-password",
            "phone_number": "+48606606606",
        }

    @pytest.mark.parametrize(
        'signup_data',
        (
            {
                "first_name": "John",
                "last_name": "Doe",
                "company_name": "Company Name",
                "password": "test-password",
            },
            {
                "first_name": "John",
                "last_name": "Doe",
                "company_name": "Company Name",
                "password": "test-password",
                "phone_number": "",
            },
        ),
    )
    def test_should_signup_user(self, api_client: APIClient, signup_data: dict[str, str]):
        PrivacyPolicyFactory()
        invitation = TenantInvitationFactory()
        url = reverse(
            'tenants:invitation_signup', kwargs={"tenant_id": invitation.tenant.pk, "token": invitation.token}
        )
        response = api_client.post(url, signup_data)

        expected_response = {
            "id": mock.ANY,
            "first_name": signup_data["first_name"],
            "last_name": signup_data["last_name"],
            "role": UserRole.ADMIN.value,
            "privacy_policy_consent_valid": True,
            'email': invitation.email,
            'profile_image': '',
            "phone_number": None,
            "company": None,
            "company_name": signup_data["company_name"],
        }

        assert response.status_code == 201
        assert response.data == expected_response

    def test_should_be_not_found_for_non_existing_token(self, api_client: APIClient, signup_data: dict[str, str]):
        tenant = TenantFactory()
        url = reverse('tenants:invitation_signup', kwargs={"tenant_id": tenant.pk, "token": "non-existing-token"})
        response = api_client.post(url, signup_data)

        expected_response = {"detail": 'Not found.'}
        assert response.status_code == 404
        assert response.data == expected_response

    def test_should_be_not_found_for_non_existing_tenant(self, api_client: APIClient, signup_data: dict[str, str]):
        invitation = TenantInvitationFactory()
        url = reverse('tenants:invitation_signup', kwargs={"tenant_id": 999, "token": invitation.token})
        response = api_client.post(url, signup_data)

        expected_response = {"detail": 'Not found.'}
        assert response.status_code == 404
        assert response.data == expected_response


@pytest.mark.django_db
class TestPasswordChangeApi:
    def test_change_password(self, api_client: APIClient, tenant_user: TenantUserRelation):
        user = tenant_user.user
        url = reverse('tenants:password_change', kwargs={"tenant_id": tenant_user.tenant.pk})
        api_client.force_authenticate(user=user)
        data = {"new_password": "new password", "old_password": USER_PASSWORD}
        response = api_client.post(url, data=data)

        assert response.status_code == 204
        assert response.data is None

    def test_must_be_authenticated_to_change_password(self, api_client: APIClient):
        tenant = TenantFactory()
        url = reverse('tenants:password_change', kwargs={"tenant_id": tenant.pk})
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_must_be_tenant_member_to_change_password(self, api_client: APIClient):
        user = UserFactory()
        tenant = TenantFactory()
        url = reverse('tenants:password_change', kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user)
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestPasswordResetApi:
    def test_reset_password(self, api_client: APIClient, tenant_user: TenantUserRelation):
        url = reverse('tenants:password_reset', kwargs=dict(tenant_id=tenant_user.tenant_id))

        response = api_client.post(url, data=dict(email=tenant_user.user.email))

        assert response.status_code == 204
        assert response.data is None


@pytest.mark.django_db
class TestPasswordResetValidateTokenApi:
    def test_invalid_token(self, api_client: APIClient):
        tenant = TenantFactory()
        url = reverse(
            'tenants:password_reset_validate_token', kwargs=dict(tenant_id=tenant.pk, uid='uid', token='token')
        )

        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data is None

    def test_valid_token(self, api_client: APIClient, tenant_user: TenantUserRelation):
        uid, token = generate_password_reset_token(tenant_user.user)
        url = reverse(
            'tenants:password_reset_validate_token', kwargs=dict(tenant_id=tenant_user.tenant_id, uid=uid, token=token)
        )
        response = api_client.get(url)

        assert response.status_code == 204
        assert response.data is None


@pytest.mark.django_db
class TestPasswordResetPasswordChangeApi:
    def test_change_password(self, api_client: APIClient, tenant_user: TenantUserRelation):
        uid, token = generate_password_reset_token(tenant_user.user)
        url = reverse(
            'tenants:password_reset_change_password', kwargs=dict(tenant_id=tenant_user.tenant_id, uid=uid, token=token)
        )
        response = api_client.post(url, data=dict(password='new password'))

        assert response.status_code == 204
        assert response.data is None


@pytest.mark.django_db
class TestMeUpdateApi:
    def test_should_update_profile(self, api_client: APIClient):
        tenant_user = TenantUserRelationFactory()
        api_client.force_authenticate(tenant_user.user)

        url = reverse('tenants:me_update', kwargs=dict(tenant_id=tenant_user.tenant_id))

        data = {
            "first_name": "New First Name",
            "last_name": "New Last Name",
            "phone_number": "+48606606606",
            "company_name": "New Company Name",
        }
        response = api_client.post(url, data=data)

        assert response.status_code == 200
        assert response.data == {
            "first_name": "New First Name",
            "last_name": "New Last Name",
            "company_name": "New Company Name",
            "company": {"id": tenant_user.user.company.pk, "name": tenant_user.user.company.name},
            "id": tenant_user.user.pk,
            'email': tenant_user.user.email,
            "role": tenant_user.user.role,
            "privacy_policy_consent_valid": False,
            'profile_image': '',
            "phone_number": {'number': '606606606', 'country_code': 48},
        }

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        api_client = APIClient()
        url = reverse('tenants:me_update', kwargs=dict(tenant_id=tenant.pk))

        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}


@pytest.mark.django_db
class TestMeAvatarUpdateApi:
    @pytest.fixture
    def image_file(self) -> SimpleUploadedFile:
        content = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        return SimpleUploadedFile('image-file.gif', content, content_type='image/gif')

    def test_should_update_avatar(self, api_client: APIClient, image_file: SimpleUploadedFile):
        tenant_user = TenantUserRelationFactory()
        api_client.force_authenticate(tenant_user.user)

        url = reverse('tenants:avatar_update', kwargs=dict(tenant_id=tenant_user.tenant_id))
        response = api_client.post(url, data={'profile_image': image_file}, format='multipart')

        tenant_user.refresh_from_db()
        assert response.status_code == 200
        assert response.data == MeSerializer(tenant_user.user).data
        assert len(response.data['profile_image']) > 0

    def test_should_be_forbidden_for_anonymous_user(self, image_file: SimpleUploadedFile):
        tenant = TenantFactory()
        api_client = APIClient()

        url = reverse('tenants:avatar_update', kwargs=dict(tenant_id=tenant.id))
        response = api_client.post(url, data={'profile_image': image_file}, format='multipart')

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}


@pytest.mark.django_db
class TestMeAvatarDeleteApi:
    def test_should_delete_avatar(self, api_client: APIClient):
        tenant_user = TenantUserRelationFactory()
        api_client.force_authenticate(tenant_user.user)

        url = reverse('tenants:avatar_delete', kwargs=dict(tenant_id=tenant_user.tenant_id))
        response = api_client.delete(url)

        tenant_user.refresh_from_db()
        assert response.status_code == 204

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        api_client = APIClient()

        url = reverse('tenants:avatar_delete', kwargs=dict(tenant_id=tenant.id))
        response = api_client.delete(url)

        expected_response = {"detail": 'Authentication credentials were not provided.'}
        assert response.status_code == 403
        assert response.data == expected_response
