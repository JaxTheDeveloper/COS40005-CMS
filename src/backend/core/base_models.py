from django.db import models
from django.conf import settings
from django.utils import timezone

class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created_at`` and ``updated_at`` fields, along with audit trails.
    """
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='%(app_label)s_%(class)s_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='%(app_label)s_%(class)s_updated'
    )

    class Meta:
        abstract = True

class SoftDeleteModel(models.Model):
    """
    An abstract base class model that provides soft deletion capabilities.
    """
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        """Soft delete the object instead of completely removing it."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """Restore a soft-deleted object."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()

class BaseModel(TimeStampedModel, SoftDeleteModel):
    """
    A base model that combines timestamps, audit trails, and soft deletes.
    """
    class Meta:
        abstract = True
