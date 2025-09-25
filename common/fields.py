from django import forms
from django.db import models
from django_ace import AceWidget
from django_json_widget.widgets import JSONEditorWidget
from djmoney.models.fields import MoneyField as BaseMoneyField
from .validators import RelaxedURLValidator


class MoneyField(BaseMoneyField):
    def formfield(self, **kwargs):
        field = super().formfield(**kwargs)
        field.widget.attrs["class"] = "money-field"
        return field


class RelaxedURLField(models.CharField):
    description = "URL que aceita hostnames internos (sem TLD)"
    default_validators = [RelaxedURLValidator(schemes=["http", "https"])]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 500)
        super().__init__(*args, **kwargs)


class AceEditorTextField(models.Field):
    """
    Campo que salva como TEXT, mas não é subclass de TextField.
    Assim, o admin não aplica o override padrão e o AceWidget permanece.
    """

    description = "TEXT with Ace editor as default widget"

    def __init__(self, *args, ace_attrs=None, **kwargs):
        self.ace_attrs = ace_attrs or {}
        super().__init__(*args, **kwargs)

    # Diz ao Django que o tipo interno é "TextField" (para mapeamento no DB)
    def get_internal_type(self):
        return "TextField"

    # Opcional: declare db_type explicitamente (funciona sem também, mas é mais explícito)
    def db_type(self, connection):
        return models.TextField().db_type(connection)

    def formfield(self, **kwargs):
        defaults = {
            "form_class": forms.CharField,
            "widget": AceWidget(**self.ace_attrs),
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.ace_attrs:
            kwargs["ace_attrs"] = self.ace_attrs
        return name, path, args, kwargs


class JSONEditorTextField(models.JSONField):
    """
    TextField customizado que usa JSONEditorWidget por padrão.
    Aceita configurações extras para o editor através de json_widget_options.
    """

    def __init__(self, *args, json_widget_options=None, **kwargs):
        self.json_widget_options = json_widget_options or {}
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {
            "form_class": forms.JSONField,  # usa JSONField do forms para validação
            "widget": JSONEditorWidget(**self.json_widget_options),
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)

    def deconstruct(self):
        """
        Garante que opções extras sejam registradas nas migrações.
        """
        name, path, args, kwargs = super().deconstruct()
        if self.json_widget_options:
            kwargs["json_widget_options"] = self.json_widget_options
        return name, path, args, kwargs
