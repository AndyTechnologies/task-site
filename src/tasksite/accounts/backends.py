from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Backend de autenticación que permite iniciar sesión con username o email.

    Resuelve el usuario buscando por username o email (normalizado a minúsculas)
    y verifica la contraseña usando los mecanismos estándar de Django.

    Rechaza la autenticación si el identificador coincide con el username de un
    usuario y el email de otro usuario diferente (ambigüedad).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        # Normalizar el identificador
        identifier = username.strip()
        normalized_identifier = identifier.lower()

        # Buscar usuarios que coincidan con el identificador como username
        username_matches = list(User.objects.filter(username__iexact=identifier))
        # Buscar usuarios que coincidan con el identificador como email
        email_matches = list(User.objects.filter(email__iexact=normalized_identifier))

        # Detectar ambigüedad: el identificador coincide con username de uno
        # y email de OTRO usuario diferente
        if username_matches and email_matches:
            # Verificar si hay usuarios diferentes en las dos listas
            username_ids = {u.pk for u in username_matches}
            email_ids = {u.pk for u in email_matches}
            if username_ids != email_ids:
                # Ambigüedad: hay al menos un usuario diferente en cada lista
                # Ejecutar hasher para prevención de timing attacks
                User().set_password(password)
                return None

        # Resolver usuario: prioridad a username exacto, luego email
        user = None
        if len(username_matches) == 1:
            user = username_matches[0]
        elif len(email_matches) == 1:
            user = email_matches[0]
        elif len(username_matches) > 1 or len(email_matches) > 1:
            # Múltiples coincidencias en el mismo campo (no debería pasar por unique constraint)
            User().set_password(password)
            return None
        else:
            # No encontrado - ejecutar hasher para timing attack prevention
            User().set_password(password)
            return None

        # Verificar contraseña y usuario activo
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None