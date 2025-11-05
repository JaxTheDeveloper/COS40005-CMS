from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.viewsets import UserViewSet
from .views.auth import CustomLoginView, AdminLoginView
from .views.dashboard import dashboard_view, student_dashboard_view, convenor_dashboard_view
from .views.profile import edit_profile
from django.contrib.auth import views as auth_views

router = DefaultRouter()
router.register('users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('admin/login/', AdminLoginView.as_view(), name='admin_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('dashboard/student/', student_dashboard_view, name='student_dashboard'),
    path('dashboard/convenor/', convenor_dashboard_view, name='convenor_dashboard'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='auth/password_reset.html',
        email_template_name='auth/password_reset_email.html',
        subject_template_name='auth/password_reset_subject.txt'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='auth/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'
    ), name='password_reset_complete'),
    path('profile/edit/', edit_profile, name='profile_edit')
]
