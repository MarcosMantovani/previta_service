from django.db import models
from common.models import AbstractDatableModel


class Resident(AbstractDatableModel):
    name = models.CharField(
        max_length=200, verbose_name="Nome", help_text="Nome completo do residente"
    )
    date_of_birth = models.DateField(
        verbose_name="Data de nascimento", help_text="Data de nascimento do residente"
    )
    family_contact = models.CharField(
        max_length=200,
        verbose_name="Contato familiar",
        help_text="Informações de contato da família",
    )
    health_history = models.TextField(
        verbose_name="Histórico de saúde",
        help_text="Histórico médico e condições de saúde",
        null=True,
        blank=True,
    )
    notes = models.TextField(
        verbose_name="Observações",
        help_text="Observações gerais sobre o residente",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Residente"
        verbose_name_plural = "Residentes"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def age(self):
        """Calcula a idade do residente"""
        from datetime import date

        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )
