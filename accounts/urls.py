from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [

    # --- URLs --- #
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    path('profile/', views.profile, name='profile'),

    # Autenticação de E-mail
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),

]