from django.urls import path

from apps.search import apis

app_name = 'search'

urlpatterns = [
    path(
        'search/',
        apis.SearchApi.as_view(),
        name='search',
    ),
]
