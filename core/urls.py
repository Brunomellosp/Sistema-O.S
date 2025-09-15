from django.urls import path
from . import views
from .views import register

urlpatterns = [
    path('auth/register/', register, name='register'),
    path('users/', views.UserList.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetail.as_view(), name='user-detail'),
    path('ordens-servico/', views.OrdemServicoList.as_view(), name='ordem-list'),
    path('ordens-servico/<int:pk>/', views.OrdemServicoDetail.as_view(), name='ordem-detail'),
    path('ordens-servico/importar-csv/', views.OrdemServicoImportCSV.as_view(), name='ordem-import-csv'),
]
