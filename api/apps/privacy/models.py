from ckeditor.fields import RichTextField
from django.db import models

from apps.core.models import TimestampedModel


class PrivacyPolicy(TimestampedModel):
    title = models.CharField(max_length=255)
    text = RichTextField()
    is_active = models.BooleanField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'Privacy policies'
        constraints = [
            models.UniqueConstraint(
                fields=['is_active'], condition=models.Q(is_active=True), name='unique_active_privacy_policy'
            ),
        ]


class PrivacyPolicyConsent(TimestampedModel):
    class RevokedReason(models.TextChoices):
        UPDATED = 'UPDATED', 'User accepted an updated policy'
        REVOKED = 'REVOKED', 'User revoked his consent'

    user = models.ForeignKey('tenants.User', on_delete=models.PROTECT, related_name='consents')
    policy = models.ForeignKey('privacy.PrivacyPolicy', on_delete=models.PROTECT)
    revoked_reason = models.CharField(max_length=16, choices=RevokedReason.choices, blank=True)
    revoked_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} consent to {self.policy.title}"


class DeleteAccountRequest(TimestampedModel):
    user = models.ForeignKey('tenants.User', on_delete=models.PROTECT)
    is_active = models.BooleanField(help_text="True if the request was not yet executed")
    execute_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user'], condition=models.Q(is_active=True), name='unique_delete_account_request'
            ),
        ]

    def __str__(self):
        return f"DeleteAccountRequest: {self.user}"
