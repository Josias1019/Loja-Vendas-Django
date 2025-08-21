from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from cart.models import Carrinho
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from .forms import UserRegisterForm, UserLoginForm, UserEditForm, ProfileEditForm
from checkout.models import Pedido


# REGISTRO DE USUÁRIOS
def register(request):
    if request.user.is_authenticated:
        messages.info(request, "Você já está logado.")
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False 
            user.save()
            
            # Envio de e-mail de confirmação
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            current_site = request.get_host()
            link_confirmacao = reverse('accounts:activate', kwargs={'uidb64': uid, 'token': token})
            link_completo = f"http://{current_site}{link_confirmacao}"

            email_subject = 'Ative sua Conta na Loja-Django'
            email_body_html = render_to_string('accounts/email_confirmacao.html', {
                'user': user,
                'link_confirmacao': link_completo,
            })
            email_body_plain = f"Olá, {user.username}!\n\nAgradecemos por se registrar. Por favor, clique no link abaixo para ativar sua conta:\n\n{link_completo}"
            
            try:
                send_mail(
                    email_subject,
                    email_body_plain,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=email_body_html
                )
                messages.success(request, "Conta criada com sucesso! Por favor, verifique seu e-mail para ativar sua conta.")
            except Exception as e:
                messages.warning(request, "Conta criada, mas houve um erro ao enviar o e-mail de ativação. Por favor, entre em contato conosco.")

            return redirect('accounts:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})


# ATIVAÇÃO DE CONTA APÓS CONFIRMAÇÃO POR E-MAIL
def activate(request, uidb64, token):

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.profile.email_verificado = True
        user.profile.save()
        user.save()
        login(request, user)
        messages.success(request, "Sua conta foi ativada com sucesso! Você já está logado.")
        return redirect('accounts:profile')
    else:
        messages.error(request, "O link de ativação é inválido ou expirou.")
        return redirect('accounts:register')


# LOGING DO USUÁRIO
def user_login(request):
 
    if request.user.is_authenticated:
        messages.info(request, "Você já está logado.")
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if not user.is_active:
                    messages.error(request, "Sua conta não foi ativada. Por favor, verifique seu e-mail.")
                    return render(request, 'login.html', {'form': form})
                
                login(request, user)
                messages.success(request, f"Bem-vindo de volta, {username}!")

                session_key = request.session.session_key
                if session_key:
                    try:
                        carrinho_anonimo = Carrinho.objects.get(session_key=session_key)
                        carrinho_anonimo.usuario = user
                        carrinho_anonimo.session_key = None
                        carrinho_anonimo.save()
                        messages.info(request, "Seu carrinho foi recuperado!")
                    except Carrinho.DoesNotExist:
                        pass
                return redirect('accounts:profile')
            else:
                messages.error(request, "Nome de usuário ou senha inválidos.")
        else:
            messages.error(request, "Erro no formulário de login. Verifique seus dados.")
    else:
        form = UserLoginForm()
    return render(request, 'login.html', {'form': form})


# LOGOUT USUÁRIO
@login_required
def user_logout(request):

    logout(request)
    messages.info(request, "Você foi desconectado com sucesso.")
    return redirect('product:home')


# EXIBE O PERFIL DO USUÁRIO
@login_required
def profile(request):

    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-data_criacao')

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Seu perfil foi atualizado com sucesso!")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Erro ao atualizar o perfil. Por favor, corrija os erros.")
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'pedidos': pedidos,
    }
    return render(request, 'profile.html', context)