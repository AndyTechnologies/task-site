from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasksite.accounts'
    label = 'accounts'
    verbose_name = 'Cuentas de usuario'