from django import forms

from apps.wells.models import WellPlannerCompleteStep, WellPlannerPlannedStep


class BaseWellPlannerStepForm(forms.Form):
    def clean(self):
        from apps.wells.services.api import validate_well_planner_step_data

        cleaned_data = super().clean()

        validate_well_planner_step_data(
            well_planner=cleaned_data.get('well_planner'),
            phase=cleaned_data.get('phase'),
            mode=cleaned_data.get('mode'),
            season=cleaned_data.get('season'),
        )

        return cleaned_data


class WellPlannerPlannedStepForm(BaseWellPlannerStepForm, forms.ModelForm):
    class Meta:
        model = WellPlannerPlannedStep
        fields = '__all__'


class WellPlannerCompleteStepForm(BaseWellPlannerStepForm, forms.ModelForm):
    class Meta:
        model = WellPlannerCompleteStep
        fields = '__all__'
