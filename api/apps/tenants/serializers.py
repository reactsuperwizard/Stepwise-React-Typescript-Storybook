from drf_recaptcha.fields import ReCaptchaV2Field
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core.api.fields import FileURLField
from apps.privacy.services import is_user_consent_valid
from apps.tenants.models import Tenant, TenantInvitation, User


def LoginSerializerFactory(locked: bool) -> type[serializers.Serializer]:
    class LoginSerializer(serializers.Serializer):
        email = serializers.EmailField()
        password = serializers.CharField()
        remember_me = serializers.BooleanField()
        recaptcha = ReCaptchaV2Field(required=locked, allow_blank=not locked)

    return LoginSerializer


class MeSerializer(serializers.ModelSerializer):
    class PhoneNumberSerializer(serializers.Serializer):
        number = serializers.CharField(source="national_number")
        country_code = serializers.IntegerField()

    class CompanySerializer(serializers.ModelSerializer):
        class Meta:
            model = Tenant
            fields = ('id', 'name')

    phone_number = serializers.SerializerMethodField()
    email = serializers.EmailField()
    profile_image = FileURLField()
    privacy_policy_consent_valid = serializers.SerializerMethodField()
    company = CompanySerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'role',
            'company',
            'company_name',
            'phone_number',
            'email',
            'profile_image',
            'privacy_policy_consent_valid',
        )

    def get_privacy_policy_consent_valid(self, obj: User) -> bool:
        return is_user_consent_valid(obj)

    @extend_schema_field(PhoneNumberSerializer(allow_null=True))
    def get_phone_number(self, obj: User) -> dict | None:
        return self.PhoneNumberSerializer(obj.phone_number).data if obj.phone_number else None


class LockedSerializer(serializers.Serializer):
    locked = serializers.BooleanField()


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ('id', 'name', 'subdomain')


class TenantInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantInvitation
        fields = ('status',)


class TenantInvitationSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField()

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'company_name', 'password', 'phone_number')
        extra_kwargs = {
            'company_name': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }


class PasswordChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField()
    old_password = serializers.CharField()


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.CharField()


class PasswordResetTokenSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()


class PasswordResetChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField()


class MeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone_number",
            "company_name",
        )


class MeAvatarUpdateSerializer(serializers.Serializer):
    profile_image = serializers.ImageField(required=True)

    class Meta:
        model = User
        fields = ("profile_image",)
