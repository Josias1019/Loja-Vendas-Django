from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

# Importar o modelo de Perfil para pré-preencher o formulário
from accounts.models import Profile  
from cart.models import Carrinho, ItemCarrinho
from .models import Pedido, ItemPedido
from .forms import CheckoutForm


def iniciar_checkout(request):
    carrinho = None
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

    if not carrinho or not carrinho.itens.exists():
        messages.warning(request, "Seu carrinho está vazio. Adicione produtos antes de finalizar a compra.")
        return redirect('cart:ver_carrinho')

    # --- VERIFICAÇÃO DE ESTOQUE ---
    itens_fora_de_estoque = []
    for item_carrinho in carrinho.itens.all():
        if item_carrinho.quantidade > item_carrinho.product_variant.quantidade:
            itens_fora_de_estoque.append(
                f"{item_carrinho.product_variant.produto.nome} ({item_carrinho.product_variant.cor}/{item_carrinho.product_variant.tamanho}) - disponível: {item_carrinho.product_variant.quantidade}, no carrinho: {item_carrinho.quantidade}"
            )
    if itens_fora_de_estoque:
        msg_erro = "Os seguintes itens excedem o estoque disponível: " + "; ".join(itens_fora_de_estoque)
        messages.error(request, msg_erro)
        return redirect('cart:ver_carrinho')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            request.session['checkout_dados'] = form.cleaned_data
            return redirect('checkout:resumo')

        else:
            messages.error(request, "Por favor, corrija os erros no formulário.")
    else:
        # --- Lógica de pré-preenchimento CORRIGIDA ---
        form = CheckoutForm()
        if request.user.is_authenticated:
            try:
                user_profile = request.user.profile
                initial_data = {
                    # Usa os campos do modelo User e Profile
                    'nome_completo': request.user.get_full_name(),
                    'email': request.user.email,
                    'telefone': user_profile.telefone,
                    'endereco': user_profile.endereco_padrao,
                    'cidade': user_profile.cidade_padrao,
                    'estado': user_profile.estado_padrao,
                    'cep': user_profile.cep_padrao,
                }
                form = CheckoutForm(initial=initial_data)
            except Profile.DoesNotExist:
                pass

    return render(request, 'iniciar.html', {'form': form, 'carrinho': carrinho})

# --- NOVA OU ATUALIZADA VIEW DE RESUMO DO PEDIDO ---
def resumo_pedido(request):
    carrinho = None
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

    if not carrinho or not carrinho.itens.exists():
        messages.warning(request, "Seu carrinho está vazio. Adicione produtos antes de finalizar a compra.")
        return redirect('cart:ver_carrinho')

    checkout_dados = request.session.get('checkout_dados')
    if not checkout_dados:
        messages.error(request, "Dados de checkout não encontrados. Por favor, preencha o formulário novamente.")
        return redirect('checkout:iniciar')

    context = {
        'carrinho': carrinho,
        'checkout_dados': checkout_dados,
    }
    return render(request, 'resumo.html', context)


@transaction.atomic
def confirmar_pedido(request):
    if request.method == 'POST':
        carrinho = None
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

        if not carrinho or not carrinho.itens.exists():
            messages.warning(request, "Seu carrinho está vazio ou ocorreu um erro. Por favor, adicione produtos novamente.")
            return redirect('cart:ver_carrinho')

        checkout_dados = request.session.get('checkout_dados')
        if not checkout_dados:
            messages.error(request, "Dados de checkout não encontrados. Por favor, preencha o formulário novamente.")
            return redirect('checkout:iniciar')

        pedido = Pedido.objects.create(
            nome_completo=checkout_dados['nome_completo'],
            email=checkout_dados['email'],
            telefone=checkout_dados['telefone'],
            endereco=checkout_dados['endereco'],
            cidade=checkout_dados['cidade'],
            estado=checkout_dados['estado'],
            cep=checkout_dados['cep'],
            total_geral=carrinho.total_geral,
            usuario=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key if not request.user.is_authenticated else None,
            status='Pendente'
        )

        for item_carrinho in carrinho.itens.all():
            ItemPedido.objects.create(
                pedido=pedido,
                product_variant=item_carrinho.product_variant,
                quantidade=item_carrinho.quantidade,
                preco_unitario_na_compra=item_carrinho.product_variant.preco_final_variacao
            )
            item_carrinho.product_variant.quantidade -= item_carrinho.quantidade
            item_carrinho.product_variant.save()

        carrinho.itens.all().delete()
        if 'checkout_dados' in request.session:
            del request.session['checkout_dados']

        messages.success(request, "Seu pedido foi realizado com sucesso!")
        return redirect('checkout:sucesso')
    else:
        messages.error(request, "Acesso inválido à confirmação do pedido.")
        return redirect('checkout:iniciar')


def pedido_sucesso(request):
    return render(request, 'sucesso.html')