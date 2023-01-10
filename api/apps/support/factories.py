import factory.fuzzy

from apps.support.models import Faq, FaqElement


class FaqFactory(factory.django.DjangoModelFactory):
    title = factory.Sequence(lambda n: f"faq-{n}")
    draft = False

    class Meta:
        model = Faq


class FaqElementFactory(factory.django.DjangoModelFactory):
    question = factory.Faker('sentence')
    answer = factory.Faker('paragraph')
    faq = factory.SubFactory(FaqFactory)
    draft = False

    class Meta:
        model = FaqElement
