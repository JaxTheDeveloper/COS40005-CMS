from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import (
    EventViewSet, SessionViewSet, AttendanceViewSet,
    TicketViewSet, TicketCommentViewSet,
    FormViewSet, FormSubmissionViewSet,
    NotificationViewSet,
    ResourceViewSet, PageViewSet, MediaAssetViewSet
)

router = DefaultRouter()
router.register('events', EventViewSet, basename='event')
router.register('sessions', SessionViewSet, basename='session')
router.register('attendance', AttendanceViewSet, basename='attendance')
router.register('tickets', TicketViewSet, basename='ticket')
router.register('ticket-comments', TicketCommentViewSet, basename='ticketcomment')
router.register('forms', FormViewSet, basename='form')
router.register('submissions', FormSubmissionViewSet, basename='formsubmission')
router.register('notifications', NotificationViewSet, basename='notification')
router.register('resources', ResourceViewSet, basename='resource')
router.register('pages', PageViewSet, basename='page')
router.register('media', MediaAssetViewSet, basename='media')

urlpatterns = [
    # Mounted at /api/core/ in project urls.py — router routes will be available at /api/core/<resource>/
    path('', include(router.urls)),
]
