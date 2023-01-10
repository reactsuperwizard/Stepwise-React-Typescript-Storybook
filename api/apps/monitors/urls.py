from django.urls import path

from apps.monitors import apis

app_name = 'monitors'

urlpatterns = [
    path('monitors/', apis.MonitorListApi.as_view(), name='monitor_list'),
    path('monitors/<int:monitor_id>/', apis.MonitorDetailsApi.as_view(), name='monitor_details'),
    path(
        'monitors/<int:monitor_id>/elements/<int:element_id>/',
        apis.MonitorElementDatasetListApi.as_view(),
        name='monitor_element_dataset_list',
    ),
]
