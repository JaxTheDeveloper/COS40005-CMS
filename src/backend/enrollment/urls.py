from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from .views_api import EnrollmentViewSet, TranscriptViewSet

router = DefaultRouter()
router.register('enrollments', EnrollmentViewSet, basename='enrollment')
router.register('transcripts', TranscriptViewSet, basename='transcript')

urlpatterns = [
    # Include DRF router URLs first so API endpoints (e.g. /enrollments/) are handled by the ViewSet.
    path('', include(router.urls)),
    # Traditional HTML views (these intentionally come after the API routes so they don't shadow them)
    path('enrollments/', views.view_enrollments, name='view_enrollments'),
    path('approvals/pending/', views.pending_approvals, name='pending_approvals'),
]
