from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.views.decorators.cache import never_cache
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics

from .models import Produto, Categoria, Marca, ProductVariant
from .serializers import ProdutoSerializer, CategoriaSerializer, MarcaSerializer, ProductVariantSerializer


# PÁGINA PRINCIPAL
@never_cache
def home(request):
    produtos = Produto.objects.all()
    produtoDestaque = Produto.objects.filter(destaque =True)
    produtoDesconto = Produto.objects.filter(desconto__gt=0)
    lancamento = Produto.objects.filter(lancamento=True).order_by('-data_lancamento')

    return render(request, 'home.html', {
        'produtos': produtos,
        'produtoDestaque': produtoDestaque,
        'produtoDesconto': produtoDesconto,
        'lancamento': lancamento
    })


# PÁGINA DE PRODUTOS
def produto(request, slug):
    produto = get_object_or_404(Produto, slug=slug)
    return render(request, 'productmain.html', {
        'produtos': produto,
    })


# ----- APIs ----- #

# API de Busca
@api_view(['GET'])
def busca_produtos_api(request):
    query = request.GET.get('q', '')
    categoria_id = request.GET.get('categoria_id', None)
    categoria_slug = request.GET.get('categoria_slug', None)
    marca_id = request.GET.get('marca_id', None)
    marca_slug = request.GET.get('marca_slug', None)

    produtos = Produto.objects.all()

    if query:
        produtos = produtos.filter(
            Q(nome__icontains=query) | Q(descricao__icontains=query)
        )

    # Filtro de Categoria
    if categoria_id:
        produtos = produtos.filter(categoria__id=categoria_id)
    elif categoria_slug:
        produtos = produtos.filter(categoria__slug=categoria_slug)

    # Filtro de Marca
    if marca_id:
        produtos = produtos.filter(marca__id=marca_id)
    elif marca_slug:
        produtos = produtos.filter(marca__slug=marca_slug)

    produtos = produtos.distinct()

    serializer = ProdutoSerializer(produtos, many=True)
    return Response({"produtos": serializer.data})


# A ÚNICA e CORRETA ProdutoListAPIView
class ProdutoListAPIView(generics.ListAPIView):
    queryset = Produto.objects.all().prefetch_related('variants', 'categoria', 'marca')
    serializer_class = ProdutoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        cor = self.request.query_params.get('cor', None)
        tamanho = self.request.query_params.get('tamanho', None)
        
        # Filtra por cor se o parâmetro 'cor' estiver presente na URL
        if cor:
            queryset = queryset.filter(variants__cor__iexact=cor).distinct() 
                                                                           
        # Filtra por tamanho se o parâmetro 'tamanho' estiver presente na URL
        if tamanho:
            queryset = queryset.filter(variants__tamanho__iexact=tamanho).distinct()

        return queryset


class ProdutoDetailAPIView(generics.RetrieveAPIView):
    queryset = Produto.objects.all().prefetch_related('variants', 'categoria', 'marca')
    serializer_class = ProdutoSerializer
    lookup_field = 'slug'


class CategoriaListAPIView(generics.ListAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class MarcaListAPIView(generics.ListAPIView):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer


# View para listar apenas as cores únicas disponíveis
class UniqueColorsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        cores_unicas = ProductVariant.objects.values_list('cor', flat=True).distinct().exclude(cor__isnull=True).exclude(cor__exact='').order_by('cor')
        return Response(list(cores_unicas))

# View para listar apenas os tamanhos únicos disponíveis
class UniqueSizesAPIView(APIView):
    def get(self, request, *args, **kwargs):
        tamanhos_unicos = ProductVariant.objects.values_list('tamanho', flat=True).distinct().exclude(tamanho__isnull=True).exclude(tamanho__exact='').order_by('tamanho')
        return Response(list(tamanhos_unicos))

# View para buscar variantes de um produto específico
class ProductVariantByProductAPIView(generics.ListAPIView):
    serializer_class = ProductVariantSerializer

    def get_queryset(self):
        produto_slug = self.kwargs['slug']
        try:
            produto = Produto.objects.get(slug=produto_slug)
            return ProductVariant.objects.filter(produto=produto)
        except Produto.DoesNotExist:
            return ProductVariant.objects.none()