from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Carrinho, ItemCarrinho
from product.models import ProductVariant
from django.views.decorators.http import require_POST
from django.db import transaction 

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from .serializers import CarrinhoSerializer, ItemCarrinhoSerializer, ProductVariantSerializer



# ADICIONAR ITEM AO CARRINHO
@require_POST
def adicionar_ao_carrinho(request):
    variant_id = request.POST.get('variant_id')
    quantidade_adicionar = int(request.POST.get('quantidade', 1))

    if not variant_id:
        messages.error(request, "Variação do produto não especificada.")
        return redirect('product:home')

    try:
        with transaction.atomic():
            variant = ProductVariant.objects.select_for_update().get(id=variant_id)
            produto = variant.produto

            if quantidade_adicionar <= 0:
                messages.error(request, "A quantidade deve ser pelo menos 1.")
                return redirect('product:produto', slug=produto.slug)

            if request.user.is_authenticated:
                carrinho, created = Carrinho.objects.get_or_create(usuario=request.user)
            else:
                if not request.session.session_key:
                    request.session.create()
                session_key = request.session.session_key
                carrinho, created = Carrinho.objects.get_or_create(session_key=session_key)

            item_carrinho, item_created = ItemCarrinho.objects.get_or_create(
                carrinho=carrinho,
                product_variant=variant,
                defaults={'quantidade': 0}
            )

            nova_quantidade_total = item_carrinho.quantidade + quantidade_adicionar

            if nova_quantidade_total > variant.quantidade:
                variant_info = f"({variant.cor}/{variant.tamanho})" if variant.cor or variant.tamanho else ""
                messages.error(request, f"Não foi possível adicionar mais {quantidade_adicionar} unidades de '{produto.nome} {variant_info}'. Você já tem {item_carrinho.quantidade} e só há {variant.quantidade - item_carrinho.quantidade} unidades restantes em estoque.")
                return redirect('cart:ver_carrinho')

            item_carrinho.quantidade = nova_quantidade_total
            item_carrinho.save()

            variant_info = f"({variant.cor}/{variant.tamanho})" if variant.cor or variant.tamanho else ""
            messages.success(request, f"{quantidade_adicionar}x {produto.nome} {variant_info} adicionado ao carrinho!")

    except ProductVariant.DoesNotExist:
        messages.error(request, "Variação do produto não encontrada.")
        return redirect('product:home')
    except Exception as e:
        messages.error(request, f"Ocorreu um erro ao adicionar ao carrinho: {e}")
        return redirect('product:home')

    return redirect('cart:ver_carrinho')


# DETALHES DOS ITENS DO CARRINHO
def ver_carrinho(request):
    carrinho = None
    itens_carrinho = []
    
    if request.user.is_authenticated:
        try:
            carrinho = Carrinho.objects.get(usuario=request.user)
        except Carrinho.DoesNotExist:
            pass
    else:
        session_key = request.session.session_key
        if session_key:
            try:
                carrinho = Carrinho.objects.get(session_key=session_key)
            except Carrinho.DoesNotExist:
                pass

    if carrinho:
        itens_carrinho = carrinho.itens.all()

    return render(request, 'carrinho.html', {'carrinho': carrinho, 'itens_carrinho': itens_carrinho})


# REMOVE ITEM DO CARRINHO
@require_POST
def remover_do_carrinho(request, item_id):
    item = get_object_or_404(ItemCarrinho, id=item_id)

    if request.user.is_authenticated:
        if item.carrinho.usuario != request.user:
            messages.error(request, "Você não tem permissão para remover este item.")
            return redirect('cart:ver_carrinho')
    else:
        if item.carrinho.session_key != request.session.session_key:
            messages.error(request, "Você não tem permissão para remover este item.")
            return redirect('cart:ver_carrinho')

    item.delete()
    messages.success(request, "Item removido do carrinho.")
    return redirect('cart:ver_carrinho')


# ATUALIZA CARRINHO
@require_POST
def atualizar_quantidade(request, item_id):
    item = get_object_or_404(ItemCarrinho, id=item_id)
    nova_quantidade = int(request.POST.get('quantidade', 1))

    if nova_quantidade < 1:
        messages.error(request, "A quantidade deve ser pelo menos 1.")
        return redirect('cart:ver_carrinho')

    with transaction.atomic():
        item_for_update = ItemCarrinho.objects.select_for_update().get(id=item_id)
        variant_for_stock = item_for_update.product_variant

        if nova_quantidade > variant_for_stock.quantidade:
            variant_info = f"({variant_for_stock.cor}/{variant_for_stock.tamanho})" if variant_for_stock.cor or variant_for_stock.tamanho else ""
            messages.error(request, f"Não temos {nova_quantidade} unidades de '{variant_for_stock.produto.nome} {variant_info}' em estoque. Disponível: {variant_for_stock.quantidade}.")
            return redirect('cart:ver_carrinho')

        if request.user.is_authenticated:
            if item_for_update.carrinho.usuario != request.user:
                messages.error(request, "Você não tem permissão para atualizar este item.")
                return redirect('cart:ver_carrinho')
        else:
            if item_for_update.carrinho.session_key != request.session.session_key:
                messages.error(request, "Você não tem permissão para atualizar este item.")
                return redirect('cart:ver_carrinho')

        item_for_update.quantidade = nova_quantidade
        item_for_update.save()
        
        variant_info = f"({variant_for_stock.cor}/{variant_for_stock.tamanho})" if variant_for_stock.cor or variant_for_stock.tamanho else ""
        messages.success(request, f"Quantidade de {item_for_update.product_variant.produto.nome} {variant_info} atualizada para {nova_quantidade}.")
        
    return redirect('cart:ver_carrinho')


