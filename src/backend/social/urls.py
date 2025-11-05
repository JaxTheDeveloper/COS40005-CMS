from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from .views_api import SocialGoldViewSet, SocialGoldTransactionViewSet

router = DefaultRouter()
router.register('social-gold', SocialGoldViewSet, basename='social-gold')
router.register('transactions', SocialGoldTransactionViewSet, basename='social-gold-transaction')

urlpatterns = [
    path('achievements/my/', views.my_achievements, name='my_achievements'),
    path('api/', include(router.urls)),
]
