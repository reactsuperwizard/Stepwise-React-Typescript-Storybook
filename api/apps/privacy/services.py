import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.forms import ValidationError
from django.template.loader import render_to_string
from django.utils import timezone

from apps.core.dashboard import DashboardRoutes
from apps.core.reverse import dashboard_reverse
from apps.privacy.models import DeleteAccountRequest, PrivacyPolicy, PrivacyPolicyConsent
from apps.tenants.models import TenantUserRelation, User

logger = logging.getLogger(__name__)


def send_privacy_changed_email(policy: PrivacyPolicy) -> None:
    logger.info(f"Sending privacy policy changed email for PrivacyPolicy(pk={policy.pk}).")

    if not policy.is_active:
        raise ValueError("Unable to send privacy email changed. Inactive policy.")

    recipient_qs = list(
        TenantUserRelation.objects.filter(user__is_active=True, tenant__is_active=True)
        .select_related('user', 'tenant')
        .distinct('user')
    )

    subject = render_to_string('emails/privacy_policy_changed_subject.txt')

    for recipient in recipient_qs:
        body = render_to_string(
            'emails/privacy_policy_changed_body.html',
            {"url": dashboard_reverse(tenant=recipient.tenant, page=DashboardRoutes.index)},
        )

        send_mail(
            subject=subject,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.user.email],
            html_message=body,
        )

    logger.info(f"Privacy policy changed emails for PrivacyPolicy(pk={policy.pk}) has been sent.")


def send_delete_account_request_email(delete_account_request: DeleteAccountRequest) -> None:
    logger.info(f"Sending delete account request email to User(pk={delete_account_request.user.pk}.")

    subject = render_to_string('emails/delete_account_request_subject.txt')
    body = render_to_string(
        'emails/delete_account_request_body.html', {"delete_account_request": delete_account_request}
    )

    send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[delete_account_request.user.email],
        html_message=body,
    )

    logger.info(f"Delete account request email sent to User(pk={delete_account_request.user.pk}.")


def send_account_deleted_email(user: User, email: str) -> None:
    logger.info(f"Sending account deleted email to User(pk={user.pk}.")

    subject = render_to_string('emails/account_deleted_subject.txt')
    body = render_to_string('emails/account_deleted_body.html')

    send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=body,
    )

    logger.info(f"Account deleted email sent to User(pk={user.pk}.")


def is_user_consent_valid(user: User) -> bool:
    return PrivacyPolicyConsent.objects.filter(
        user=user,
        policy__is_active=True,
        revoked_at__isnull=True,
    ).exists()


def accept_active_policy(user: User) -> PrivacyPolicyConsent:
    logger.info(f"User(pk={user.pk}) accepts the latest Privacy Policy.")
    policy = PrivacyPolicy.objects.get(is_active=True)

    logger.info(f"User(pk={user.pk}) accepts PrivacyPolicy(pk={policy.pk}).")
    is_consent_already_given = PrivacyPolicyConsent.objects.filter(
        user=user, policy=policy, revoked_at__isnull=True
    ).exists()

    if is_consent_already_given:
        logger.info(f"Unable to accept Privacy Policy(pk={policy.pk}) by User(pk={user.pk}). Consent already given.")
        raise ValidationError("Unable to accept Privacy Policy. Consent already given.")

    logger.info(f"Revoking outdated consents for User(pk={user.pk}) and Policy(pk={policy.pk})")
    PrivacyPolicyConsent.objects.filter(user=user, revoked_at__isnull=True).update(
        revoked_at=timezone.now(), revoked_reason=PrivacyPolicyConsent.RevokedReason.UPDATED
    )

    logger.info(f"Creating consent for User(pk={user.pk}) for Policy(pk={policy.pk}).")
    consent = PrivacyPolicyConsent.objects.create(user=user, policy=policy)
    return consent


@transaction.atomic
def activate_policy(policy: PrivacyPolicy) -> PrivacyPolicy:
    logger.info(f"Activating PrivacyPolicy(pk={policy.pk}).")

    if policy.is_active:
        logger.info(f"Unable to activate PrivacyPolicy(pk={policy.pk}). Policy already active.")
        raise ValueError("Policy is already active.")

    active_policy = PrivacyPolicy.objects.get(is_active=True)
    active_policy.is_active = False
    active_policy.save()

    policy.is_active = True
    policy.save()

    send_privacy_changed_email(policy)

    logger.info(f"PrivacyPolicy(pk={policy.pk}) has been activated.")
    return policy


@transaction.atomic
def create_delete_account_request(user: User) -> DeleteAccountRequest:
    delete_account_request = DeleteAccountRequest.objects.create(
        user=user, is_active=True, execute_at=timezone.now() + timedelta(days=settings.REMOVE_ACCOUNTS_AFTER_DAYS)
    )
    user.is_active = False
    user.save()

    send_delete_account_request_email(delete_account_request)
    return delete_account_request


@transaction.atomic
def delete_account(delete_account_request: DeleteAccountRequest) -> DeleteAccountRequest:
    if not delete_account_request.is_active:
        logger.info(f"Unable to execute DeleteAccountRequest(pk={delete_account_request.pk}). Request inactive.")
        raise ValueError('Delete account request is not active.')

    user = delete_account_request.user
    user_email = user.email

    user.is_active = False
    user.first_name = ''
    user.last_name = ''
    user.phone_number = ''  # type: ignore
    user.email = f"deleted-user-{user.pk}@example.com"
    user.username = user.email
    user.save()

    delete_account_request.is_active = False
    delete_account_request.save()

    TenantUserRelation.objects.filter(user=user).delete()

    send_account_deleted_email(user, user_email)
    return delete_account_request
