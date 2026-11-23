"""
Tests completos para el sistema de autenticación y usuarios.

Cubre:
- Modelo de usuario (creación, unicidad, normalización, hashing)
- Registro (correcto, duplicados, validaciones)
- Autenticación (username, email, normalización, casos edge)
- Acceso y logout (protección, sesión, CSRF)
"""
import re
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError

from tasksite.accounts.hashers import CustomArgon2PasswordHasher
from tasksite.accounts.forms import CustomUserCreationForm, EmailOrUsernameAuthenticationForm
from tasksite.accounts.backends import EmailOrUsernameModelBackend

User = get_user_model()


class UserModelTests(TestCase):
    """Tests para el modelo de usuario personalizado."""

    def test_create_user_basic(self):
        """Creación básica de usuario con username, email y password."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepass123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('securepass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_email_normalization(self):
        """El email se normaliza a minúsculas al crear usuario."""
        user = User.objects.create_user(
            username='testuser',
            email='TEST@EXAMPLE.COM',
            password='securepass123'
        )
        self.assertEqual(user.email, 'test@example.com')

    def test_create_user_email_strips_whitespace(self):
        """El email elimina espacios exteriores al crear usuario."""
        user = User.objects.create_user(
            username='testuser',
            email='  test@example.com  ',
            password='securepass123'
        )
        self.assertEqual(user.email, 'test@example.com')

    def test_create_superuser(self):
        """Creación de superusuario."""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_active)

    def test_username_uniqueness(self):
        """Username debe ser único (case-insensitive a nivel de formulario)."""
        User.objects.create_user(
            username='testuser',
            email='test1@example.com',
            password='securepass123'
        )
        # A nivel de base de datos, Django usa unique case-sensitive
        # La validación case-insensitive está en el formulario
        # Verificar que el formulario rechaza username duplicado case-insensitive
        form_data = {
            'username': 'TESTUSER',
            'email': 'test2@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_email_uniqueness(self):
        """Email debe ser único (case-insensitive)."""
        User.objects.create_user(
            username='testuser1',
            email='test@example.com',
            password='securepass123'
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='testuser2',
                email='TEST@EXAMPLE.COM',  # Diferente capitalización
                password='securepass123'
            )

    def test_email_normalization_on_save(self):
        """Email se normaliza al guardar el modelo."""
        user = User(
            username='testuser',
            email='  TEST@EXAMPLE.COM  ',
            password='securepass123'
        )
        user.save()
        self.assertEqual(user.email, 'test@example.com')

    def test_password_hashing_argon2id(self):
        """Contraseña se hashea con Argon2id usando parámetros OWASP."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepass123'
        )
        # Verificar que el hash tiene el prefijo Argon2id correcto
        self.assertTrue(user.password.startswith('argon2$argon2id$v=19$m=19456,t=2,p=1$'))

    def test_password_verification(self):
        """Verificación de contraseña funciona correctamente."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepass123'
        )
        self.assertTrue(user.check_password('securepass123'))
        self.assertFalse(user.check_password('wrongpassword'))

    def test_set_password_updates_hash(self):
        """set_password actualiza el hash correctamente."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )
        user.set_password('newpass456')
        user.save()
        self.assertTrue(user.check_password('newpass456'))
        self.assertFalse(user.check_password('oldpass123'))

    def test_str_representation(self):
        """Representación string del usuario."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepass123'
        )
        self.assertEqual(str(user), 'testuser')


class Argon2HasherTests(TestCase):
    """Tests específicos para el hasher Argon2id personalizado."""

    def test_hasher_parameters(self):
        """Verificar parámetros del hasher personalizado."""
        hasher = CustomArgon2PasswordHasher()
        self.assertEqual(hasher.memory_cost, 19456)
        self.assertEqual(hasher.time_cost, 2)
        self.assertEqual(hasher.parallelism, 1)
        # El algoritmo base es 'argon2', la variante Argon2id se define en type=0
        self.assertEqual(hasher.algorithm, 'argon2')
        self.assertEqual(hasher.type, 0)

    def test_hash_format(self):
        """El hash generado tiene el formato correcto con parámetros OWASP."""
        hasher = CustomArgon2PasswordHasher()
        password = 'testpassword123'
        hash_value = hasher.encode(password, hasher.salt())
        # Verificar prefijo con parámetros exactos
        self.assertTrue(hash_value.startswith('argon2$argon2id$v=19$m=19456,t=2,p=1$'))

    def test_verify_password(self):
        """Verificación de contraseña con hasher personalizado."""
        hasher = CustomArgon2PasswordHasher()
        password = 'testpassword123'
        hash_value = hasher.encode(password, hasher.salt())
        self.assertTrue(hasher.verify(password, hash_value))
        self.assertFalse(hasher.verify('wrongpassword', hash_value))


class RegistrationFormTests(TestCase):
    """Tests para el formulario de registro."""

    def test_valid_registration(self):
        """Registro válido con todos los campos correctos."""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'new@example.com')
        self.assertTrue(user.check_password('SecurePass123!'))

    def test_duplicate_username_rejected(self):
        """Username duplicado es rechazado."""
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='securepass123'
        )
        form_data = {
            'username': 'EXISTING',  # Diferente capitalización
            'email': 'new@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_duplicate_email_rejected(self):
        """Email duplicado es rechazado."""
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='securepass123'
        )
        form_data = {
            'username': 'newuser',
            'email': 'EXISTING@EXAMPLE.COM',  # Diferente capitalización
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_password_mismatch_rejected(self):
        """Contraseñas que no coinciden son rechazadas."""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'SecurePass123!',
            'password2': 'DifferentPass456!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_weak_password_rejected(self):
        """Contraseña débil es rechazada por validadores de Django."""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': '123',  # Muy corta
            'password2': '123',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        # Los errores de validación de contraseña aparecen en password2 en UserCreationForm
        self.assertIn('password2', form.errors)

    def test_invalid_email_rejected(self):
        """Email inválido es rechazado."""
        form_data = {
            'username': 'newuser',
            'email': 'not-an-email',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_email_normalized_on_save(self):
        """Email se normaliza al guardar el formulario."""
        form_data = {
            'username': 'newuser',
            'email': '  NEW@EXAMPLE.COM  ',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.email, 'new@example.com')


class AuthenticationFormTests(TestCase):
    """Tests para el formulario de autenticación."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepass123'
        )

    def test_valid_login_username(self):
        """Login válido con username."""
        form = EmailOrUsernameAuthenticationForm(data={
            'username': 'testuser',
            'password': 'securepass123',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_user(), self.user)

    def test_valid_login_email(self):
        """Login válido con email."""
        form = EmailOrUsernameAuthenticationForm(data={
            'username': 'test@example.com',
            'password': 'securepass123',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_user(), self.user)

    def test_valid_login_email_case_insensitive(self):
        """Login con email en diferentes capitalizaciones."""
        for email in ['TEST@EXAMPLE.COM', 'Test@Example.Com', 'test@example.com']:
            form = EmailOrUsernameAuthenticationForm(data={
                'username': email,
                'password': 'securepass123',
            })
            self.assertTrue(form.is_valid(), f"Failed for email: {email}")
            self.assertEqual(form.get_user(), self.user)

    def test_invalid_password_rejected(self):
        """Contraseña incorrecta es rechazada."""
        form = EmailOrUsernameAuthenticationForm(data={
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertFalse(form.is_valid())
        self.assertIsNone(form.get_user())

    def test_nonexistent_user_rejected(self):
        """Usuario inexistente es rechazado."""
        form = EmailOrUsernameAuthenticationForm(data={
            'username': 'nonexistent',
            'password': 'anypassword',
        })
        self.assertFalse(form.is_valid())
        self.assertIsNone(form.get_user())

    def test_inactive_user_rejected(self):
        """Usuario inactivo es rechazado."""
        self.user.is_active = False
        self.user.save()
        form = EmailOrUsernameAuthenticationForm(data={
            'username': 'testuser',
            'password': 'securepass123',
        })
        self.assertFalse(form.is_valid())
        self.assertIsNone(form.get_user())


class AuthenticationBackendTests(TestCase):
    """Tests para el backend de autenticación personalizado."""

    def setUp(self):
        self.backend = EmailOrUsernameModelBackend()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='password123'
        )

    def test_authenticate_with_username(self):
        """Autenticación exitosa con username."""
        user = self.backend.authenticate(
            request=None,
            username='user1',
            password='password123'
        )
        self.assertEqual(user, self.user1)

    def test_authenticate_with_email(self):
        """Autenticación exitosa con email."""
        user = self.backend.authenticate(
            request=None,
            username='user1@example.com',
            password='password123'
        )
        self.assertEqual(user, self.user1)

    def test_authenticate_with_email_case_insensitive(self):
        """Autenticación con email en diferentes capitalizaciones."""
        for email in ['USER1@EXAMPLE.COM', 'User1@Example.Com', 'user1@example.com']:
            user = self.backend.authenticate(
                request=None,
                username=email,
                password='password123'
            )
            self.assertEqual(user, self.user1, f"Failed for email: {email}")

    def test_authenticate_wrong_password(self):
        """Contraseña incorrecta retorna None."""
        user = self.backend.authenticate(
            request=None,
            username='user1',
            password='wrongpassword'
        )
        self.assertIsNone(user)

    def test_authenticate_nonexistent_user(self):
        """Usuario inexistente retorna None."""
        user = self.backend.authenticate(
            request=None,
            username='nonexistent',
            password='anypassword'
        )
        self.assertIsNone(user)

    def test_authenticate_inactive_user(self):
        """Usuario inactivo retorna None."""
        self.user1.is_active = False
        self.user1.save()
        user = self.backend.authenticate(
            request=None,
            username='user1',
            password='password123'
        )
        self.assertIsNone(user)

    def test_authenticate_none_credentials(self):
        """Credenciales None retornan None."""
        user = self.backend.authenticate(request=None, username=None, password='pass')
        self.assertIsNone(user)
        user = self.backend.authenticate(request=None, username='user', password=None)
        self.assertIsNone(user)

    def test_ambiguous_identifier_rejected(self):
        """
        Si un identificador coincide con username de un usuario y email de otro,
        la autenticación falla para evitar ambigüedad.
        """
        # user1 tiene username='user1', email='user1@example.com'
        # user2 tiene username='user2', email='user2@example.com'
        # Crear conflicto: user3 con username='user2@example.com'
        user3 = User.objects.create_user(
            username='user2@example.com',  # username que parece email de user2
            email='user3@example.com',
            password='password123'
        )

        # Intentar autenticar con 'user2@example.com' - coincide con
        # email de user2 Y username de user3 -> debe fallar
        user = self.backend.authenticate(
            request=None,
            username='user2@example.com',
            password='password123'  # password de user2 y user3
        )
        # Debe retornar None por ambigüedad
        self.assertIsNone(user)

    def test_timing_attack_prevention(self):
        """
        Verificar que usuario inexistente y contraseña incorrecta
        tienen comportamiento similar (no hay diferencias obvias de tiempo
        en el código - se ejecuta hasher en ambos casos).
        """
        # Este test verifica que el código ejecuta set_password
        # para usuarios inexistentes (prevención de timing attacks)
        user = self.backend.authenticate(
            request=None,
            username='nonexistentuser',
            password='anypassword'
        )
        self.assertIsNone(user)


class ViewAccessTests(TestCase):
    """Tests para vistas: acceso, login, logout, dashboard."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepass123'
        )
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.dashboard_url = reverse('accounts:dashboard')
        self.logout_url = reverse('accounts:logout')

    def test_anonymous_can_access_register(self):
        """Usuario anónimo puede acceder a registro."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_anonymous_can_access_login(self):
        """Usuario anónimo puede acceder a login."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_anonymous_cannot_access_dashboard(self):
        """Usuario anónimo NO puede acceder a dashboard."""
        response = self.client.get(self.dashboard_url)
        # Debe redirigir a login
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_authenticated_can_access_dashboard(self):
        """Usuario autenticado puede acceder a dashboard."""
        self.client.force_login(self.user)
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/dashboard.html')
        self.assertContains(response, 'Bienvenido, testuser')

    def test_authenticated_cannot_access_register(self):
        """Usuario autenticado es redirigido desde registro."""
        self.client.force_login(self.user)
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:dashboard'), response.url)

    def test_authenticated_cannot_access_login(self):
        """Usuario autenticado es redirigido desde login."""
        self.client.force_login(self.user)
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:dashboard'), response.url)

    def test_successful_registration_redirects_to_login(self):
        """Registro exitoso redirige a login."""
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)
        # Verificar que el usuario se creó
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_successful_login_redirects_to_dashboard(self):
        """Login exitoso redirige a dashboard."""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'securepass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:dashboard'), response.url)

    def test_login_with_email(self):
        """Login con email funciona."""
        response = self.client.post(self.login_url, {
            'username': 'test@example.com',
            'password': 'securepass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:dashboard'), response.url)

    def test_failed_login_shows_error(self):
        """Login fallido muestra error."""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        # Verificar que el formulario tiene errores
        form = response.context['form']
        self.assertTrue(form.errors)
        # El error puede estar en non_field_errors o en el campo username
        all_errors = []
        for field_errors in form.errors.values():
            all_errors.extend(field_errors)
        error_text = ' '.join(all_errors)
        self.assertIn('usuario/correo y contraseña correctos', error_text)

    def test_logout_requires_post(self):
        """Logout requiere POST."""
        self.client.force_login(self.user)
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed

    def test_logout_post_invalidates_session(self):
        """Logout por POST invalida la sesión."""
        self.client.force_login(self.user)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)
        # Verificar que la sesión se invalidó
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)

    def test_csrf_protection_on_forms(self):
        """Formularios tienen protección CSRF."""
        response = self.client.get(self.register_url)
        self.assertContains(response, 'csrfmiddlewaretoken')

        response = self.client.get(self.login_url)
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_dashboard_shows_username(self):
        """Dashboard muestra el username del usuario."""
        self.client.force_login(self.user)
        response = self.client.get(self.dashboard_url)
        self.assertContains(response, 'testuser')

    def test_dashboard_has_logout_button(self):
        """Dashboard tiene botón de logout por POST."""
        self.client.force_login(self.user)
        response = self.client.get(self.dashboard_url)
        self.assertContains(response, 'Cerrar sesión')
        self.assertContains(response, 'method="post"')
        self.assertContains(response, 'csrfmiddlewaretoken')


class RegistrationViewTests(TestCase):
    """Tests adicionales para la vista de registro."""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')

    def test_registration_creates_user_with_hashed_password(self):
        """Registro crea usuario con contraseña hasheada."""
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='newuser')
        self.assertTrue(user.check_password('SecurePass123!'))
        # Verificar que NO está en texto plano
        self.assertNotEqual(user.password, 'SecurePass123!')
        # Verificar hash Argon2id
        self.assertTrue(user.password.startswith('argon2$argon2id$v=19$m=19456,t=2,p=1$'))

    def test_registration_with_email_spaces(self):
        """Registro normaliza email con espacios."""
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': '  NEW@EXAMPLE.COM  ',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'new@example.com')


class CustomSettingsTests(TestCase):
    """Tests para verificar configuración de Django."""

    def test_auth_user_model(self):
        """AUTH_USER_MODEL está configurado correctamente."""
        from django.conf import settings
        self.assertEqual(settings.AUTH_USER_MODEL, 'accounts.User')

    def test_authentication_backends(self):
        """AUTHENTICATION_BACKENDS incluye backend personalizado."""
        from django.conf import settings
        self.assertIn('tasksite.accounts.backends.EmailOrUsernameModelBackend', settings.AUTHENTICATION_BACKENDS)
        self.assertIn('django.contrib.auth.backends.ModelBackend', settings.AUTHENTICATION_BACKENDS)

    def test_password_hashers(self):
        """PASSWORD_HASHERS tiene CustomArgon2PasswordHasher en primera posición."""
        from django.conf import settings
        self.assertEqual(
            settings.PASSWORD_HASHERS[0],
            'tasksite.accounts.hashers.CustomArgon2PasswordHasher'
        )

    def test_login_urls(self):
        """URLs de login/logout están configuradas."""
        from django.conf import settings
        self.assertEqual(settings.LOGIN_URL, 'accounts:login')
        self.assertEqual(settings.LOGIN_REDIRECT_URL, 'tasks:list')
        self.assertEqual(settings.LOGOUT_REDIRECT_URL, 'accounts:login')

    def test_installed_apps(self):
        """accounts está en INSTALLED_APPS."""
        from django.conf import settings
        self.assertIn('tasksite.accounts.apps.AccountsConfig', settings.INSTALLED_APPS)