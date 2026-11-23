from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """
    Formulario de registro adaptado al modelo de usuario personalizado.

    Incluye validación de unicidad de username y email, validación de email,
    y validación de contraseñas mediante los validadores de Django.
    """

    email = forms.EmailField(
        label=_("Correo electrónico"),
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': _('correo@ejemplo.com'),
            'class': 'form-control',
        }),
        help_text=_("Requerido. Se usará para iniciar sesión y recuperar la cuenta."),
        error_messages={
            'required': _("El correo electrónico es obligatorio."),
            'invalid': _("Ingrese un correo electrónico válido."),
        },
    )

    username = forms.CharField(
        label=_("Nombre de usuario"),
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'autocomplete': 'username',
            'placeholder': _('usuario'),
            'class': 'form-control',
        }),
        help_text=_("Requerido. 150 caracteres o menos. Letras, dígitos y @/./+/-/_ solamente."),
        error_messages={
            'required': _("El nombre de usuario es obligatorio."),
        },
    )

    password1 = forms.CharField(
        label=_("Contraseña"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'placeholder': _('Contraseña'),
            'class': 'form-control',
        }),
        help_text=_("Al menos 8 caracteres. No puede ser muy común. No puede ser solo números."),
    )

    password2 = forms.CharField(
        label=_("Confirmar contraseña"),
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'placeholder': _('Repetir contraseña'),
            'class': 'form-control',
        }),
        strip=False,
        help_text=_("Ingrese la misma contraseña para verificación."),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')
        field_classes = {'username': forms.CharField, 'email': forms.EmailField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajustar mensajes de error de password1/password2
        self.fields['password1'].help_text = _(
            "Su contraseña no puede ser muy similar a su otra información personal. "
            "Debe contener al menos 8 caracteres. No puede ser una contraseña común. "
            "No puede ser solo números."
        )
        self.fields['password2'].label = _("Confirmar contraseña")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            if User.objects.filter(email__iexact=email).exists():
                raise ValidationError(
                    _("Ya existe un usuario con este correo electrónico."),
                    code='email_exists',
                )
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            username = username.strip()
            if User.objects.filter(username__iexact=username).exists():
                raise ValidationError(
                    _("Ya existe un usuario con este nombre de usuario."),
                    code='username_exists',
                )
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower().strip()
        if commit:
            user.save()
        return user


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    """
    Formulario de autenticación que acepta username o email en un solo campo.

    Hereda de AuthenticationForm y sobrescribe el campo username para
    aceptar ambos tipos de identificador.
    """

    username = forms.CharField(
        label=_("Usuario o correo electrónico"),
        max_length=254,
        widget=forms.TextInput(attrs={
            'autocomplete': 'username',
            'placeholder': _('usuario o correo@ejemplo.com'),
            'class': 'form-control',
            'autofocus': True,
        }),
    )

    password = forms.CharField(
        label=_("Contraseña"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'placeholder': _('Contraseña'),
            'class': 'form-control',
        }),
    )

    error_messages = {
        'invalid_login': _(
            "Por favor, ingrese un usuario/correo y contraseña correctos. "
            "Ambos campos distinguen mayúsculas/minúsculas."
        ),
        'inactive': _("Esta cuenta está inactiva."),
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        # El campo username ahora acepta email también
        self.fields['username'].widget.attrs['autofocus'] = True

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            # Normalizar para búsqueda
            self.cleaned_data['username'] = username.strip()
        return super().clean()

    def get_user(self):
        """Retorna el usuario autenticado por el backend personalizado."""
        return self.user_cache