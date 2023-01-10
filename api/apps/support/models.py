from ckeditor.fields import RichTextField
from django.db import models
from ordered_model.models import OrderedModel

from apps.core.models import TimestampedModel


class Faq(OrderedModel, TimestampedModel):
    title = models.CharField(max_length=255, unique=True, help_text="Title of the FAQ section")
    draft = models.BooleanField(help_text="Draft FAQs will not be visible in the app")

    def __str__(self) -> str:
        return self.title


class FaqElement(OrderedModel, TimestampedModel):
    question = models.CharField(max_length=255)
    answer = RichTextField()
    draft = models.BooleanField(help_text="Draft questions will not be visible in the app")
    faq = models.ForeignKey('support.Faq', on_delete=models.PROTECT, related_name='elements')
    order_with_respect_to = 'faq'

    class Meta:
        constraints = [models.UniqueConstraint(fields=["faq", "question"], name="unique_faq_element")]

    def __str__(self) -> str:
        return self.question
