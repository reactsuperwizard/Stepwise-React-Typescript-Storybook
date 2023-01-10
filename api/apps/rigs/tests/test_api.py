import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.projects.factories import ProjectFactory
from apps.rigs.factories import (
    ConceptDrillshipFactory,
    ConceptJackupRigFactory,
    ConceptSemiRigFactory,
    CustomDrillshipFactory,
    CustomJackupRigFactory,
    CustomSemiRigFactory,
)
from apps.rigs.models import CustomDrillship, CustomJackupRig, CustomSemiRig
from apps.rigs.serializers import (
    ConceptDrillshipDetailsSerializer,
    ConceptJackupRigDetailsSerializer,
    ConceptSemiRigDetailsSerializer,
    CustomDrillshipDetailsSerializer,
    CustomJackupRigDetailsSerializer,
    CustomRigListSerializer,
    CustomSemiRigDetailsSerializer,
    RigListSerializer,
)
from apps.rigs.tests.fixtures import (
    CUSTOM_DRILLSHIP_DRAFT_DATA,
    CUSTOM_DRILLSHIP_PUBLIC_DATA,
    CUSTOM_JACKUP_RIG_DRAFT_DATA,
    CUSTOM_JACKUP_RIG_PUBLIC_DATA,
    CUSTOM_SEMI_RIG_DRAFT_DATA,
    CUSTOM_SEMI_RIG_PUBLIC_DATA,
)
from apps.tenants.factories import TenantFactory, TenantUserRelationFactory, UserFactory


