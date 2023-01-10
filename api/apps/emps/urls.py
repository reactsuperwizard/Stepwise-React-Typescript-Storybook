from django.urls import path

from apps.emps import apis

app_name = 'emps'

urlpatterns = [
    path('emps/', apis.ConceptEMPElementListApi.as_view(), name='concept_emp_element_list'),
]
