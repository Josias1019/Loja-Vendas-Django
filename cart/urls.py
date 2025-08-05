# cart/urls.py (ADICIONANDO URLs DE API)

from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    # --- URLs para Views HTML (mantidas) ---
    path('adicionar/', views.adicionar_ao_carrinho, name='adicionar_ao_carrinho'),
    path('', views.ver_carrinho, name='ver_carrinho'),
    path('remover/<int:item_id>/', views.remover_do_carrinho, name='remover_do_carrinho'), # Corrigido o nome
    path('atualizar/<int:item_id>/', views.atualizar_quantidade, name='atualizar_quantidade'),

    # --- URLs para APIs DRF ---
    path('api/', views.CartDetailAPIView.as_view(), name='api_cart_detail'),
    path('api/add/', views.CartAddItemAPIView.as_view(), name='api_cart_add_item'),
    path('api/update/<int:item_id>/', views.CartUpdateItemAPIView.as_view(), name='api_cart_update_item'),
    path('api/remove/<int:item_id>/', views.CartRemoveItemAPIView.as_view(), name='api_cart_remove_item'),
    # A API para esvaziar o carrinho está no DELETE de CartDetailAPIView
]