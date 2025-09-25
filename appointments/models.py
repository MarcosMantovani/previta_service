from django.db import models
from django.utils import timezone
from common.models import AbstractDatableModel
from residents.models import Resident


class TypeChoices(models.TextChoices):
    APPOINTMENT = "appointment", "Consulta"
    EXAM = "exam", "Exame"


class StatusChoices(models.TextChoices):
    SCHEDULED = "scheduled", "Agendado"
    COMPLETED = "completed", "Concluído"
    PENDING = "pending", "Pendente"


class AppointmentExam(AbstractDatableModel):

    resident = models.ForeignKey(
        Resident,
        on_delete=models.CASCADE,
        related_name="appointments_exams",
        verbose_name="Residente",
        help_text="Residente que terá a consulta ou exame",
    )
    type = models.CharField(
        max_length=20,
        choices=TypeChoices.choices,
        verbose_name="Tipo",
        help_text="Tipo de atendimento",
    )
    description = models.TextField(
        verbose_name="Descrição", help_text="Descrição da consulta ou exame"
    )
    date_time = models.DateTimeField(
        verbose_name="Data e hora", help_text="Data e hora do atendimento"
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.SCHEDULED,
        verbose_name="Status",
        help_text="Status atual do atendimento",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Observações sobre o atendimento",
    )

    class Meta:
        verbose_name = "Consulta/Exame"
        verbose_name_plural = "Consultas/Exames"
        ordering = ["-date_time"]

    def __str__(self):
        type_display = self.get_type_display()
        return f"{self.resident.name} - {type_display} ({self.date_time.strftime('%d/%m/%Y %H:%M')})"

    @property
    def is_overdue(self):
        """Verifica se o atendimento está em atraso"""
        if self.status == self.StatusChoices.COMPLETED:
            return False
        return self.date_time < timezone.now()


class ExamAttachment(AbstractDatableModel):
    resident = models.ForeignKey(
        Resident,
        on_delete=models.CASCADE,
        related_name="exam_attachments",
        verbose_name="Residente",
        help_text="Residente ao qual o exame pertence",
    )
    appointment_exam = models.ForeignKey(
        AppointmentExam,
        on_delete=models.CASCADE,
        related_name="attachments",
        null=True,
        blank=True,
        verbose_name="Consulta/Exame",
        help_text="Consulta ou exame ao qual o anexo pertence (opcional para exames não registrados)",
    )
    file = models.FileField(
        upload_to="exam_attachments/%Y/%m/",
        verbose_name="Arquivo",
        help_text="Arquivo do exame (PDF, imagem, etc.)",
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Descrição",
        help_text="Descrição do arquivo",
    )

    class Meta:
        verbose_name = "Anexo de Exame"
        verbose_name_plural = "Anexos de Exames"
        ordering = ["-created_at"]

    def __str__(self):
        description = self.description or "Sem descrição"
        return f"{self.resident.name} - {description} ({self.created_at.strftime('%d/%m/%Y')})"

    @property
    def file_extension(self):
        """Retorna a extensão do arquivo"""
        return self.file.name.split(".")[-1].lower() if self.file else None
