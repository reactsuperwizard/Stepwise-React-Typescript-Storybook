from django.urls import path

from apps.tenants import apis

app_name = 'tenants'

urlpatterns = [
    path('login/', apis.LoginApi.as_view(), name='login'),
    path('logout/', apis.LogoutApi.as_view(), name='logout'),
    path('me/', apis.MeApi.as_view(), name='me'),
    path('me/update/', apis.MeUpdateApi.as_view(), name='me_update'),
    path('me/locked/', apis.LockedApi.as_view(), name='locked'),
    path('me/password/', apis.PasswordChangeApi.as_view(), name='password_change'),
    path('me/avatar/', apis.MeAvatarUpdateApi.as_view(), name='avatar_update'),
    path('me/avatar/delete/', apis.MeAvatarDeleteApi.as_view(), name='avatar_delete'),
    path('invitations/<str:token>/', apis.TenantInvitationDetailsApi.as_view(), name='invitation_details'),
    path('invitations/<str:token>/accept/', apis.TenantInvitationAcceptApi.as_view(), name='invitation_accept'),
    path('invitations/<str:token>/signup/', apis.TenantInvitationSignupApi.as_view(), name='invitation_signup'),
    path('password-reset/', apis.PasswordResetApi.as_view(), name='password_reset'),
    path(
        'password-reset/<str:uid>/<str:token>/',
        apis.PasswordResetValidateTokenApi.as_view(),
        name='password_reset_validate_token',
    ),
    path(
        'password-reset/<str:uid>/<str:token>/change/',
        apis.PasswordResetPasswordChangeApi.as_view(),
        name='password_reset_change_password',
    ),
]
