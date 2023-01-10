from django.db import models


class LiveQuerySet(models.QuerySet):
    def live(self) -> "LiveQuerySet":
        return self.filter(deleted=False)
