import random
from datetime import date, datetime, time, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from faker import Faker
from residents.models import Resident
from medications.models import Medication
from appointments.models import (
    AppointmentExam,
    ExamAttachment,
    TypeChoices,
    StatusChoices,
)


class Command(BaseCommand):
    help = "Popula a aplicação com dados fictícios para desenvolvimento"

    def add_arguments(self, parser):
        parser.add_argument(
            "--residents",
            type=int,
            default=20,
            help="Número de residentes para criar (padrão: 20)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Limpa dados existentes antes de criar novos",
        )

    def handle(self, *args, **options):
        fake = Faker("pt_BR")

        if options["clear"]:
            self.stdout.write("🗑️  Limpando dados existentes...")
            ExamAttachment.objects.all().delete()
            AppointmentExam.objects.all().delete()
            Medication.objects.all().delete()
            Resident.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✅ Dados limpos com sucesso!"))

        num_residents = options["residents"]

        self.stdout.write(f"🏥 Criando {num_residents} residentes...")

        # Listas para dados mais realistas
        health_conditions = [
            "Hipertensão arterial, diabetes tipo 2",
            "Alzheimer em estágio inicial",
            "Artrite reumatoide, osteoporose",
            "Insuficiência cardíaca leve",
            "Demência vascular",
            "Parkinson em estágio inicial",
            "DPOC (Doença Pulmonar Obstrutiva Crônica)",
            "Fibromialgia, ansiedade",
            "Diabetes tipo 2, neuropatia diabética",
            "Osteoartrose, hipertensão",
        ]

        medications_list = [
            ("Losartana", "50mg", "Contínuo"),
            ("Metformina", "850mg", "Contínuo"),
            ("Omeprazol", "20mg", "Contínuo"),
            ("Sinvastatina", "40mg", "Contínuo"),
            ("Captopril", "25mg", "Contínuo"),
            ("Glibenclamida", "5mg", "Contínuo"),
            ("Propranolol", "40mg", "Contínuo"),
            ("Amitriptilina", "25mg", "Contínuo"),
            ("Paracetamol", "500mg", "7 dias"),
            ("Ibuprofeno", "600mg", "5 dias"),
            ("Rivotril", "0,5mg", "Contínuo"),
            ("Donepezila", "10mg", "Contínuo"),
        ]

        appointment_descriptions = [
            "Consulta cardiológica de rotina",
            "Avaliação geriátrica geral",
            "Consulta neurológica",
            "Exame de sangue - hemograma completo",
            "Ecocardiograma",
            "Tomografia computadorizada",
            "Consulta com psicólogo",
            "Fisioterapia - sessão individual",
            "Consulta oftalmológica",
            "Exame de urina",
            "Radiografia de tórax",
            "Consulta endocrinológica",
        ]

        residents = []

        # Criar residentes
        for i in range(num_residents):
            birth_date = fake.date_of_birth(minimum_age=65, maximum_age=95)

            resident = Resident.objects.create(
                name=fake.name(),
                date_of_birth=birth_date,
                family_contact=f"{fake.name()} - {fake.phone_number()}",
                health_history=random.choice(health_conditions),
                notes=(
                    fake.text(max_nb_chars=200) if random.choice([True, False]) else ""
                ),
            )
            residents.append(resident)

        self.stdout.write(
            self.style.SUCCESS(f"✅ {len(residents)} residentes criados!")
        )

        # Criar medicações
        self.stdout.write("💊 Criando medicações...")
        total_medications = 0

        for resident in residents:
            # Cada residente tem entre 1 e 5 medicações
            num_medications = random.randint(1, 5)

            for _ in range(num_medications):
                med_name, dosage, duration = random.choice(medications_list)

                # Horários comuns para medicações
                schedule_times = [
                    time(6, 0),  # 06:00
                    time(8, 0),  # 08:00
                    time(12, 0),  # 12:00
                    time(18, 0),  # 18:00
                    time(20, 0),  # 20:00
                    time(22, 0),  # 22:00
                ]

                Medication.objects.create(
                    resident=resident,
                    name=med_name,
                    dosage=dosage,
                    schedule_time=random.choice(schedule_times),
                    duration=duration,
                    is_active=random.choice([True, True, True, False]),  # 75% ativo
                )
                total_medications += 1

        self.stdout.write(
            self.style.SUCCESS(f"✅ {total_medications} medicações criadas!")
        )

        # Criar consultas e exames
        self.stdout.write("🩺 Criando consultas e exames...")
        total_appointments = 0

        for resident in residents:
            # Cada residente tem entre 3 e 8 consultas/exames
            num_appointments = random.randint(3, 8)

            for _ in range(num_appointments):
                # Data entre 6 meses atrás e 3 meses à frente
                # Como USE_TZ = False, trabalharemos com datetime naive

                if settings.USE_TZ:
                    now = timezone.now()
                else:
                    now = datetime.now()

                start_date = now.date() - timedelta(days=180)
                end_date = now.date() + timedelta(days=90)

                # Gerar data e hora separadamente
                appointment_date_naive = fake.date_between(
                    start_date=start_date, end_date=end_date
                )
                appointment_time = fake.time_object()

                # Combinar data e hora
                appointment_date = datetime.combine(
                    appointment_date_naive, appointment_time
                )

                # Se USE_TZ = True, aplicar timezone
                if settings.USE_TZ:
                    appointment_date = timezone.make_aware(appointment_date)

                # Status baseado na data
                if appointment_date < now:
                    status = random.choice(
                        [
                            StatusChoices.COMPLETED,
                            StatusChoices.COMPLETED,
                            StatusChoices.PENDING,
                        ]
                    )
                else:
                    status = StatusChoices.SCHEDULED

                appointment = AppointmentExam.objects.create(
                    resident=resident,
                    type=random.choice(TypeChoices.choices)[0],
                    description=random.choice(appointment_descriptions),
                    date_time=appointment_date,
                    status=status,
                    notes=(
                        fake.text(max_nb_chars=150)
                        if random.choice([True, False])
                        else ""
                    ),
                )
                total_appointments += 1

                # Alguns exames têm anexos (apenas registros, sem arquivos reais)
                if (
                    appointment.type == TypeChoices.EXAM
                    and appointment.status == StatusChoices.COMPLETED
                    and random.choice([True, False])
                ):

                    ExamAttachment.objects.create(
                        resident=resident,
                        appointment_exam=appointment,
                        file="exam_attachments/2024/01/exemplo_exame.pdf",  # arquivo fictício
                        description=f"Resultado: {appointment.description}",
                    )

        self.stdout.write(
            self.style.SUCCESS(f"✅ {total_appointments} consultas/exames criados!")
        )

        # Estatísticas finais
        self.stdout.write("\n📊 Estatísticas finais:")
        self.stdout.write(f"   👥 Residentes: {Resident.objects.count()}")
        self.stdout.write(f"   💊 Medicações: {Medication.objects.count()}")
        self.stdout.write(f"   🩺 Consultas/Exames: {AppointmentExam.objects.count()}")
        self.stdout.write(f"   📎 Anexos: {ExamAttachment.objects.count()}")

        # Estatísticas por status
        scheduled = AppointmentExam.objects.filter(
            status=StatusChoices.SCHEDULED
        ).count()
        completed = AppointmentExam.objects.filter(
            status=StatusChoices.COMPLETED
        ).count()
        pending = AppointmentExam.objects.filter(status=StatusChoices.PENDING).count()

        self.stdout.write("\n📅 Status das consultas:")
        self.stdout.write(f"   ⏰ Agendadas: {scheduled}")
        self.stdout.write(f"   ✅ Concluídas: {completed}")
        self.stdout.write(f"   ⚠️  Pendentes: {pending}")

        self.stdout.write(self.style.SUCCESS("\n🎉 Dados criados com sucesso!"))
        self.stdout.write(
            "\n💡 Para limpar e recriar dados, use: python manage.py populate_data --clear"
        )
