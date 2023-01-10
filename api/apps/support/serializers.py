from rest_framework import serializers

from apps.support.models import Faq, FaqElement


class FaqSerializer(serializers.ModelSerializer):
    class FaqElementSerializer(serializers.ModelSerializer):
        class Meta:
            model = FaqElement
            fields = ('id', 'question', 'answer')

    elements = FaqElementSerializer(many=True)

    class Meta:
        model = Faq
        fields = ('id', 'title', 'elements')
