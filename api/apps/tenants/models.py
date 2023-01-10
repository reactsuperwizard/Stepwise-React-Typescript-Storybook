from __future__ import annotations

from typing import cast

import pgcrypto
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.fields import EncryptedPhoneNumberField
from apps.core.models import TenantAwareModel
from apps.tenants.validators import domain_name_validator


class UserManager(BaseUserManager):
    def _create_user(self, email: str, password: str, **extra_fields: str | bool) -> User:
        """
        Create and save a user with the given username, email, and password.
        """
        email = self.normalize_email(email)
        username = User.normalize_username(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return cast(User, user)

    def create_user(self, email: str, password: str, **extra_fields: str | bool) -> User:
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields: str | bool) -> User:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


def get_user_profile_image_path(_: User, filename: str) -> str:
    return f"users/profile_images/{filename}"


class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Admin'
    ASSET_MANAGER = 'ASSET_MANAGER', 'Asset Manager'
    OPERATOR = 'OPERATOR', 'Operator'


class User(AbstractUser):
    username = pgcrypto.EncryptedCharField(
        error_messages={'unique': 'A user with that username already exists.'},
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
        max_length=150,
        unique=True,
        validators=[UnicodeUsernameValidator()],
        verbose_name='username',
    )
    first_name = pgcrypto.EncryptedCharField(blank=True, max_length=150, verbose_name='first name')
    last_name = pgcrypto.EncryptedCharField(blank=True, max_length=150, verbose_name='last name')
    email = pgcrypto.EncryptedEmailField(unique=True)

    profile_image = models.ImageField(upload_to=get_user_profile_image_path, null=True, blank=True)
    company = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, null=True, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    phone_number = EncryptedPhoneNumberField(blank=True)
    role = models.CharField(max_length=24, choices=UserRole.choices)

    objects = UserManager()  # type: ignore

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(role__in=[UserRole.ASSET_MANAGER.value, UserRole.OPERATOR.value], company__isnull=False)
                | Q(role=UserRole.ADMIN.value),
                name="optional_admin_company",
            ),
        ]


class TenantUserRelation(TenantAwareModel):
    class TenantUserRole(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        MEMBER = 'MEMBER', 'Member'

    user = models.ForeignKey("tenants.User", on_delete=models.PROTECT)
    role = models.CharField(max_length=10, choices=TenantUserRole.choices, help_text='User\'s role within a tenant')

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "user"], name="unique_tenant_user_relation")]

    def __str__(self) -> str:
        return f'Tenant User Relation: {self.pk}'


class Tenant(models.Model):
    name = models.CharField(max_length=100)
    subdomain = models.CharField(max_length=50, validators=[domain_name_validator()], unique=True)
    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this tenant should be treated as active. Unselect this instead of deleting tenants.',
    )
    members = models.ManyToManyField("tenants.User", through=TenantUserRelation, blank=True)

    def __str__(self) -> str:
        return f'Tenant: {self.name}'


class TenantInvitation(TenantAwareModel):
    class InvitationStatus(models.TextChoices):
        NEW_USER = 'NEW_USER', 'New User'
        EXISTING_USER = 'EXISTING_USER', 'Existing User'
        EXPIRED = 'EXPIRED', 'Expired'

    email = models.EmailField(max_length=255)
    token = models.CharField(max_length=86)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "token"], name="unique_tenant_invitation")]

    def __str__(self):
        return f"Tenant Invitation: {self.pk}"

    @property
    def is_valid(self):
        return self.is_active and not self.is_expired

    @property
    def is_expired(self):
        return self.expires_at < timezone.now()

    @property
    def status(self) -> TenantInvitation.InvitationStatus:
        if not self.is_valid:
            return self.InvitationStatus.EXPIRED

        user_exists = User.objects.filter(email=self.email).exists()  # type: ignore
        return self.InvitationStatus.EXISTING_USER if user_exists else self.InvitationStatus.NEW_USER
