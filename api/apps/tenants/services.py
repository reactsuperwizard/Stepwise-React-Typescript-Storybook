import logging
import secrets
from datetime import timedelta
from typing import cast

from django.conf import settings
from django.contrib.auth import authenticate, login, password_validation, update_session_auth_hash, user_login_failed
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from apps.core.dashboard import DashboardRoutes
from apps.core.reverse import dashboard_reverse
from apps.privacy.services import accept_active_policy
from apps.tenants.models import Tenant, TenantInvitation, TenantUserRelation, User, UserRole

logger = logging.getLogger(__name__)


def send_tenant_is_ready_email(tenant: Tenant) -> int:
    if not tenant.is_active:
        raise ValueError(f'Unable to send the email for tenant "{tenant.name}". Inactive tenant.')

    recipient_list = list(
        TenantUserRelation.objects.filter(
            tenant=tenant, user__is_active=True, role=TenantUserRelation.TenantUserRole.ADMIN
        ).values_list('user__email', flat=True)
    )

    subject = render_to_string('emails/tenant_is_ready_subject.txt')
    body = render_to_string(
        'emails/tenant_is_ready_body.html', {"url": dashboard_reverse(tenant=tenant, page=DashboardRoutes.index)}
    )
    return send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        html_message=body,
    )


def send_invitation_email(invitation: TenantInvitation) -> int:
    logger.info(f'Sending invitation email for Invitation(pk={invitation.pk}).')

    if not invitation.is_valid:
        logger.info(f'Unable to send invitation email for Invitation(pk={invitation.pk}). Invitation invalid.')
        raise ValueError(
            f'Unable to send the invitation email for email:"{invitation.email} and tenant:"{invitation.tenant.name}". Invitation invalid.'
        )

    if not invitation.tenant.is_active:
        logger.info(f'Unable to send invitation email for Invitation(pk={invitation.pk}). Inactive tenant.')
        raise ValueError(f'Unable to send the email for tenant "{invitation.tenant.name}". Inactive tenant.')

    recipient_list = [invitation.email]
    subject = render_to_string('emails/tenant_invitation_subject.txt', {"invitation": invitation})

    body = render_to_string(
        'emails/tenant_invitation_body.html',
        {
            "invitation": invitation,
            "url": dashboard_reverse(tenant=invitation.tenant, page=DashboardRoutes.invitation, token=invitation.token),
        },
    )

    result = send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        html_message=body,
    )
    logger.info(f'Invitation email sent for Invitation(pk={invitation.pk}).')
    return result


def expire_invitation(invitation: TenantInvitation) -> TenantInvitation:
    logger.info(f'Expiring Invitation(pk={invitation.pk}).')
    invitation.is_active = False
    invitation.save()
    logger.info(f'Invitation(pk={invitation.pk}) has been expired.')
    return invitation


def create_tenant_user(
    *, tenant: Tenant, user: User, role: TenantUserRelation.TenantUserRole = TenantUserRelation.TenantUserRole.MEMBER
) -> TenantUserRelation:
    logger.info(f'Creating tenant user for User(pk={user.pk}) and Tenant(pk={tenant.pk}).')
    tenant_user_exists = tenant.members.filter(pk=user.pk).exists()

    if tenant_user_exists:
        logger.info(
            f'Unable to create tenant user for User(pk={user.pk}) and Tenant(pk={tenant.pk}). User already belongs to tenant.'
        )
        raise ValidationError("User already belongs to tenant.")

    tenant_user = TenantUserRelation.objects.create(
        tenant=tenant,
        user=user,
        role=role,
    )

    logger.info(f'Tenant user for User(pk={user.pk}) and Tenant(pk={tenant.pk}) has been created.')
    return tenant_user


