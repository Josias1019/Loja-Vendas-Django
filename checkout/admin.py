# checkout/admin.py

from django.contrib import admin
from .models import Pedido, ItemPedido

# --- Inline para os Itens do Pedido ---
class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    # MUDANÇA CRÍTICA: Referenciando product_variant
    fields = ('product_variant', 'quantidade', 'preco_unitario_na_compra', 'subtotal')
    # preco_unitario_na_compra agora é apenas leitura se não for preenchido no admin
    readonly_fields = ('subtotal', 'preco_unitario_na_compra') 
    
    def get_formset(self, request, obj=None, **kwargs):
        # Garante que o preco_unitario_na_compra não possa ser editado após o pedido ser criado
        # e que product_variant seja um SelectBox apropriado
        formset = super().get_formset(request, obj, **kwargs)
        if obj and obj.pk: # Se o Pedido já existe (estamos editando)
            formset.form.base_fields['product_variant'].widget.can_add_related = False
            formset.form.base_fields['product_variant'].widget.can_change_related = False
            formset.form.base_fields['product_variant'].widget.can_delete_related = False
        return formset


# --- Classe Admin para o modelo Pedido ---
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'nome_completo', 'data_criacao', 'total_geral', 'status', 'pago') # Ajustado nome do campo
    list_filter = ('status', 'data_criacao', 'pago') # Ajustado nome do campo
    search_fields = ('id', 'usuario__username', 'nome_completo', 'email')
    inlines = [ItemPedidoInline]

    fieldsets = (
        (None, {
            'fields': ('usuario', 'session_key', 'total_geral', 'status', 'pago', 'data_pagamento', 'metodo_pagamento', 'transacao_id')
        }),
        ('Informações do Cliente e Entrega', {
            'fields': ('nome_completo', 'email', 'telefone', 'endereco', 'cidade', 'estado', 'cep')
        }),
        ('Datas', {
            'fields': ('data_criacao', 'data_atualizacao') # Adicionado data_atualizacao
        }),
    )
    readonly_fields = ('data_criacao', 'data_atualizacao', 'total_geral', 'transacao_id', 'data_pagamento') # Campos apenas leitura

    # Ações customizadas para o admin (opcional, mas útil)
    actions = ['marcar_como_processando', 'marcar_como_enviado', 'marcar_como_entregue', 'marcar_como_pago']

    def marcar_como_processando(self, request, queryset):
        queryset.update(status='processando')
        self.message_user(request, "Pedidos marcados como Processando.")
    marcar_como_processando.short_description = "Marcar pedidos selecionados como Processando"

    def marcar_como_enviado(self, request, queryset):
        queryset.update(status='enviado')
        self.message_user(request, "Pedidos marcados como Enviado.")
    marcar_como_enviado.short_description = "Marcar pedidos selecionados como Enviado"

    def marcar_como_entregue(self, request, queryset):
        queryset.update(status='entregue')
        self.message_user(request, "Pedidos marcados como Entregue.")
    marcar_como_entregue.short_description = "Marcar pedidos selecionados como Entregue"
    
    def marcar_como_pago(self, request, queryset):
        queryset.update(pago=True, status='processando', data_pagamento=timezone.now())
        self.message_user(request, "Pedidos marcados como Pagos e Processando.")
    marcar_como_pago.short_description = "Marcar pedidos selecionados como Pagos"