# ----- APIs ----- #


# API de Detalhe do Carrinho
class CartDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, request):
        if request.user.is_authenticated:
            carrinho, _ = Carrinho.objects.get_or_create(usuario=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key
            carrinho, _ = Carrinho.objects.get_or_create(session_key=session_key)
        return carrinho

    def get(self, request, *args, **kwargs):
        carrinho = self.get_object(request)
        serializer = CarrinhoSerializer(carrinho, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        carrinho = self.get_object(request)
        carrinho.itens.all().delete()
        return Response({"message": "Carrinho esvaziado com sucesso."}, status=status.HTTP_204_NO_CONTENT)


# API para Adicionar Item no Carrinho
class CartAddItemAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        variant_id = request.data.get('variant_id')
        quantidade_adicionar = int(request.data.get('quantidade', 1))

        if not variant_id:
            return Response({"error": "ID da variação do produto não fornecido."}, status=status.HTTP_400_BAD_REQUEST)
        if quantidade_adicionar <= 0:
            return Response({"error": "A quantidade deve ser pelo menos 1."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                variant = ProductVariant.objects.select_for_update().get(id=variant_id)
                
                if request.user.is_authenticated:
                    carrinho, _ = Carrinho.objects.get_or_create(usuario=request.user)
                else:
                    if not request.session.session_key:
                        request.session.create()
                    session_key = request.session.session_key
                    carrinho, _ = Carrinho.objects.get_or_create(session_key=session_key)

                item_carrinho, item_created = ItemCarrinho.objects.get_or_create(
                    carrinho=carrinho,
                    product_variant=variant,
                    defaults={'quantidade': 0}
                )

                nova_quantidade_total = item_carrinho.quantidade + quantidade_adicionar

                if nova_quantidade_total > variant.quantidade:
                    return Response(
                        {"error": f"Estoque insuficiente para a variação '{variant.produto.nome} ({variant.cor}/{variant.tamanho})'. Disponível: {variant.quantidade - item_carrinho.quantidade}."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                item_carrinho.quantidade = nova_quantidade_total
                item_carrinho.save()

                serializer = CarrinhoSerializer(carrinho, context={'request': request})
                return Response(serializer.data, status=status.HTTP_200_OK)

        except ProductVariant.DoesNotExist:
            return Response({"error": "Variação do produto não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Ocorreu um erro: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# API para Atualizar Item do carrinho
class CartUpdateItemAPIView(APIView):
    permission_classes = [AllowAny]

    def put(self, request, item_id, *args, **kwargs):
        return self._update_item(request, item_id, 'put')

    def patch(self, request, item_id, *args, **kwargs):
        return self._update_item(request, item_id, 'patch')

    def _update_item(self, request, item_id, method_type):
        try:
            item_carrinho = get_object_or_404(ItemCarrinho.objects.select_for_update(), id=item_id)
            variant = item_carrinho.product_variant

            if request.user.is_authenticated:
                if item_carrinho.carrinho.usuario != request.user:
                    return Response({"error": "Não autorizado."}, status=status.HTTP_403_FORBIDDEN)
            else:
                if item_carrinho.carrinho.session_key != request.session.session_key:
                    return Response({"error": "Não autorizado."}, status=status.HTTP_403_FORBIDDEN)

            nova_quantidade = request.data.get('quantidade')

            if nova_quantidade is None:
                return Response({"error": "Quantidade não fornecida."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                nova_quantidade = int(nova_quantidade)
            except ValueError:
                return Response({"error": "Quantidade inválida."}, status=status.HTTP_400_BAD_REQUEST)

            if nova_quantidade < 1:
                return Response({"error": "A quantidade deve ser pelo menos 1."}, status=status.HTTP_400_BAD_REQUEST)

            if nova_quantidade > variant.quantidade:
                return Response(
                    {"error": f"Estoque insuficiente para a variação '{variant.produto.nome} ({variant.cor}/{variant.tamanho})'. Disponível: {variant.quantidade}."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            item_carrinho.quantidade = nova_quantidade
            item_carrinho.save()

            serializer = ItemCarrinhoSerializer(item_carrinho, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Ocorreu um erro: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# API para Remover Item do Carrinho
class CartRemoveItemAPIView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, item_id, *args, **kwargs):
        try:
            item_carrinho = get_object_or_404(ItemCarrinho, id=item_id)

            if request.user.is_authenticated:
                if item_carrinho.carrinho.usuario != request.user:
                    return Response({"error": "Não autorizado."}, status=status.HTTP_403_FORBIDDEN)
            else:
                if item_carrinho.carrinho.session_key != request.session.session_key:
                    return Response({"error": "Não autorizado."}, status=status.HTTP_403_FORBIDDEN)

            item_carrinho.delete()
            return Response({"message": "Item removido do carrinho com sucesso."}, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response({"error": f"Ocorreu um erro: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)