@transaction.atomic
def invite_tenant_user(tenant: Tenant, email: str) -> TenantInvitation:
    logger.info(f'Inviting user to Tenant(pk={tenant.pk}).')

    if not tenant.is_active:
        logger.info(f'Unable to invite user to Tenant(pk={tenant.pk}). Inactive tenant.')
        raise ValidationError('Unable to invite user. Inactive tenant.')

    tenant_user_exists = TenantUserRelation.objects.filter(
        user__email=email,
        tenant=tenant,
    ).exists()

    if tenant_user_exists:
        logger.info(f'Unable to invite user to Tenant(pk={tenant.pk}). User already belongs to the tenant.')
        raise ValidationError("User already belongs to tenant.")

    TenantInvitation.objects.filter(
        tenant=tenant,
        email=email,
        is_active=True,
    ).update(is_active=False)

    user = User.objects.filter(email=email).first()  # type: ignore

    if user and not user.is_active:
        logger.info(f'Unable to invite user to Tenant(pk={tenant.pk}). User is inactive.')
        raise ValidationError("Unable to invite user. Inactive user.")

    expires_at = timezone.now() + timedelta(days=settings.SIGNUP_TOKEN_EXPIRE_AFTER_DAYS)
    invitation = TenantInvitation.objects.create(
        token=secrets.token_urlsafe(64), tenant=tenant, email=email, is_active=True, expires_at=expires_at
    )

    send_invitation_email(invitation)
    return invitation


@transaction.atomic
def accept_tenant_invitation(invitation: TenantInvitation) -> TenantUserRelation:
    logger.info(f'Accepting Invitation(pk={invitation.pk}).')

    if not invitation.is_valid:
        logger.info(f'Unable to accept Invitation(pk={invitation.pk}). Invitation is no longer valid.')
        raise ValidationError("Invitation is no longer valid.")

    user = User.objects.filter(email=invitation.email).first()  # type: ignore

    if user is None:
        logger.info(f'Unable to accept Invitation(pk={invitation.pk}). User does not exist.')
        raise ValidationError("Unable to accept invitation. User does not exist.")

    if not user.is_active:
        logger.info(f'Unable to accept Invitation(pk={invitation.pk}). User is not active.')
        raise ValidationError("Unable to accept invitation. User is not active.")

    logger.info(f'Creating tenant user for Invitation(pk={invitation.pk}).')

    tenant_user = create_tenant_user(tenant=invitation.tenant, user=user)
    expire_invitation(invitation)

    logger.info(f'Invitation(pk={invitation.pk}) has been accepted.')
    return tenant_user


@transaction.atomic
def signup_user(
    *,
    invitation: TenantInvitation,
    first_name: str,
    last_name: str,
    company_name: str,
    password: str,
    phone_number: str | None = None,
) -> TenantUserRelation:
    logger.info(f'User is signing up with an Invitation(pk={invitation.pk}).')
    user_exists = User.objects.filter(email=invitation.email).exists()  # type: ignore

    if user_exists:
        logger.info(
            f'Unable to sign up user with an Invitation(pk={invitation.pk}). User with this email already exists'
        )
        raise ValidationError("User with this email already exists.")

    if not invitation.is_valid:
        logger.info(f'Unable to sign up user with an Invitation(pk={invitation.pk}). Invitation is no longer valid.')
        raise ValidationError("Invitation is no longer valid.")

    try:
        password_validation.validate_password(password)
    except ValidationError as e:
        logger.info(
            f'Unable to sign up user with an Invitation(pk={invitation.pk}). Password doesn\'t meet all validator requirements.'
        )
        raise ValidationError({"password": e})

    user = User.objects.create(  # type: ignore
        username=invitation.email,
        email=invitation.email,
        first_name=first_name,
        last_name=last_name,
        company_name=company_name,
        phone_number=phone_number or "",
        role=UserRole.ADMIN,  # TODO: introduce other roles
    )
    user.set_password(password)
    user.save()

    logger.info(f'Creating tenant user for Invitation(pk={invitation.pk}).')

    tenant_user = create_tenant_user(tenant=invitation.tenant, user=user)
    expire_invitation(invitation)

    logger.info(f'Accepting active Privacy Policy for User(pk={user.pk}).')
    accept_active_policy(user)

    logger.info(f'User signed up with an Invitation(pk={invitation.pk}).')
    return tenant_user