@pytest.mark.django_db
class TestCustomRigListApi:
    @pytest.fixture
    def setup_rig_list(self):
        self.api_client = APIClient()
        self.tenant_user = TenantUserRelationFactory()
        self.semi_rig = CustomSemiRigFactory(tenant=self.tenant_user.tenant, name='Semi Rig')
        CustomSemiRigFactory()
        self.jackup_rig = CustomJackupRigFactory(tenant=self.tenant_user.tenant, name='Jackup Rig')
        CustomJackupRigFactory()
        self.drillship = CustomDrillshipFactory(tenant=self.tenant_user.tenant, name='Drillship')
        CustomDrillshipFactory()

        self.project = ProjectFactory(tenant=self.tenant_user.tenant)
        self.project.jackup_rigs.add(self.jackup_rig)
        self.project.drillships.add(self.drillship)

    def test_should_retrieve_custom_rig_list(self, setup_rig_list: None):
        url = reverse('rigs:custom_rig_list', kwargs={"tenant_id": self.tenant_user.tenant.pk})
        self.api_client.force_authenticate(user=self.tenant_user.user)

        response = self.api_client.get(url)

        values = ('id', 'name', 'type', 'created_at', 'updated_at', 'draft', 'project_id', 'emp_id')
        assert response.status_code == 200
        assert response.data == {
            'count': 3,
            'next': None,
            'previous': None,
            'results': CustomRigListSerializer(
                [
                    CustomDrillship.objects.with_type().filter(pk=self.drillship.pk).values(*values).first(),
                    CustomJackupRig.objects.with_type().filter(pk=self.jackup_rig.pk).values(*values).first(),
                    CustomSemiRig.objects.with_type().filter(pk=self.semi_rig.pk).values(*values).first(),
                ],
                many=True,
            ).data,
        }

    @pytest.mark.parametrize(
        'ordering,results',
        (
            ('-created_at', ['Drillship', 'Jackup Rig', 'Semi Rig']),
            ('created_at', ['Semi Rig', 'Jackup Rig', 'Drillship']),
            ('name', ['Drillship', 'Jackup Rig', 'Semi Rig']),
            ('-name', ['Semi Rig', 'Jackup Rig', 'Drillship']),
        ),
    )
    def test_should_order_rig_list(self, ordering: str, results: list[str], setup_rig_list: None):
        url = (
            reverse('rigs:custom_rig_list', kwargs={"tenant_id": self.tenant_user.tenant.pk}) + f'?ordering={ordering}'
        )
        self.api_client.force_authenticate(user=self.tenant_user.user)

        response = self.api_client.get(url)

        assert response.status_code == 200

        assert list(map(lambda result: result['name'], response.data['results'])) == results

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        url = reverse('rigs:custom_rig_list', kwargs={"tenant_id": tenant.pk})

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        url = reverse('rigs:custom_rig_list', kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.parametrize(
    'viewname,RigFactory,RigSerializer',
    (
        ('rigs:custom_jackup_rig_details', CustomJackupRigFactory, CustomJackupRigDetailsSerializer),
        ('rigs:custom_semi_rig_details', CustomSemiRigFactory, CustomSemiRigDetailsSerializer),
        ('rigs:custom_drillship_details', CustomDrillshipFactory, CustomDrillshipDetailsSerializer),
    ),
)
@pytest.mark.django_db
class TestCustomRigDetailsApi:
    def test_should_retrieve_rig_details(
        self,
        viewname,
        RigFactory,
        RigSerializer,
    ):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        rig = RigFactory(tenant=tenant_user.tenant)
        url = reverse(viewname, kwargs={"tenant_id": tenant_user.tenant_id, "rig_id": rig.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == RigSerializer(rig).data

    def test_should_be_forbidden_for_anonymous_user(
        self,
        viewname,
        RigFactory,
        RigSerializer,
    ):
        api_client = APIClient()
        rig = RigFactory()
        url = reverse(viewname, kwargs={"tenant_id": rig.tenant_id, "rig_id": rig.pk})

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(
        self,
        viewname: str,
        RigFactory,
        RigSerializer,
    ):
        api_client = APIClient()
        rig = RigFactory()
        user = UserFactory()
        url = reverse(viewname, kwargs={"tenant_id": rig.tenant_id, "rig_id": rig.pk})
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.parametrize(
    'viewname,RigFactory,RigSerializer',
    (
        ('rigs:concept_jackup_rig_details', ConceptJackupRigFactory, ConceptJackupRigDetailsSerializer),
        ('rigs:concept_semi_rig_details', ConceptSemiRigFactory, ConceptSemiRigDetailsSerializer),
        ('rigs:concept_drillship_details', ConceptDrillshipFactory, ConceptDrillshipDetailsSerializer),
    ),
)
@pytest.mark.django_db
class TestConceptRigDetailsApi:
    def test_should_retrieve_rig_details(
        self,
        viewname,
        RigFactory,
        RigSerializer,
    ):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        rig = RigFactory()
        url = reverse(viewname, kwargs={"tenant_id": tenant_user.tenant_id, "rig_id": rig.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == RigSerializer(rig).data

    def test_should_be_forbidden_for_anonymous_user(
        self,
        viewname,
        RigFactory,
        RigSerializer,
    ):
        api_client = APIClient()
        rig = RigFactory()
        tenant = TenantFactory()
        url = reverse(viewname, kwargs={"tenant_id": tenant.pk, "rig_id": rig.pk})

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(
        self,
        viewname,
        RigFactory,
        RigSerializer,
    ):
        api_client = APIClient()
        rig = RigFactory()
        tenant = TenantFactory()
        user = UserFactory()
        url = reverse(viewname, kwargs={"tenant_id": tenant.pk, "rig_id": rig.pk})
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.parametrize(
    'viewname,RigFactory',
    (
        ('rigs:custom_jackup_rig_list', CustomJackupRigFactory),
        ('rigs:custom_semi_rig_list', CustomSemiRigFactory),
        ('rigs:custom_drillship_list', CustomDrillshipFactory),
    ),
)
@pytest.mark.django_db
class TestCustomJackupSemiDrillshipRigListApi:
    def test_should_retrieve_rig_list(
        self,
        viewname,
        RigFactory,
    ):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        rig = RigFactory(tenant=tenant_user.tenant)
        RigFactory()
        url = reverse(viewname, kwargs={"tenant_id": tenant_user.tenant_id})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            "count": 1,
            "previous": None,
            "next": None,
            "results": RigListSerializer([rig], many=True).data,
        }

    def test_should_be_forbidden_for_anonymous_user(
        self,
        viewname,
        RigFactory,
    ):
        api_client = APIClient()
        tenant = TenantFactory()
        url = reverse(viewname, kwargs={"tenant_id": tenant.pk})

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self, viewname, RigFactory):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        url = reverse(viewname, kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.parametrize(
    'viewname,RigFactory',
    (
        ('rigs:concept_jackup_rig_list', ConceptJackupRigFactory),
        ('rigs:concept_semi_rig_list', ConceptSemiRigFactory),
        ('rigs:concept_drillship_list', ConceptDrillshipFactory),
    ),
)
@pytest.mark.django_db
class TestConceptJackupSemiDrillshipRigListApi:
    def test_should_retrieve_concept_rig_list(
        self,
        viewname,
        RigFactory,
    ):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        rig = RigFactory()
        url = reverse(viewname, kwargs={"tenant_id": tenant_user.tenant_id})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            "count": 1,
            "previous": None,
            "next": None,
            "results": RigListSerializer([rig], many=True).data,
        }

    def test_should_be_forbidden_for_anonymous_user(self, viewname, RigFactory):
        api_client = APIClient()
        tenant = TenantFactory()
        url = reverse(viewname, kwargs={"tenant_id": tenant.pk})

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self, viewname, RigFactory):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        url = reverse(viewname, kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateCustomRigApi:
    @pytest.mark.parametrize(
        "viewname, data, RigModel, RigSerializer",
        (
            (
                'rigs:create_custom_jackup_rig',
                CUSTOM_JACKUP_RIG_DRAFT_DATA,
                CustomJackupRig,
                CustomJackupRigDetailsSerializer,
            ),
            (
                'rigs:create_custom_jackup_rig',
                CUSTOM_JACKUP_RIG_PUBLIC_DATA,
                CustomJackupRig,
                CustomJackupRigDetailsSerializer,
            ),
            ('rigs:create_custom_semi_rig', CUSTOM_SEMI_RIG_DRAFT_DATA, CustomSemiRig, CustomSemiRigDetailsSerializer),
            ('rigs:create_custom_semi_rig', CUSTOM_SEMI_RIG_PUBLIC_DATA, CustomSemiRig, CustomSemiRigDetailsSerializer),
            (
                'rigs:create_custom_drillship',
                CUSTOM_DRILLSHIP_DRAFT_DATA,
                CustomDrillship,
                CustomDrillshipDetailsSerializer,
            ),
            (
                'rigs:create_custom_drillship',
                CUSTOM_DRILLSHIP_PUBLIC_DATA,
                CustomDrillship,
                CustomDrillshipDetailsSerializer,
            ),
        ),
    )
    def test_should_create_custom_rig(self, viewname, data, RigModel, RigSerializer):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()

        url = reverse(viewname, kwargs={"tenant_id": tenant_user.tenant_id})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.post(url, data=data, format='json')

        assert response.status_code == 201
        rig = RigModel.objects.get()
        assert response.data == {**RigSerializer(rig).data, **data}

    @pytest.mark.parametrize(
        "viewname, data",
        (
            ('rigs:create_custom_jackup_rig', CUSTOM_JACKUP_RIG_DRAFT_DATA),
            ('rigs:create_custom_semi_rig', CUSTOM_SEMI_RIG_DRAFT_DATA),
            ('rigs:create_custom_drillship', CUSTOM_DRILLSHIP_DRAFT_DATA),
        ),
    )
    def test_should_provide_all_data_to_create_public_custom_rig(self, viewname, data):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()

        url = reverse(viewname, kwargs={"tenant_id": tenant_user.tenant_id})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.post(url, data={**data, "draft": False}, format='json')

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "viewname", ('rigs:create_custom_jackup_rig', 'rigs:create_custom_semi_rig', 'rigs:create_custom_drillship')
    )
    def test_should_be_forbidden_for_anonymous_user(self, viewname):
        api_client = APIClient()
        tenant = TenantFactory()
        url = reverse(viewname, kwargs={"tenant_id": tenant.pk})

        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    @pytest.mark.parametrize(
        "viewname", ('rigs:create_custom_jackup_rig', 'rigs:create_custom_semi_rig', 'rigs:create_custom_drillship')
    )
    def test_should_be_forbidden_for_non_tenant_user(self, viewname):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        url = reverse(viewname, kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user)

        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateCustomRigApi:
    @pytest.mark.parametrize(
        "viewname, draft, data, RigSerializer, RigFactory",
        (
            (
                'rigs:update_custom_jackup_rig',
                True,
                CUSTOM_JACKUP_RIG_DRAFT_DATA,
                CustomJackupRigDetailsSerializer,
                CustomJackupRigFactory,
            ),
            (
                'rigs:update_custom_jackup_rig',
                True,
                CUSTOM_JACKUP_RIG_PUBLIC_DATA,
                CustomJackupRigDetailsSerializer,
                CustomJackupRigFactory,
            ),
            (
                'rigs:update_custom_jackup_rig',
                False,
                CUSTOM_JACKUP_RIG_PUBLIC_DATA,
                CustomJackupRigDetailsSerializer,
                CustomJackupRigFactory,
            ),
            (
                'rigs:update_custom_semi_rig',
                True,
                CUSTOM_SEMI_RIG_DRAFT_DATA,
                CustomSemiRigDetailsSerializer,
                CustomSemiRigFactory,
            ),
            (
                'rigs:update_custom_semi_rig',
                True,
                CUSTOM_SEMI_RIG_PUBLIC_DATA,
                CustomSemiRigDetailsSerializer,
                CustomSemiRigFactory,
            ),
            (
                'rigs:update_custom_semi_rig',
                False,
                CUSTOM_SEMI_RIG_PUBLIC_DATA,
                CustomSemiRigDetailsSerializer,
                CustomSemiRigFactory,
            ),
            (
                'rigs:update_custom_drillship',
                True,
                CUSTOM_DRILLSHIP_DRAFT_DATA,
                CustomDrillshipDetailsSerializer,
                CustomDrillshipFactory,
            ),
            (
                'rigs:update_custom_drillship',
                True,
                CUSTOM_DRILLSHIP_PUBLIC_DATA,
                CustomDrillshipDetailsSerializer,
                CustomDrillshipFactory,
            ),
            (
                'rigs:update_custom_drillship',
                False,
                CUSTOM_DRILLSHIP_PUBLIC_DATA,
                CustomDrillshipDetailsSerializer,
                CustomDrillshipFactory,
            ),
        ),
    )
    def test_should_update_custom_rig(self, viewname, draft, data, RigSerializer, RigFactory):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        rig = RigFactory(tenant=tenant_user.tenant, draft=draft)
        url = reverse(viewname, kwargs={"tenant_id": tenant_user.tenant_id, "rig_id": rig.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 200
        rig.refresh_from_db()
        assert response.data == {**RigSerializer(rig).data, **data}

    @pytest.mark.parametrize(
        "viewname, RigFactory, data",
        (
            ('rigs:update_custom_jackup_rig', CustomJackupRigFactory, CUSTOM_JACKUP_RIG_DRAFT_DATA),
            ('rigs:update_custom_semi_rig', CustomSemiRigFactory, CUSTOM_SEMI_RIG_DRAFT_DATA),
            ('rigs:update_custom_drillship', CustomDrillshipFactory, CUSTOM_DRILLSHIP_DRAFT_DATA),
        ),
    )
    def test_should_provide_all_data_to_update_public_custom_rig(self, viewname, RigFactory, data):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        rig = RigFactory(tenant=tenant_user.tenant)
        url = reverse(viewname, kwargs={"tenant_id": tenant_user.tenant_id, "rig_id": rig.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.put(url, data={**data, "draft": False}, format='json')

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "viewname, RigFactory",
        (
            ('rigs:update_custom_jackup_rig', CustomJackupRigFactory),
            ('rigs:update_custom_semi_rig', CustomSemiRigFactory),
            ('rigs:update_custom_drillship', CustomDrillshipFactory),
        ),
    )
    def test_should_be_forbidden_for_anonymous_user(self, viewname, RigFactory):
        api_client = APIClient()
        rig = RigFactory()
        url = reverse(viewname, kwargs={"tenant_id": rig.tenant_id, "rig_id": rig.pk})

        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    @pytest.mark.parametrize(
        "viewname, RigFactory",
        (
            ('rigs:update_custom_jackup_rig', CustomJackupRigFactory),
            ('rigs:update_custom_semi_rig', CustomSemiRigFactory),
            ('rigs:update_custom_drillship', CustomDrillshipFactory),
        ),
    )
    def test_should_be_forbidden_for_non_tenant_user(self, viewname, RigFactory):
        api_client = APIClient()
        rig = RigFactory()
        user = UserFactory()
        url = reverse(viewname, kwargs={"tenant_id": rig.tenant_id, "rig_id": rig.pk})
        api_client.force_authenticate(user)

        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
@pytest.mark.parametrize(
    'viewname, RigFactory, RigModel',
    (
        ('rigs:delete_custom_jackup_rig', CustomJackupRigFactory, CustomJackupRig),
        ('rigs:delete_custom_semi_rig', CustomSemiRigFactory, CustomSemiRig),
        ('rigs:delete_custom_drillship', CustomDrillshipFactory, CustomDrillship),
    ),
)
class TestDeleteCustomRigApi:
    def test_should_delete_custom_rig(self, viewname, RigFactory, RigModel):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        rig = RigFactory(tenant=tenant_user.tenant)

        url = reverse(viewname, kwargs={"tenant_id": rig.tenant_id, "rig_id": rig.pk})
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.delete(url)

        assert response.status_code == 204
        assert response.data is None
        assert RigModel.objects.filter(pk=rig.pk).first() is None

    def test_should_be_forbidden_for_anonymous_user(self, viewname, RigFactory, RigModel):
        api_client = APIClient()
        rig = RigFactory()
        url = reverse(viewname, kwargs={"tenant_id": rig.tenant_id, "rig_id": rig.pk})

        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self, viewname, RigFactory, RigModel):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        rig = RigFactory()
        url = reverse(viewname, kwargs={"tenant_id": rig.tenant_id, "rig_id": rig.pk})

        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}
