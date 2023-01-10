from typing import cast

from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from apps.search.serializers import SearchQuerySerializer, SearchResultSerializer
from apps.search.services import search
from apps.tenants.mixins import TenantMixin
from apps.tenants.models import User
from apps.tenants.permissions import IsTenantUser


class SearchApi(TenantMixin, GenericAPIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        parameters=[SearchQuerySerializer], responses={200: SearchResultSerializer(many=True)}, summary="Search"
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        query_serializer = SearchQuerySerializer(data=request.GET)
        query_serializer.is_valid(raise_exception=True)

        search_results = search(
            user=cast(User, self.request.user), tenant=self.tenant, **query_serializer.validated_data
        )
        page = self.paginate_queryset(search_results)  # noqa
        response_serializer = SearchResultSerializer(page, many=True)
        return self.get_paginated_response(response_serializer.data)
