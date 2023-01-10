import factory.fuzzy


class NotificationFactory(factory.django.DjangoModelFactory):
    tenant_user = factory.SubFactory("apps.tenants.factories.TenantUserRelationFactory")
    title = factory.Sequence(lambda n: f"Notification {n}")
    url = factory.Sequence(lambda n: f"/notification/{n}/")
    read = False

    class Meta:
        model = "notifications.Notification"
