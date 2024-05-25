from django.db import models


class category(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    is_listed = models.BooleanField(default=True, null=True)
    is_deleted = models.BooleanField(default=False, null=True)

    def __str__(self):
        return self.name
