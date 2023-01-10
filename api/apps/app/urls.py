"""app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from typing import cast

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.core.debug import sentry_debug
from apps.tenants.apis import TenantDetailsApi
from apps.tenants.forms import AdminCaptchaAuthenticationForm

admin.site.login_form = AdminCaptchaAuthenticationForm  # type: ignore
admin.site.login_template = 'admin/login.html'

urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    path('api/tenants/subdomains/<str:subdomain>/', TenantDetailsApi.as_view(), name='tenant_details'),
    path('api/tenants/<int:tenant_id>/', include('apps.tenants.urls')),
    path('api/tenants/<int:tenant_id>/', include('apps.projects.urls')),
    path('api/tenants/<int:tenant_id>/', include('apps.rigs.urls')),
    path('api/tenants/<int:tenant_id>/', include('apps.wells.urls')),
    path('api/tenants/<int:tenant_id>/', include('apps.monitors.urls')),
    path('api/tenants/<int:tenant_id>/', include('apps.support.urls')),
    path('api/tenants/<int:tenant_id>/', include('apps.studies.urls')),
    path('api/tenants/<int:tenant_id>/', include('apps.emps.urls')),
    path('api/tenants/<int:tenant_id>/', include('apps.search.urls')),
    path('api/tenants/<int:tenant_id>/', include('apps.notifications.urls')),
    path('api/tenants/<int:tenant_id>/', include('apps.emissions.urls')),
    path('api/', include('apps.privacy.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        path('api/docs/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('sentry_debug/', sentry_debug),
    ]
    if not settings.USE_S3:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
        urlpatterns += static(cast(str, settings.STATIC_URL), document_root=settings.STATIC_ROOT)
