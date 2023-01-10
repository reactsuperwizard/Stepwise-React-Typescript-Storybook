from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.emps.models import ConceptEMPElement
from apps.emps.serializers import ConceptEMPElementSerializer
from apps.tenants.mixins import TenantMixin
from apps.tenants.permissions import IsTenantUser


class ConceptEMPElementListApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={200: ConceptEMPElementSerializer(many=True)}, summary="Concept emp element list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        concept_emp_elements = ConceptEMPElement.objects.all()

        response_data = ConceptEMPElementSerializer(concept_emp_elements, many=True).data
        return Response(response_data, status=200)
