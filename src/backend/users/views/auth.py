from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages


class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = False
        return context

    def form_valid(self, form):
        user = form.get_user()
        
        # Prevent admin users from using this login page
        if user.is_staff or user.is_superuser:
            form.add_error(None, "Please use the admin login page")
            return self.form_invalid(form)

        auth_login(self.request, user)
        return redirect(self.get_success_url())

    def get_success_url(self):
        if self.request.user.user_type == 'student':
            return reverse_lazy('student_dashboard')  # You'll need to create this URL pattern
        elif self.request.user.user_type == 'unit_convenor':
            return reverse_lazy('convenor_dashboard')  # You'll need to create this URL pattern
        else:
            return reverse_lazy('dashboard')  # Default dashboard


class AdminLoginView(LoginView):
    template_name = 'auth/login.html'
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = True
        return context

    def form_valid(self, form):
        user = form.get_user()
        
        # Only allow admin users
        if not (user.is_staff or user.is_superuser):
            form.add_error(None, "Access denied. Please use the regular login page.")
            return self.form_invalid(form)

        auth_login(self.request, user)
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('admin:index')