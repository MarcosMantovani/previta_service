from typing import Any, List, Tuple, Type, Union

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.contenttypes.admin import GenericStackedInline
from django.urls import path
from django.utils.translation import gettext_lazy as _

from . import models


class NoteInline(GenericStackedInline):
    model = models.Note
    extra = 0
    ct_field = 'content_type'
    ct_fk_field = 'object_id'
    fields = ('contents', 'author', 'created_at')
    readonly_fields = ('author', 'created_at')
    verbose_name = _('Anotação')
    verbose_name_plural = _('Anotações')


class AttachmentInline(GenericStackedInline):
    model = models.Attachment
    extra = 0
    ct_field = 'content_type'
    ct_fk_field = 'object_id'
    fields = ('file', 'notes')
    verbose_name = _('Anexo')
    verbose_name_plural = _('Anexos')
