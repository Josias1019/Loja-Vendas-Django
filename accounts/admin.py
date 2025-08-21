from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Profile 

from checkout.models import Pedido

# EXIBE PEDIDOS DENTRO DE USUÁRIOS
class PedidoInline(admin.TabularInline):
    model = Pedido
    extra = 0
    fields = ('id', 'data_criacao', 'status', 'total_geral', 'endereco', 'cidade', 'estado', 'cep')
    readonly_fields = ('id', 'data_criacao', 'status', 'total_geral', 'endereco', 'cidade', 'estado', 'cep')
    can_delete = False

    show_change_link = True

# EXIBE CAMPOS DO PERFIL
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Perfil do Usuário'
    fields = ('cpf', 'telefone', 'endereco_padrao', 'cidade_padrao', 'estado_padrao', 'cep_padrao')

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass 


# REGISTRA MODELOS DO USUÁRIO COM ALTERAÇÕES DO SUPERUSER / ADMINSTRADOR
@admin.register(User) 
class CustomUserAdmin(BaseUserAdmin): 
    inlines = (ProfileInline, PedidoInline,)
