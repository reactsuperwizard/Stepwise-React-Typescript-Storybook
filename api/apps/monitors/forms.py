from django import forms
from django_ace import AceWidget

from apps.monitors.models import MonitorFunction
from apps.monitors.services import MonitorFunctionTestResult, compile_monitor_function, run_monitor_function_test

INITIAL_MONITOR_FUNCTION = """
def monitor(tags):
    return 0
""".strip()

TEST_MONITOR_FUNCTION_ACTION = "_testmonitorfunction"


class MonitorFunctionWidget(AceWidget):
    def render(self, *args, **kwargs):
        html: str = super().render(*args, **kwargs)
        html += f'<input type="submit" value="Test function" name={TEST_MONITOR_FUNCTION_ACTION} formtarget="_blank">'
        return html


class MonitorFunctionTestForm(forms.ModelForm):
    monitor_function_source = forms.CharField(
        widget=MonitorFunctionWidget(mode='python'),
        initial=INITIAL_MONITOR_FUNCTION,
        help_text="Function should be called 'monitor', take a single 'tags' argument and return a value",
    )
    monitor_function_test_result: MonitorFunctionTestResult | None

    def __init__(self, *args, **kwargs):
        self.monitor_function_test_result = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        vessel = cleaned_data.get("vessel")
        monitor_function_source = cleaned_data.get("monitor_function_source")

        if monitor_function_source and vessel:
            callable_monitor_function = compile_monitor_function(monitor_function_source=monitor_function_source)
            self.monitor_function_test_result = run_monitor_function_test(
                callable_monitor_function=callable_monitor_function,
                vessel=vessel,
                hours=3,
            )

        return cleaned_data

    class Meta:
        model = MonitorFunction
        fields = (
            'vessel',
            'monitor_function_source',
        )


class MonitorFunctionForm(MonitorFunctionTestForm):
    class Meta:
        model = MonitorFunction
        fields = '__all__'
