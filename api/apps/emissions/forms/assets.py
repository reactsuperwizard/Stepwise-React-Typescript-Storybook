from django import forms

from apps.emissions.models import Asset, Baseline, EmissionManagementPlan, EmissionReductionInitiative


class AssetAdminForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = "__all__"

    def clean_name(self):
        if not self.instance:
            if Asset.objects.live().filter(name=self.cleaned_data["name"]).exists():
                raise forms.ValidationError("Asset name is already used.")
        else:
            if Asset.objects.live().filter(name=self.cleaned_data["name"]).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Asset name is already used.")

        return self.cleaned_data["name"]


class EmissionReductionInitiativeAdminForm(forms.ModelForm):
    class Meta:
        model = EmissionReductionInitiative
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")

        if emission_management_plan := cleaned_data.get("emission_management_plan"):
            asset_emission_reduction_initiatives = EmissionReductionInitiative.objects.live().filter(
                emission_management_plan__baseline__asset=emission_management_plan.baseline.asset,
                name=name,
            )
            if not self.instance:
                if asset_emission_reduction_initiatives.exists():
                    raise forms.ValidationError({"name": "Emission reduction initiative name is already used."})
            else:
                if asset_emission_reduction_initiatives.exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError({"name": "Emission reduction initiative name is already used."})

        return cleaned_data


class BaselineAdminForm(forms.ModelForm):
    class Meta:
        model = Baseline
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        asset = cleaned_data.get("asset")

        if asset and name:
            if not self.instance:
                if Baseline.objects.live().filter(asset=asset, name=name).exists():
                    raise forms.ValidationError("Baseline name is already used.")
            else:
                if Baseline.objects.live().filter(asset=asset, name=name).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError("Baseline name is already used.")

        return cleaned_data


class EmissionManagementPlanAdminForm(forms.ModelForm):
    class Meta:
        model = EmissionManagementPlan
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        baseline = cleaned_data.get("baseline")

        if baseline and name:
            asset = baseline.asset
            if not self.instance:
                if EmissionManagementPlan.objects.live().filter(baseline__asset=asset, name=name).exists():
                    raise forms.ValidationError("EMP name is already used.")
            else:
                if (
                    EmissionManagementPlan.objects.live()
                    .filter(baseline__asset=asset, name=name)
                    .exclude(pk=self.instance.pk)
                    .exists()
                ):
                    raise forms.ValidationError("EMP name is already used.")

        return cleaned_data