def login_tenant_user(
    *,
    request: HttpRequest,
    tenant_id: int,
    email: str,
    password: str,
    remember_me: bool,
    recaptcha: str | None = None,
) -> TenantUserRelation:
    logger.info(f'User is logging into Tenant(pk={tenant_id}).')

    user = authenticate(request, email=email, password=password)

    if not user:
        logger.info('Invalid credentials or inactive user.')
        raise ValidationError('Invalid credentials.')

    tenant_user = TenantUserRelation.objects.filter(user=cast(User, user), tenant_id=tenant_id).first()

    if not tenant_user:
        user_login_failed.send(
            sender=User,
            request=request,
            credentials={
                'email': email,
            },
        )
        logger.info(f'User(pk={user}) is not member of Tenant(pk={tenant_id}).')
        raise ValidationError('Invalid credentials.')

    if not tenant_user.tenant.is_active:
        logger.info(f'Unable to login User(pk={tenant_user.user.pk}) to Tenant(pk={tenant_id}). Tenant is not active.')
        user_login_failed.send(
            sender=User,
            request=request,
            credentials={
                'email': email,
            },
        )
        raise ValidationError("Unable to login. Inactive tenant.")

    login(request, user)

    if not remember_me:
        # expire when the user’s web browser is closed
        request.session.set_expiry(0)
    return tenant_user


def change_user_password(*, request: HttpRequest, user: User, old_password: str, new_password: str) -> None:
    logger.info(f'User(pk={user.pk}) is changing password')
    if not user.check_password(old_password):
        logger.info('Unable to change password. Invalid old password')
        raise ValidationError({"old_password": "Old password is not correct"})

    try:
        password_validation.validate_password(new_password, user)
    except ValidationError as e:
        logger.info('Unable to change password. New password doesn\'t meet all validator requirements')
        raise ValidationError({"new_password": e})

    user.set_password(new_password)
    user.save()
    update_session_auth_hash(request, user)

    logger.info('Password has been changed')


def generate_password_reset_token(user: User) -> tuple[str, str]:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    return uid, token


def send_password_reset_email(tenant: Tenant, user: User) -> int:
    logger.info(f'Sending password reset email for User(pk={user.pk}) in Tenant(pk={tenant.pk})')
    uid, token = generate_password_reset_token(user)

    subject = render_to_string('emails/password_reset_subject.txt')
    body = render_to_string(
        'emails/password_reset_body.html',
        {'url': dashboard_reverse(tenant=tenant, page=DashboardRoutes.changeForgottenPassword, uid=uid, token=token)},
    )
    result = send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=body,
    )
    logger.info('Email has been sent')
    return result


def reset_password(tenant: Tenant, email: str) -> int:
    logger.info(f'Resetting password for email {email} in Tenant(pk={tenant.pk})')
    tenant_users = TenantUserRelation.objects.filter(
        tenant=tenant, user__email=email, user__is_active=True
    ).select_related('user')

    users = [tenant_user.user for tenant_user in tenant_users]

    for user in users:
        send_password_reset_email(tenant=tenant, user=user)

    logger.info(f'Sent password reset email to {len(users)} users')

    return len(users)


def decode_password_reset_token(uid: str, token: str) -> User:
    logger.info('Decoding password reset token')
    try:
        uid = force_str(urlsafe_base64_decode(uid))
        user: User = User.objects.get(pk=uid)  # type: ignore
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        logger.info("Invalid token. Invalid user id or user doesn't exist")
        raise ValidationError("Invalid token")

    logger.info(f'Decoded token for User(pk={user.pk})')

    is_token_valid = default_token_generator.check_token(user, token)
    if not is_token_valid:
        logger.info("Invalid token. Token has expired or has been tampered with.")
        raise ValidationError("Expired token")

    logger.info('Token is valid')
    return user


def change_password_reset_password(uid: str, token: str, password: str) -> None:
    user = decode_password_reset_token(uid=uid, token=token)

    logger.info(f'User(pk={user.pk}) is changing password after password reset')

    try:
        password_validation.validate_password(password, user)
    except ValidationError as e:
        logger.info('Unable to change password. New password doesn\'t meet all validator requirements')
        raise ValidationError({"password": e})

    user.set_password(password)
    user.save()

    logger.info('New password has been changed')


def update_user_profile(
    *, user: User, first_name: str, last_name: str, company_name: str, phone_number: str | None = None
) -> User:
    logger.info(f"Upadting User(pk={user.pk}) profile information.")
    user.first_name = first_name
    user.last_name = last_name
    user.company_name = company_name
    user.phone_number = phone_number or ""  # type: ignore
    user.save()

    logger.info(f"Updated User(pk={user.pk}) profile information.")
    return user


def update_user_avatar(user: User, profile_image: UploadedFile | None) -> User:
    logger.info(f"Updating User(pk={user.pk}) profile image")
    user.profile_image = profile_image
    user.save()

    logger.info(f"Updated User(pk={user.pk}) profile image")
    return user
