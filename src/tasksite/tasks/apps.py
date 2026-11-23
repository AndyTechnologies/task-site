from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasksite.tasks'
    label = 'tasks'
    verbose_name = 'Gestión de tareas'