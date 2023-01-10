from django.db.models import Count, Prefetch, Q
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.support.models import Faq, FaqElement
from apps.support.serializers import FaqSerializer
from apps.tenants.mixins import TenantMixin
from apps.tenants.permissions import IsTenantUser


class FaqApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={200: FaqSerializer(many=True)})
    def get(self, *args: str, **kwargs: str) -> Response:
        faqs = (
            Faq.objects.filter(draft=False)
            .annotate(non_draft_element_count=Count('elements', filter=Q(elements__draft=False)))
            .filter(non_draft_element_count__gt=0)
            .prefetch_related(
                Prefetch(
                    'elements',
                    queryset=FaqElement.objects.filter(draft=False),
                )
            )
        ).order_by('order')

        response_data = FaqSerializer(faqs, many=True).data
        return Response(response_data, status=200)
