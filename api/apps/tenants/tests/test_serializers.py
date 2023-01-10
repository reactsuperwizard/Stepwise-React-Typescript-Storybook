import pytest

from apps.tenants.serializers import TenantInvitationSignupSerializer


@pytest.mark.django_db
class TestTenantInvitationSignupSerializer:
    def test_should_not_be_valid_for_invalid_phone_number(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "company_name": "Company Name",
            "password": "test-password",
            "phone_number": "+48000000000",
        }
        serializer = TenantInvitationSignupSerializer(data=data)

        assert serializer.is_valid() is False
        assert serializer.errors['phone_number'] is not None
        assert str(serializer.errors['phone_number'][0]) == 'The phone number entered is not valid.'
