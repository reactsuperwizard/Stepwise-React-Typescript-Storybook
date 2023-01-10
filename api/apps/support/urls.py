from django.urls import path

from apps.support import apis

app_name = 'support'

urlpatterns = [
    path('support/faq/', apis.FaqApi.as_view(), name='faq'),
]
