# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import Profile # Certifique-se de importar o modelo Profile

# Formulário de Cadastro (Registro)
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True) # Torna o email obrigatório
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email já está registrado.")
        return email

# Formulário de Login
class UserLoginForm(AuthenticationForm):
    pass

# Formulário de Edição de Perfil (Para o usuário logado)
class UserEditForm(UserChangeForm):
    password = None # Remove o campo de senha para não permitir mudança de senha por aqui

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email') # Campos que o usuário pode editar

# Formulário para o Perfil (Profile)
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('cpf', 'telefone', 'endereco_padrao', 'cidade_padrao', 'estado_padrao', 'cep_padrao')