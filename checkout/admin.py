from django.contrib import admin
from .models import Pedido, ItemPedido
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


# --- ITENS DO PEDIDO --- #
class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    fields = ('product_variant', 'quantidade', 'preco_unitario_na_compra', 'get_subtotal')
    readonly_fields = ('get_subtotal', 'preco_unitario_na_compra') 
    
    def get_subtotal(self, obj):
        return f"R$ {obj.subtotal:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    get_subtotal.short_description = 'Subtotal'

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj and obj.pk:
            formset.form.base_fields['product_variant'].widget.can_add_related = False
            formset.form.base_fields['product_variant'].widget.can_change_related = False
            formset.form.base_fields['product_variant'].widget.can_delete_related = False
        return formset


# --- PEDIDO ADMIN --- #
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'nome_completo', 'data_criacao', 'total_geral', 'status', 'pago') 
    list_filter = ('status', 'data_criacao', 'pago') 
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
            'fields': ('data_criacao', 'data_atualizacao')
        }),
    )
    readonly_fields = ('data_criacao', 'data_atualizacao', 'total_geral', 'transacao_id', 'data_pagamento') 

    actions = ['marcar_como_processando', 'marcar_como_enviado', 'marcar_como_entregue', 'marcar_como_pago']
    
    # Enviar Atualização de Status por E-mail
    def enviar_email_status(self, pedido):
        email_subject = f'Atualização do seu pedido #{pedido.id}'
        email_body_html = render_to_string('checkout/email_status_pedido.html', {
            'pedido': pedido,
        })
        email_body_plain = f"Olá, {pedido.nome_completo}!\n\nO status do seu pedido #{pedido.id} foi alterado para: {pedido.status}. \n\nPara ver mais detalhes, acesse seu perfil em nosso site."

        try:
            send_mail(
                email_subject,
                email_body_plain,
                settings.DEFAULT_FROM_EMAIL,
                [pedido.email],
                html_message=email_body_html
            )
        except Exception as e:
            print(f"Erro ao enviar e-mail de atualização de status para o pedido {pedido.id}: {e}")


    # MÉTODO PARA PEGAR MUDANÇAS INDIVIDUAIS
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            self.enviar_email_status(obj)
            
        super().save_model(request, obj, form, change)

    def marcar_como_processando(self, request, queryset):
        queryset.update(status='processando')
        for pedido in queryset:
            self.enviar_email_status(pedido)
        self.message_user(request, "Pedidos marcados como Processando e e-mails de notificação enviados.")
    marcar_como_processando.short_description = "Marcar pedidos selecionados como Processando"

    def marcar_como_enviado(self, request, queryset):
        queryset.update(status='enviado')
        for pedido in queryset:
            self.enviar_email_status(pedido)
        self.message_user(request, "Pedidos marcados como Enviado e e-mails de notificação enviados.")
    marcar_como_enviado.short_description = "Marcar pedidos selecionados como Enviado"

    def marcar_como_entregue(self, request, queryset):
        queryset.update(status='entregue')
        for pedido in queryset:
            self.enviar_email_status(pedido)
        self.message_user(request, "Pedidos marcados como Entregue e e-mails de notificação enviados.")
    marcar_como_entregue.short_description = "Marcar pedidos selecionados como Entregue"
    
    def marcar_como_pago(self, request, queryset):
        queryset.update(pago=True, status='processando', data_pagamento=timezone.now())
        for pedido in queryset:
            self.enviar_email_status(pedido)
        self.message_user(request, "Pedidos marcados como Pagos e Processando. E-mails de notificação enviados.")
    marcar_como_pago.short_description = "Marcar pedidos selecionados como Pagos"