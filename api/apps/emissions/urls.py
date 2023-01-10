from django.urls import path

from apps.emissions import apis

app_name = 'emissions'

urlpatterns = [
    path(
        'emissions/assets/reference-material/',
        apis.AssetReferenceMaterialApi.as_view(),
        name='asset_reference_material',
    ),
    path('emissions/assets/', apis.AssetListApi.as_view(), name='asset_list'),
    path('emissions/assets/complete/', apis.CompleteAssetListApi.as_view(), name='complete_asset_list'),
    path('emissions/assets/create/', apis.CreateAssetApi.as_view(), name='create_asset'),
    path('emissions/assets/<int:asset_id>/update/', apis.UpdateAssetApi.as_view(), name='update_asset'),
    path('emissions/assets/<int:asset_id>/', apis.AssetDetailsApi.as_view(), name='asset_details'),
    path('emissions/assets/<int:asset_id>/duplicate/', apis.DuplicateAssetApi.as_view(), name='duplicate_asset'),
    path('emissions/assets/<int:asset_id>/delete/', apis.DeleteAssetApi.as_view(), name='delete_asset'),
    path(
        'emissions/assets/<int:asset_id>/baselines/<int:baseline_id>/',
        apis.AssetBaselineDetailsApi.as_view(),
        name='asset_baseline_details',
    ),
    path(
        'emissions/assets/<int:asset_id>/baselines/create/',
        apis.CreateAssetBaselineApi.as_view(),
        name='create_asset_baseline',
    ),
    path(
        'emissions/assets/<int:asset_id>/baselines/<int:baseline_id>/update/',
        apis.UpdateAssetBaselineApi.as_view(),
        name='update_asset_baseline',
    ),
    path(
        'emissions/assets/<int:asset_id>/baselines/<int:baseline_id>/activate/',
        apis.ActivateBaselineApi.as_view(),
        name='activate_baseline',
    ),
    path(
        'emissions/assets/<int:asset_id>/baselines/<int:baseline_id>/delete/',
        apis.DeleteBaselineApi.as_view(),
        name='delete_baseline',
    ),
    path(
        'emissions/assets/<int:asset_id>/baselines/<int:baseline_id>/duplicate/',
        apis.DuplicateBaselineApi.as_view(),
        name='duplicate_baseline',
    ),
    path(
        'emissions/assets/<int:asset_id>/baselines/<int:baseline_id>/emission-management-plans/<int:emission_management_plan_id>/emission-reduction-initiatives/<int:emission_reduction_initiative_id>/',
        apis.EmissionReductionInitiativeDetailsApi.as_view(),
        name='emission_reduction_initiative_details',
    ),
    path(
        'emissions/assets/<int:asset_id>/baselines/<int:baseline_id>/emission-management-plans/<int:emission_management_plan_id>/emission-reduction-initiatives/create/',
        apis.CreateEmissionReductionInitiativeApi.as_view(),
        name='create_emission_reduction_initiative',
    ),
    path(
        'emissions/assets/<int:asset_id>/baselines/<int:baseline_id>/emission-management-plans/<int:emission_management_plan_id>/emission-reduction-initiatives/<int:emission_reduction_initiative_id>/update/',
        apis.UpdateEmissionReductionInitiativeApi.as_view(),
        name='update_emission_reduction_initiative',
    ),
    path(
        'emissions/assets/<int:asset_id>/baselines/<int:baseline_id>/emission-management-plans/<int:emission_management_plan_id>/emission-reduction-initiatives/<int:emission_reduction_initiative_id>/delete/',
        apis.DeleteEmissionReductionInitiativeApi.as_view(),
        name='delete_emission_reduction_initiative',
    ),
    path(
        'emissions/assets/<int:asset_id>/baselines/<int:baseline_id>/emission-management-plans/create/',
        apis.CreateEmissionManagementPlanApi.as_view(),
        name='create_emission_management_plan',
    ),
    path(
        'emissions/assets/<int:asset_id>/baselines/<int:baseline_id>/emission-management-plans/<int:emission_management_plan_id>/',
        apis.EmissionManagementPlanDetailsApi.as_view(),
        name='emission_management_plan_details',
    ),
    path(
        'emissions/assets/<int:asset_id>/baselines/<int:baseline_id>/emission-management-plans/<int:emission_management_plan_id>/update/',
        apis.UpdateEmissionManagementPlanApi.as_view(),
        name='update_emission_management_plan',
    ),
    path(
        'emissions/assets/<int:asset_id>/baselines/<int:baseline_id>/emission-management-plans/<int:emission_management_plan_id>/delete/',
        apis.DeleteEmissionManagementPlanApi.as_view(),
        name='delete_emission_management_plan',
    ),
    path(
        'emissions/assets/<int:asset_id>/baselines/<int:baseline_id>/emission-management-plans/<int:emission_management_plan_id>/activate/',
        apis.ActivateEmissionManagementPlanApi.as_view(),
        name='activate_emission_management_plan',
    ),
    path(
        'emissions/assets/<int:asset_id>/baselines/<int:baseline_id>/emission-management-plans/<int:emission_management_plan_id>/duplicate/',
        apis.DuplicateEmissionManagementPlanApi.as_view(),
        name='duplicate_emission_management_plan',
    ),
    path(
        'emissions/assets/<int:asset_id>/phases/',
        apis.AssetPhaseListApi.as_view(),
        name='asset_phase_list',
    ),
    path(
        'emissions/assets/<int:asset_id>/phases/create/',
        apis.CreateAssetCustomPhaseApi.as_view(),
        name='create_asset_custom_phase',
    ),
    path(
        'emissions/assets/<int:asset_id>/phases/<int:custom_phase_id>/update/',
        apis.UpdateAssetCustomPhaseApi.as_view(),
        name='update_asset_custom_phase',
    ),
    path(
        'emissions/assets/<int:asset_id>/modes/',
        apis.AssetModeListApi.as_view(),
        name='asset_mode_list',
    ),
    path(
        'emissions/assets/<int:asset_id>/modes/create/',
        apis.CreateAssetCustomModeApi.as_view(),
        name='create_asset_custom_mode',
    ),
    path(
        'emissions/assets/<int:asset_id>/modes/<int:custom_mode_id>/update/',
        apis.UpdateAssetCustomModeApi.as_view(),
        name='update_asset_custom_mode',
    ),
    path(
        'emissions/vessel-types/',
        apis.VesselTypeListApi.as_view(),
        name='vessel_type_list',
    ),
    path(
        'emissions/vessel-types/all/',
        apis.AllVesselTypeListApi.as_view(),
        name='all_vessel_type_list',
    ),
    path(
        'emissions/vessel-types/create/',
        apis.CreateVesselTypeApi.as_view(),
        name='create_vessel_type',
    ),
    path(
        'emissions/vessel-types/<int:vessel_type_id>/update/',
        apis.UpdateVesselTypeApi.as_view(),
        name='update_vessel_type',
    ),
    path(
        'emissions/vessel-types/<int:vessel_type_id>/delete/',
        apis.DeleteVesselTypeApi.as_view(),
        name='delete_vessel_type',
    ),
    path(
        'emissions/helicopter-types/',
        apis.HelicopterTypeListApi.as_view(),
        name="helicopter_type_list",
    ),
    path(
        'emissions/helicopter-types/create/',
        apis.CreateHelicopterTypeApi.as_view(),
        name="create_helicopter_type",
    ),
    path(
        'emissions/helicopter-types/<int:helicopter_type_id>/update/',
        apis.UpdateHelicopterTypeApi.as_view(),
        name="update_helicopter_type",
    ),
    path(
        'emissions/helicopter-types/all/',
        apis.AllHelicopterTypeListApi.as_view(),
        name='all_helicopter_type_list',
    ),
    path(
        'emissions/material-types/',
        apis.MaterialTypeListApi.as_view(),
        name='material_type_list',
    ),
    path(
        'emissions/material-types/all/',
        apis.AllMaterialTypeListApi.as_view(),
        name='all_material_type_list',
    ),
    path(
        'emissions/material-types/create/',
        apis.CreateMaterialTypeApi.as_view(),
        name='create_material_type',
    ),
    path(
        'emissions/material-types/<int:material_type_id>/update/',
        apis.UpdateMaterialTypeApi.as_view(),
        name='update_material_type',
    ),
    path(
        'emissions/material-types/<int:material_type_id>/delete/',
        apis.DeleteMaterialTypeApi.as_view(),
        name='delete_material_type',
    ),
    path(
        'emissions/helicopter-types/<int:helicopter_type_id>/delete/',
        apis.DeleteHelicopterTypeApi.as_view(),
        name='delete_helicopter_type',
    ),
    path(
        'emissions/assets/<int:asset_id>/baselines/<int:baseline_id>/phases/',
        apis.BaselinePhaseListApi.as_view(),
        name='baseline_phase_list',
    ),
    path(
        'emissions/assets/<int:asset_id>/baselines/<int:baseline_id>/modes/',
        apis.BaselineModeListApi.as_view(),
        name='baseline_mode_list',
    ),
]

