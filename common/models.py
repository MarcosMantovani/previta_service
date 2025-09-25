import uuid
from django.db.models import Func, fields
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class AbstractAvailabilityModel(models.Model):
    is_enabled = models.BooleanField(_("Está Ativo"), default=True, db_index=True)

    class Meta:
        abstract = True


class AbstractDatableModel(models.Model):
    created_at = models.DateTimeField(_("Criado em"), editable=False, db_index=True)
    updated_at = models.DateTimeField(_("Atualizado em"), editable=False, db_index=True)

    def save(self, *args, **kwargs):
        updated_fields = kwargs.pop("update_fields", None)

        incoming_created_at = updated_fields and "created_at" in updated_fields
        incoming_updated_at = updated_fields and "updated_at" in updated_fields

        if not self.created_at and not incoming_created_at:
            self.created_at = timezone.now()

        if not incoming_updated_at:
            self.updated_at = timezone.now()

        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class AbstractUUIDModel(models.Model):
    uuid = models.UUIDField(_("UUID"), default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        abstract = True


class Note(AbstractDatableModel, AbstractUUIDModel):
    contents = models.TextField(_("Conteúdo"))
    author = models.ForeignKey(
        "users.User",
        verbose_name=_("Autor"),
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    entity = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = _("Nota")
        verbose_name_plural = _("Notas")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return f"{self.author} - {self.created_at}"


def get_attachment_upload_path(instance, filename):
    return f"attachments/{instance.entity.__class__.__name__}/{instance.entity.id}/{filename}"


class Attachment(AbstractDatableModel, AbstractUUIDModel):
    file = models.FileField(_("Arquivo"), upload_to=get_attachment_upload_path)
    notes = models.TextField(_("Observações"), null=True, blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    entity = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = _("Anexo")
        verbose_name_plural = _("Anexos")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]


class ExtractEpoch(Func):
    function = "EXTRACT"
    template = "%(function)s(EPOCH FROM %(expressions)s)"
    output_field = fields.IntegerField()
