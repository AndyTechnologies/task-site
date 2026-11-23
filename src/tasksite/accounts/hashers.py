from django.contrib.auth.hashers import Argon2PasswordHasher


class CustomArgon2PasswordHasher(Argon2PasswordHasher):
    """
    Hasher Argon2id personalizado con parámetros OWASP recomendados.

    Parámetros:
    - memory_cost: 19456 KiB (19 MiB)
    - time_cost: 2 iteraciones
    - parallelism: 1 hilo
    """

    algorithm = "argon2"
    memory_cost = 19456  # KiB
    time_cost = 2
    parallelism = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Forzar variante Argon2id explícitamente (tipo 0 = Argon2id)
        self.type = 0