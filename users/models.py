from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicManager, PolymorphicModel
from common.models import AbstractUUIDModel


class UserManager(
    PolymorphicManager,
    BaseUserManager,
):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("O campo Email deve ser preenchido"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superusuário deve ter is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superusuário deve ter is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class User(PolymorphicModel, AbstractUser):
    first_name = models.CharField(_("Nome"), max_length=255)
    last_name = models.CharField(_("Sobrenome"), max_length=255)
    email = models.EmailField(_("E-mail"), unique=True)
    phone = models.CharField(_("Telefone"), max_length=255, null=True, blank=True)

    is_active = models.BooleanField(
        _("Está Ativo"),
        default=True,
        help_text=_(
            "Indica se este usuário deve ser tratado como ativo. "
            "Desmarque isso em vez de deletar contas."
        ),
        db_index=True,
    )

    username = None
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return "%s (%s)" % (self.get_full_name(), self.email)

    class Meta:
        verbose_name = _("Usuário")
        verbose_name_plural = _("Usuários")
