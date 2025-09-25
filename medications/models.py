from django.db import models
from common.models import AbstractDatableModel
from residents.models import Resident


class Medication(AbstractDatableModel):
    resident = models.ForeignKey(
        Resident,
        on_delete=models.CASCADE,
        related_name="medications",
        verbose_name="Residente",
        help_text="Residente que toma a medicação",
    )
    name = models.CharField(
        max_length=200,
        verbose_name="Nome da medicação",
        help_text="Nome do medicamento",
    )
    dosage = models.CharField(
        max_length=100,
        verbose_name="Dosagem",
        help_text="Dosagem prescrita (ex: 10mg, 1 comprimido)",
    )
    schedule_time = models.TimeField(
        verbose_name="Horário", help_text="Horário para administração da medicação"
    )
    duration = models.CharField(
        max_length=100,
        verbose_name="Duração",
        help_text="Período do tratamento (ex: 7 dias, contínuo)",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Indica se a medicação está sendo administrada atualmente",
    )

    class Meta:
        verbose_name = "Medicação"
        verbose_name_plural = "Medicações"
        ordering = ["resident__name", "schedule_time", "name"]

    def __str__(self):
        return f"{self.resident.name} - {self.name} ({self.schedule_time.strftime('%H:%M')})"
