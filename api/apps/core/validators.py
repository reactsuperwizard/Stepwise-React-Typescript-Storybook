import datetime

from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from django.utils.deconstruct import deconstructible


@deconstructible
class MinDateValidator:
    def __init__(self, min_date: datetime.date):
        self.min_date = min_date

    def __call__(self, value: datetime.date) -> None:
        if value < self.min_date:
            raise ValidationError(f'Date must be greater than {self.min_date}')


@deconstructible
class MaxDateValidator:
    def __init__(self, max_date: datetime.date):
        self.max_date = max_date

    def __call__(self, value: datetime.date) -> None:
        if self.max_date < value:
            raise ValidationError(f'Date must be earlier than {self.max_date}')


@deconstructible
class GreaterThanValidator(BaseValidator):
    message = "Ensure this value is greater than %(limit_value)s."
    code = "greater_than"

    def compare(self, a, b):
        return a <= b
