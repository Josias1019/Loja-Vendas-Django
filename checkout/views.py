from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from cart.models import Carrinho, ItemCarrinho
from .models import Pedido, ItemPedido
from .forms import CheckoutForm
from django.db import transaction


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
        if item_carrinho.quantidade > item_carrinho.produto.quantidade:
            itens_fora_de_estoque.append(
                f"{item_carrinho.produto.nome} (disponível: {item_carrinho.produto.quantidade_estoque}, no carrinho: {item_carrinho.quantidade})"
            )
    if itens_fora_de_estoque:
        msg_erro = "Os seguintes itens excedem o estoque disponível: " + "; ".join(itens_fora_de_estoque)
        messages.error(request, msg_erro)
        return redirect('cart:ver_carrinho') # Redireciona para o carrinho para o usuário ajustar

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Armazenar os dados do formulário na sessão e redirecionar para o resumo
            # (Não criar o pedido ainda, pois o pagamento será em outro app)
            request.session['checkout_dados'] = form.cleaned_data
            return redirect('checkout:resumo') # <--- REDIRECIONA PARA A PÁGINA DE RESUMO

        else:
            messages.error(request, "Por favor, corrija os erros no formulário.")
    else:
        initial_data = {}
        if request.user.is_authenticated:
            # Tentar pré-preencher com dados do usuário logado (se tiver um perfil)
            initial_data['nome_completo'] = request.user.get_full_name() if request.user.first_name and request.user.last_name else request.user.username
            initial_data['email'] = request.user.email
            # Adicione outros campos como endereço se tiver no perfil do usuário
        form = CheckoutForm(initial=initial_data)

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

    # Recupera os dados do formulário da sessão
    checkout_dados = request.session.get('checkout_dados')
    if not checkout_dados:
        messages.error(request, "Dados de checkout não encontrados. Por favor, preencha o formulário novamente.")
        return redirect('checkout:iniciar')

    # Passa o carrinho e os dados do formulário para o template
    context = {
        'carrinho': carrinho,
        'checkout_dados': checkout_dados,
    }
    return render(request, 'resumo.html', context)


@transaction.atomic # Garante que as operações sejam atômicas ao confirmar
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

        # --- AQUI É ONDE VOCÊ INTEGRARIA COM O APP DE PAGAMENTO ---
        # Por enquanto, vamos simular a criação do pedido e a redução do estoque.
        # No futuro, esta lógica seria chamada APÓS a confirmação de pagamento do gateway.

        # 1. Criar o Pedido
        pedido = Pedido.objects.create(
            nome_completo=checkout_dados['nome_completo'],
            email=checkout_dados['email'],
            telefone=checkout_dados['telefone'],
            endereco=checkout_dados['endereco'],
            cidade=checkout_dados['cidade'],
            estado=checkout_dados['estado'],
            cep=checkout_dados['cep'],
            total_pago=carrinho.total_geral,
            usuario=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key if not request.user.is_authenticated else None,
            status='Pendente' # Status inicial, seria 'Pago' após confirmação real
        )

        # 2. Mover itens do carrinho para itens do pedido e REDUZIR ESTOQUE
        for item_carrinho in carrinho.itens.all():
            ItemPedido.objects.create(
                pedido=pedido,
                produto=item_carrinho.produto,
                quantidade=item_carrinho.quantidade,
                preco_unitario=item_carrinho.produto.precoDesconto
            )
            # Reduzir o estoque do produto
            item_carrinho.produto.quantidade -= item_carrinho.quantidade
            item_carrinho.produto.save() # Salva a mudança no estoque

        # 3. Limpar o carrinho após a criação do pedido
        carrinho.itens.all().delete() # Deleta apenas os itens do carrinho, mantém o objeto Carrinho
        # Se preferir deletar o objeto Carrinho, use: carrinho.delete()

        # Limpa os dados de checkout da sessão
        if 'checkout_dados' in request.session:
            del request.session['checkout_dados']

        messages.success(request, "Seu pedido foi realizado com sucesso!")
        return redirect('checkout:sucesso')
    else:
        # Se alguém tentar acessar /checkout/confirmar diretamente via GET
        messages.error(request, "Acesso inválido à confirmação do pedido.")
        return redirect('checkout:iniciar')


def pedido_sucesso(request):
    return render(request, 'sucesso.html')