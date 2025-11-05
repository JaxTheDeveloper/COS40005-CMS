from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import UnitViewSet, SemesterOfferingViewSet
from . import views

router = DefaultRouter()
router.register('units', UnitViewSet, basename='unit')
router.register('offerings', SemesterOfferingViewSet, basename='offering')

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),

    # Web pages
    path('units/available/', views.available_units, name='available_units'),
    path('units/my/', views.my_units, name='my_units'),
    path('units/<int:unit_id>/resources/', views.manage_resources, name='manage_resources'),
]
