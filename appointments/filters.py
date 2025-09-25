import django_filters
from .models import AppointmentExam, ExamAttachment


class AppointmentExamFilter(django_filters.FilterSet):
    resident = django_filters.NumberFilter(field_name="resident__id")
    type = django_filters.ChoiceFilter(
        choices=AppointmentExam._meta.get_field("type").choices
    )
    status = django_filters.ChoiceFilter(
        choices=AppointmentExam._meta.get_field("status").choices
    )
    date_time = django_filters.DateTimeFromToRangeFilter()

    class Meta:
        model = AppointmentExam
        fields = ["resident", "type", "status", "date_time"]


class ExamAttachmentFilter(django_filters.FilterSet):
    resident = django_filters.NumberFilter(field_name="resident__id")
    appointment_exam = django_filters.NumberFilter(field_name="appointment_exam__id")

    class Meta:
        model = ExamAttachment
        fields = ["resident", "appointment_exam"]
