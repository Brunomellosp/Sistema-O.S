from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', views.presentation_user_list, name='presentation-list'),
    path('users/delete/<uuid:pk>/', views.presentation_user_delete, name='presentation-delete'),
    path('api/v1/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/', include('core.urls')),
]
