from axes.handlers.proxy import AxesProxyHandler
from captcha.fields import ReCaptchaField
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from apps.tenants.mixins import UserFormValidationMixin


class AdminCaptchaAuthenticationForm(AdminAuthenticationForm):
    captcha = ReCaptchaField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        username = self.data.get('username')
        locked = AxesProxyHandler().is_locked(request=self.request, credentials=dict(email=username))
        if not locked:
            del self.fields['captcha']


class UserAdminForm(UserFormValidationMixin, UserChangeForm):
    pass


class UserAdminCreationForm(UserFormValidationMixin, UserCreationForm):
    pass
