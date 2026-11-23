from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(UserManager):
    """Manager personalizado para normalizar email al crear usuarios."""

    def normalize_email(self, email: str) -> str:
        """Normaliza el email a minúsculas."""
        return email.lower().strip() if email else ''

    def create_user(self, username, email, password, **extra_fields):
        email = self.normalize_email(email)
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        email = self.normalize_email(email)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Modelo de usuario personalizado con email único y normalizado."""

    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("Ya existe un usuario con este correo electrónico."),
        },
    )

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Requerido. 150 caracteres o menos. Letras, dígitos y @/./+/-/_ solamente.'),
        error_messages={
            'unique': _("Ya existe un usuario con este nombre de usuario."),
        },
    )

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('usuario')
        verbose_name_plural = _('usuarios')
        db_table = 'accounts_user'

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        self.email = self.__class__.objects.normalize_email(self.email)
        super().save(*args, **kwargs)