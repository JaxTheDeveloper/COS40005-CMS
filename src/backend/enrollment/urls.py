from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from .views_api import EnrollmentViewSet

router = DefaultRouter()
router.register('enrollments', EnrollmentViewSet, basename='enrollment')

urlpatterns = [
    path('enrollments/', views.view_enrollments, name='view_enrollments'),
    path('approvals/pending/', views.pending_approvals, name='pending_approvals'),
    path('api/', include(router.urls)),
]
