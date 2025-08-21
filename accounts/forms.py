from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import Profile


# Formulário de Cadastro
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
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

# Formulário de Edição de Perfil
class UserEditForm(UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

# Formulário para o Perfil
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('cpf', 'telefone', 'endereco_padrao', 'cidade_padrao', 'estado_padrao', 'cep_padrao')