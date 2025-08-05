# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User # Importe o modelo de usuário padrão do Django

# Importe o modelo Profile do seu app accounts
from .models import Profile # <--- Certifique-se de que esta linha está presente e correta

# Importe o modelo Pedido do seu app checkout
from checkout.models import Pedido # <--- Certifique-se de que esta linha está presente e correta

# Inline para Pedidos: Exibe os pedidos dentro da página de detalhes do Usuário
class PedidoInline(admin.TabularInline):
    model = Pedido
    extra = 0 # Não exibe campos extras vazios por padrão
    # Campos que serão exibidos para cada Pedido
    fields = ('id', 'data_pedido', 'status', 'total_pago', 'endereco', 'cidade', 'estado', 'cep')
    # Define campos somente leitura para evitar alterações acidentais
    readonly_fields = ('id', 'data_pedido', 'status', 'total_pago', 'endereco', 'cidade', 'estado', 'cep')
    can_delete = False # Impede que pedidos sejam deletados diretamente por aqui

    # Isso fará com que o ID do pedido seja um link para a página de edição do pedido
    show_change_link = True

# Inline para o Perfil (Profile): Exibe os campos do Profile dentro da página de detalhes do Usuário
class ProfileInline(admin.StackedInline): # StackedInline é geralmente mais visual para um Profile
    model = Profile
    can_delete = False # Não permite deletar o perfil sem deletar o usuário
    verbose_name_plural = 'Perfil do Usuário' # Nome que aparecerá no admin para esta seção
    # Define quais campos do Profile serão editáveis na página do usuário
    fields = ('cpf', 'telefone', 'endereco_padrao', 'cidade_padrao', 'estado_padrao', 'cep_padrao')

# Desregistre o UserAdmin padrão se ele já estiver registrado, para que possamos modificá-lo
# Isso é necessário se você estiver usando o modelo User padrão do Django.
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass # Já não estava registrado, não há problema

@admin.register(User) # Registra o modelo de usuário padrão com nossas modificações
class CustomUserAdmin(BaseUserAdmin): # Herda do UserAdmin padrão
    # Adiciona ambos os inlines (Profile e Pedidos) à página de detalhes do Usuário
    inlines = (ProfileInline, PedidoInline,) # <--- Ordem importa para a exibição no admin

    # Você pode personalizar o list_display do UserAdmin se quiser
    # list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    # list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    # search_fields = ('username', 'first_name', 'last_name', 'email')

    # Você pode também adicionar campos do Profile no fieldsets do UserAdmin
    # se você quiser que eles apareçam em outras seções, mas o inline já faz isso.
    # Exemplo:
    # fieldsets = BaseUserAdmin.fieldsets + (
    #     ('Informações de Contato', {'fields': ('email',)}),
    # )