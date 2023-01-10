from django.urls import path

from apps.rigs import apis

app_name = 'rigs'

urlpatterns = [
    # custom
    path('rigs/custom/', apis.CustomRigListApi.as_view(), name='custom_rig_list'),
    # custom jackup
    path('rigs/custom/jackup/', apis.CustomJackupRigListApi.as_view(), name='custom_jackup_rig_list'),
    path('rigs/custom/jackup/create/', apis.CreateCustomJackupRigApi.as_view(), name='create_custom_jackup_rig'),
    path(
        'rigs/custom/jackup/<int:rig_id>/', apis.CustomJackupRigDetailsApi.as_view(), name='custom_jackup_rig_details'
    ),
    path(
        'rigs/custom/jackup/<int:rig_id>/update/',
        apis.UpdateCustomJackupRigApi.as_view(),
        name='update_custom_jackup_rig',
    ),
    path(
        'rigs/custom/jackup/<int:rig_id>/delete/',
        apis.DeleteCustomJackupRigApi.as_view(),
        name='delete_custom_jackup_rig',
    ),
    # custom semi
    path('rigs/custom/semi/', apis.CustomSemiRigListApi.as_view(), name='custom_semi_rig_list'),
    path('rigs/custom/semi/create/', apis.CreateCustomSemiRigApi.as_view(), name='create_custom_semi_rig'),
    path('rigs/custom/semi/<int:rig_id>/', apis.CustomSemiRigDetailsApi.as_view(), name='custom_semi_rig_details'),
    path('rigs/custom/semi/<int:rig_id>/update/', apis.UpdateCustomSemiRigApi.as_view(), name='update_custom_semi_rig'),
    path('rigs/custom/semi/<int:rig_id>/delete/', apis.DeleteCustomSemiRigApi.as_view(), name='delete_custom_semi_rig'),
    # custom drillship
    path('rigs/custom/drillship/', apis.CustomDrillshipListApi.as_view(), name='custom_drillship_list'),
    path('rigs/custom/drillship/create/', apis.CreateCustomDrillshipApi.as_view(), name='create_custom_drillship'),
    path(
        'rigs/custom/drillship/<int:rig_id>/update/',
        apis.UpdateCustomDrillshipApi.as_view(),
        name='update_custom_drillship',
    ),
    path(
        'rigs/custom/drillship/<int:rig_id>/', apis.CustomDrillshipDetailsApi.as_view(), name='custom_drillship_details'
    ),
    path(
        'rigs/custom/drillship/<int:rig_id>/delete/',
        apis.DeleteCustomDrillshipApi.as_view(),
        name='delete_custom_drillship',
    ),
    # concept jackup
    path('rigs/concept/jackup/', apis.ConceptJackupRigListApi.as_view(), name='concept_jackup_rig_list'),
    path(
        'rigs/concept/jackup/<int:rig_id>/',
        apis.ConceptJackupRigDetailsApi.as_view(),
        name='concept_jackup_rig_details',
    ),
    # concept semi
    path('rigs/concept/semi/', apis.ConceptSemiRigListApi.as_view(), name='concept_semi_rig_list'),
    path('rigs/concept/semi/<int:rig_id>/', apis.ConceptSemiRigDetailsApi.as_view(), name='concept_semi_rig_details'),
    # concept drillship
    path('rigs/concept/drillship/', apis.ConceptDrillshipListApi.as_view(), name='concept_drillship_list'),
    path(
        'rigs/concept/drillship/<int:rig_id>/',
        apis.ConceptDrillshipDetailsApi.as_view(),
        name='concept_drillship_details',
    ),
]
