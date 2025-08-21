from django.urls import path
from .views import (
    home, produto, busca_produtos_api, 
    ProdutoListAPIView, ProdutoDetailAPIView, CategoriaListAPIView, MarcaListAPIView,
    UniqueColorsAPIView, UniqueSizesAPIView, ProductVariantByProductAPIView 
)


app_name = 'product'


urlpatterns = [

    # URLs Home
    path('', home, name='home'),
    path('produto/<slug:slug>/', produto, name='produto'),

    # ------ APIs ------ #

    path('api/busca/', busca_produtos_api, name='api_busca_produtos'),
    path('api/produtos/', ProdutoListAPIView.as_view(), name='api_lista_produtos'), 
    

    path('api/produtos/cores/', UniqueColorsAPIView.as_view(), name='api-unique-colors'),
    path('api/produtos/tamanhos/', UniqueSizesAPIView.as_view(), name='api-unique-sizes'),
    path('api/produtos/<slug:slug>/variantes/', ProductVariantByProductAPIView.as_view(), name='api-produto-variantes'),
    

    path('api/produtos/<slug:slug>/', ProdutoDetailAPIView.as_view(), name='api_detalhe_produto'),
    
    path('api/categorias/', CategoriaListAPIView.as_view(), name='api_lista_categorias'),
    path('api/marcas/', MarcaListAPIView.as_view(), name='api_lista_marcas'),

]
