from django.urls import path

from apps.projects import apis

app_name = 'projects'

urlpatterns = [
    path('projects/', apis.ProjectListApi.as_view(), name='project_list'),
    path('projects/create/', apis.CreateProjectApi.as_view(), name='create_project'),
    path('projects/<int:project_id>/', apis.ProjectDetailsApi.as_view(), name='project_details'),
    path('projects/<int:project_id>/update/', apis.UpdateProjectApi.as_view(), name='update_project'),
    path('projects/<int:project_id>/delete/', apis.DeleteProjectApi.as_view(), name='delete_project'),
    path(
        'projects/<int:project_id>/rigs/',
        apis.ProjectRigListApi.as_view(),
        name='project_rig_list',
    ),
    # emp
    path(
        'projects/<int:project_id>/rigs/<str:rig_type>/<int:rig_id>/emp/',
        apis.ProjectRigEmpDetailsApi.as_view(),
        name='project_rig_emp_details',
    ),
    path(
        'projects/<int:project_id>/rigs/<str:rig_type>/<int:rig_id>/emp/create/',
        apis.CreateProjectRigEmpApi.as_view(),
        name='create_project_rig_emp',
    ),
    path(
        'projects/<int:project_id>/rigs/<str:rig_type>/<int:rig_id>/emp/update/',
        apis.UpdateProjectRigEmpApi.as_view(),
        name='update_project_rig_emp',
    ),
    path(
        'projects/<int:project_id>/rigs/<str:rig_type>/<int:rig_id>/emp/delete/',
        apis.DeleteProjectRigEmpApi.as_view(),
        name='delete_project_rig_emp',
    ),
    # wells
    path(
        'projects/<int:project_id>/wells/',
        apis.ProjectWellListApi.as_view(),
        name='project_well_list',
    ),
    # plans
    path(
        'projects/<int:project_id>/plans/',
        apis.ProjectPlanListApi.as_view(),
        name='project_plan_list',
    ),
    path(
        'projects/<int:project_id>/plans/<int:plan_id>/',
        apis.ProjectPlanDetailsApi.as_view(),
        name='project_plan_details',
    ),
    path(
        'projects/<int:project_id>/plans/create/',
        apis.CreateProjectPlanApi.as_view(),
        name='create_project_plan',
    ),
    path(
        'projects/<int:project_id>/plans/<int:plan_id>/delete/',
        apis.DeleteProjectPlanApi.as_view(),
        name='delete_project_plan',
    ),
    path(
        'projects/<int:project_id>/plans/<int:plan_id>/update/',
        apis.UpdateProjectPlanApi.as_view(),
        name='update_project_plan',
    ),
]

# common
urlpatterns += [
    path('elements/', apis.ElementListApi.as_view(), name='element_list'),
]
