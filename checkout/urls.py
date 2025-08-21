from django.urls import path
from . import views

app_name = 'checkout'

urlpatterns = [

    # --- URLs --- #
    path('iniciar/', views.iniciar_checkout, name='iniciar'),
    path('resumo/', views.resumo_pedido, name='resumo'),
    path('confirmar/', views.confirmar_pedido, name='confirmar'),
    path('sucesso/', views.pedido_sucesso, name='sucesso'),
    
]