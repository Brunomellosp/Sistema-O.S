from django.urls import path
from . import views

urlpatterns = [
    path('auth/register/', views.register_user, name='register'),
    path('users/', views.UserList.as_view(), name='user-list'),
    path('users/<uuid:pk>/', views.UserDetail.as_view(), name='user-detail'),
    path('ordens-servico/', views.OrdemServicoList.as_view(), name='ordem-list'),
    path('ordens-servico/<uuid:pk>/', views.OrdemServicoDetail.as_view(), name='ordem-detail'),
    path('ordens-servico/importar-csv/', views.OrdemServicoImportCSV.as_view(), name='ordem-import-csv'),
    path('auth/user/', views.UserProfileView.as_view(), name='auth-user-profile'),
    path('auth/password-reset/', views.password_reset_request, name='password-reset-request'),
    path('auth/password-reset/confirm/', views.password_reset_confirm, name='password-reset-confirm'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='auth-change-password'),
    path('demo/users/', views.presentation_user_list, name='presentation-list'),
    path('demo/users/delete/<uuid:pk>/', views.presentation_user_delete, name='presentation-delete'),
    path('hello/', views.hello_world, name='hello-world'),
]
