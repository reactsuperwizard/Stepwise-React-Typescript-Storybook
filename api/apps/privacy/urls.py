from django.urls import path

from apps.privacy import apis

app_name = 'privacy'

urlpatterns = [
    path('policies/<int:policy_id>/', apis.PrivacyPolicyDetailsApi.as_view(), name='policy_details'),
    path('policies/latest/', apis.PrivacyPolicyLatestApi.as_view(), name='policy_latest'),
    path(
        'tenants/<int:tenant_id>/policies/latest/accept/',
        apis.PrivacyPolicyLatestAcceptApi.as_view(),
        name='policy_latest_accept',
    ),
    path('tenants/<int:tenant_id>/consents/', apis.PrivacyPolicyConsentListApi.as_view(), name='consent_list'),
    path('tenants/<int:tenant_id>/delete-account/', apis.DeleteAccountApi.as_view(), name='delete_account'),
    path(
        'tenants/<int:tenant_id>/consents/latest/', apis.PrivacyPolicyConsentLatestApi.as_view(), name='consent_latest'
    ),
]
