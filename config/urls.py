from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from src.backend.users.views_api import TokenObtainPairCompatView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('rest_framework.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/compat/', TokenObtainPairCompatView.as_view(), name='token_obtain_pair_compat'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/users/', include('src.backend.users.urls')),
    path('api/academic/', include('src.backend.academic.urls')),
    path('api/core/', include('src.backend.core.urls')),
    path('api/enrollment/', include('src.backend.enrollment.urls')),
    path('api/social/', include('src.backend.social.urls')),

    # Web auth and dashboard routes
    path('', include('src.backend.users.urls')),
    path('', include('src.backend.academic.urls')),
    path('', include('src.backend.core.urls')),
    path('', include('src.backend.enrollment.urls')),
    path('', include('src.backend.social.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)