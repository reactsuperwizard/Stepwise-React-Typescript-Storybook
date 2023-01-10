from functools import cached_property
from typing import cast

from django.db import models
from django.db.models import Case, F, OuterRef, QuerySet, Subquery, Sum, When, Window
from django.db.models.functions import Coalesce
from django.utils import timezone
from django_generate_series.models import generate_series
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework_csv.renderers import CSVRenderer

from apps.monitors.choices import MonitorElementDatasetType
from apps.monitors.models import Monitor, MonitorElement, MonitorElementPhase, MonitorFunctionValue, MonitorQuerySet
from apps.monitors.serializers import (
    MonitorDetailsSerializer,
    MonitorElementDatasetListParamsSerializer,
    MonitorElementDatasetSerializer,
    MonitorListSerializer,
)
from apps.tenants.mixins import TenantMixin
from apps.tenants.permissions import IsTenantUser


class MonitorListApi(TenantMixin, ListAPIView):
    permission_classes = [IsTenantUser]
    serializer_class = MonitorListSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'name']

    def get_queryset(self) -> QuerySet['Monitor']:
        return Monitor.objects.filter(tenant=self.tenant, draft=False).order_by('-created_at')

    @extend_schema(summary="Monitor list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class MonitorDetailsApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={200: MonitorDetailsSerializer}, summary="Monitor details")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        monitor = get_object_or_404(
            cast(MonitorQuerySet, Monitor.objects.filter(tenant=self.tenant, draft=False)).with_public_elements(),
            pk=self.kwargs['monitor_id'],
        )
        serializer = MonitorDetailsSerializer(instance=monitor)
        return Response(serializer.data, status=200)


class MonitorCSVRenderer(CSVRenderer):
    header = ['date', 'baseline', 'target', 'current']


class MonitorElementDatasetListApi(TenantMixin, APIView):
    renderer_classes = (MonitorCSVRenderer, *api_settings.DEFAULT_RENDERER_CLASSES)  # type: ignore
    permission_classes = [IsTenantUser]

    @cached_property
    def monitor_element(self) -> MonitorElement:
        monitor_element = get_object_or_404(
            MonitorElement.objects.filter(
                monitor__tenant=self.tenant,
                monitor__draft=False,
                monitor__pk=self.kwargs['monitor_id'],
                draft=False,
            ).select_related('monitor', 'monitor_function'),
            pk=self.kwargs['element_id'],
        )
        return monitor_element

    def get_monitor_element_queryset(self) -> models.QuerySet:
        element_values = (
            MonitorFunctionValue.objects.filter(
                date__date=OuterRef('date'), monitor_function=self.monitor_element.monitor_function
            )
            .values('date__date')
            .annotate(total_value=Coalesce(Sum('value'), 0, output_field=models.FloatField()))
        )
        element_phases = MonitorElementPhase.objects.filter(
            monitor_element=self.monitor_element,
            start_date__lte=OuterRef('date'),
            end_date__gte=OuterRef('date'),
        ).order_by('start_date')

        return cast(
            models.QuerySet,
            (
                generate_series(
                    self.monitor_element.monitor.start_date.date(),
                    self.monitor_element.monitor.end_date.date(),
                    "1 days",
                    output_field=models.DateField,
                )
                .annotate(date=F('term'))
                .annotate(baseline=Subquery(element_phases.values('baseline')[:1]))
                .annotate(target=Subquery(element_phases.values('target')[:1]))
                .annotate(value=Subquery(element_values.values('total_value')[:1]))
            ),
        )

    def get_cumulative_results(self) -> models.QuerySet:
        return cast(
            models.QuerySet,
            (
                self.get_monitor_element_queryset()
                .annotate(
                    current=Case(
                        When(date__lte=timezone.now().date(), then=Window(Sum('value'), order_by=F('date').asc())),
                        default=None,
                    )
                )
                .annotate(
                    baseline=Window(Sum(F('baseline')), order_by=F('date').asc()),
                )
                .annotate(
                    target=Window(Sum(F('target')), order_by=F('date').asc()),
                )
                .values('date', 'baseline', 'target', 'current')
            ),
        )

    def get_daily_results(self) -> models.QuerySet:
        return cast(
            models.QuerySet,
            (
                self.get_monitor_element_queryset()
                .annotate(
                    current=Case(
                        When(date__lte=timezone.now().date(), then=F('value')),
                        default=None,
                    )
                )
                .values('date', 'baseline', 'target', 'current')
            ),
        )

    def get_results(self, type: MonitorElementDatasetType) -> models.QuerySet:
        if type == MonitorElementDatasetType.CUMULATIVE:
            return self.get_cumulative_results()
        elif type == MonitorElementDatasetType.DAILY:
            return self.get_daily_results()
        raise NotImplementedError(f'Unknown monitor element type: {type}')

    @extend_schema(
        parameters=[MonitorElementDatasetListParamsSerializer],
        responses={200: MonitorElementDatasetSerializer(many=True)},
        summary="Monitor element dataset list",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        params_serializer = MonitorElementDatasetListParamsSerializer(data=request.GET)
        params_serializer.is_valid(raise_exception=True)
        results = self.get_results(**params_serializer.validated_data)

        serializer = MonitorElementDatasetSerializer(results, many=True)
        return Response(serializer.data, status=200)

    def finalize_response(self, request: Request, response: Response, *args: str, **kwargs: str) -> Response:
        response['Content-Disposition'] = f"attachment; filename={self.monitor_element.name}.csv"
        return super().finalize_response(request, response, *args, **kwargs)
