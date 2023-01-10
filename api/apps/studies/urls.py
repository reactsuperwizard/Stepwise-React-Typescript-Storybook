from django.urls import path

from apps.studies import apis

app_name = 'studies'

urlpatterns = [
    path('studies/metrics/', apis.StudyMetricListApi.as_view(), name='study_metric_list'),
    path('studies/<int:project_id>/elements/', apis.StudyElementListApi.as_view(), name='study_element_list'),
    path(
        'studies/<int:project_id>/elements/<int:element_id>/',
        apis.StudyElementDetailsApi.as_view(),
        name='study_element_details',
    ),
    path(
        'studies/<int:project_id>/elements/create/', apis.CreateStudyElementApi.as_view(), name='create_study_element'
    ),
    path(
        'studies/<int:project_id>/elements/<int:element_id>/delete/',
        apis.DeleteStudyElementApi.as_view(),
        name='delete_study_element',
    ),
    path(
        'studies/<int:project_id>/elements/<int:element_id>/update/',
        apis.UpdateStudyElementApi.as_view(),
        name='update_study_element',
    ),
    path(
        'studies/<int:project_id>/elements/swap/',
        apis.SwapStudyElementsApi.as_view(),
        name='swap_study_elements',
    ),
]