urlpatterns += [
    path(
        'emissions/wells/<int:well_planner_id>/delete/',
        apis.DeleteWellApi.as_view(),
        name='delete_well',
    ),
    path(
        'emissions/wells/<int:well_planner_id>/duplicate/',
        apis.DuplicateWellApi.as_view(),
        name='duplicate_well',
    ),
    path('emissions/wells/create/', apis.CreateWellApi.as_view(), name='create_well'),
    path('emissions/wells/<int:well_planner_id>/update/', apis.UpdateWellApi.as_view(), name='update_well'),
    path('emissions/well-names/', apis.WellNameListApi.as_view(), name='well_name_list'),
    path('emissions/well-names/create/', apis.CreateWellNameApi.as_view(), name='create_well_name'),
    path(
        'emissions/wells/<int:well_planner_id>/planned/vessel-uses/create/',
        apis.CreateWellPlannedVesselUseApi.as_view(),
        name="create_well_planned_vessel_use",
    ),
    path(
        'emissions/wells/<int:well_planner_id>/planned/vessel-uses/<int:planned_vessel_use_id>/update/',
        apis.UpdateWellPlannedVesselUseApi.as_view(),
        name="update_well_planned_vessel_use",
    ),
    path(
        'emissions/wells/<int:well_planner_id>/planned/vessel-uses/<int:planned_vessel_use_id>/delete/',
        apis.DeleteWellPlannedVesselUseApi.as_view(),
        name="delete_well_planned_vessel_use",
    ),
    path(
        'emissions/wells/<int:well_planner_id>/planned/helicopter-uses/create/',
        apis.CreateWellPlannedHelicopterUseApi.as_view(),
        name="create_well_planned_helicopter_use",
    ),
    path(
        'emissions/wells/<int:well_planner_id>/planned/helicopter-uses/<int:planned_helicopter_use_id>/update/',
        apis.UpdateWellPlannedHelicopterUseApi.as_view(),
        name="update_well_planned_helicopter_use",
    ),
    path(
        'emissions/wells/<int:well_planner_id>/planned/helicopter-uses/<int:planned_helicopter_use_id>/delete/',
        apis.DeleteWellPlannedHelicopterUseApi.as_view(),
        name="delete_well_planned_helicopter_use",
    ),
    path(
        'emissions/wells/<int:well_planner_id>/planned/start-date/update/',
        apis.UpdateWellPlannedStartDateApi.as_view(),
        name='update_well_planned_start_date',
    ),
    path(
        'emissions/wells/<int:well_planner_id>/planned/emissions/target/co2/',
        apis.WellTargetCO2EmissionsApi.as_view(),
        name='well_target_co2_emissions',
    ),
    path(
        'emissions/wells/<int:well_planner_id>/planned/emissions/target/reductions/co2/',
        apis.WellTargetCO2EmissionReductionsApi.as_view(),
        name='well_target_co2_emission_reductions',
    ),
    path(
        'emissions/wells/<int:well_planner_id>/planned/emissions/baseline/co2/',
        apis.WellBaselineCO2EmissionsApi.as_view(),
        name='well_baseline_co2_emissions',
    ),
    path(
        'emissions/wells/<int:well_planner_id>/complete/vessel-uses/create/',
        apis.CreateWellCompleteVesselUseApi.as_view(),
        name="create_well_complete_vessel_use",
    ),
    path(
        'emissions/wells/<int:well_planner_id>/complete/vessel-uses/<int:complete_vessel_use_id>/update/',
        apis.UpdateWellCompleteVesselUseApi.as_view(),
        name="update_well_complete_vessel_use",
    ),
    path(
        'emissions/wells/<int:well_planner_id>/complete/vessel-uses/<int:complete_vessel_use_id>/delete/',
        apis.DeleteWellCompleteVesselUseApi.as_view(),
        name="delete_well_complete_vessel_use",
    ),
    path(
        'emissions/wells/<int:well_planner_id>/complete/helicopter-uses/create/',
        apis.CreateWellCompleteHelicopterUseApi.as_view(),
        name="create_well_complete_helicopter_use",
    ),
    path(
        'emissions/wells/<int:well_planner_id>/complete/helicopter-uses/<int:complete_helicopter_use_id>/update/',
        apis.UpdateWellCompleteHelicopterUseApi.as_view(),
        name="update_well_complete_helicopter_use",
    ),
    path(
        'emissions/wells/<int:well_planner_id>/complete/helicopter-uses/<int:complete_helicopter_use_id>/delete/',
        apis.DeleteWellCompleteHelicopterUseApi.as_view(),
        name="delete_well_complete_helicopter_use",
    ),
]
