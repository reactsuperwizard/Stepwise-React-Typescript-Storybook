from rest_framework import serializers

from apps.privacy.models import PrivacyPolicy, PrivacyPolicyConsent


class PrivacyPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = ('id', 'title', 'text')


class PrivacyPolicyConsentSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='policy.title')
    text = serializers.CharField(source='policy.text')

    class Meta:
        model = PrivacyPolicyConsent
        fields = ('id', 'title', 'text', 'revoked_at', 'created_at')
