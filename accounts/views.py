# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Importe os formulários que você definiu em accounts/forms.py
from .forms import UserRegisterForm, UserLoginForm, UserEditForm, ProfileEditForm
# Importe o modelo Pedido para exibir os pedidos do usuário no perfil
from checkout.models import Pedido

def register(request):
    if request.user.is_authenticated:
        messages.info(request, "Você já está logado.")
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Conta criada com sucesso para {user.username}!")
            return redirect('accounts:profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

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
                login(request, user)
                messages.success(request, f"Bem-vindo de volta, {username}!")
                return redirect('accounts:profile')
            else:
                messages.error(request, "Nome de usuário ou senha inválidos.")
        else:
            messages.error(request, "Erro no formulário de login. Verifique seus dados.")
    else:
        form = UserLoginForm()
    return render(request, 'login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, "Você foi desconectado com sucesso.")
    return redirect('product:home')

@login_required
def profile(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-data_pedido')

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