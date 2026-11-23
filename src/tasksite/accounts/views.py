from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import CustomUserCreationForm, EmailOrUsernameAuthenticationForm


class AnonymousRequiredMixin:
    """
    Mixin para restringir acceso a usuarios NO autenticados.

    Redirige a usuarios autenticados al dashboard si intentan
    acceder a páginas de registro o login.
    """

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return self.handle_already_authenticated(request)
        return super().dispatch(request, *args, **kwargs)

    def handle_already_authenticated(self, request):
        from django.shortcuts import redirect
        return redirect('accounts:dashboard')


class RegisterView(AnonymousRequiredMixin, CreateView):
    """
    Vista de registro de usuarios usando CreateView.

    Usa CustomUserCreationForm y redirige al login tras éxito.
    """

    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Registro'
        return context


class CustomLoginView(AnonymousRequiredMixin, LoginView):
    """
    Vista de login personalizada usando LoginView.

    Usa EmailOrUsernameAuthenticationForm para autenticación
    con username o email.
    """

    form_class = EmailOrUsernameAuthenticationForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Iniciar sesión'
        return context

    def get_success_url(self):
        return reverse_lazy('accounts:dashboard')


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Vista del dashboard protegida por LoginRequiredMixin.

    Muestra mensaje de bienvenida con el username del usuario.
    """

    template_name = 'accounts/dashboard.html'
    login_url = reverse_lazy('accounts:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Panel de control'
        return context


class CustomLogoutView(LogoutView):
    """
    Vista de logout personalizada usando LogoutView.

    Requiere POST, CSRF, invalida sesión y redirige al login.
    """

    next_page = reverse_lazy('accounts:login')

    def dispatch(self, request, *args, **kwargs):
        # Asegurar que solo se permite POST
        if request.method.lower() != 'post':
            from django.http import HttpResponseNotAllowed
            return HttpResponseNotAllowed(['POST'])
        return super().dispatch(request, *args, **kwargs)