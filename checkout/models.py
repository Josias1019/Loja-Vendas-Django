from django.db import models
from django.conf import settings
from product.models import ProductVariant
from django.urls import reverse


# MODELO DE PEDIDO
class Pedido(models.Model):
    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('processando', 'Processando'),
        ('enviado', 'Enviado'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    )

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Usuário")
    session_key = models.CharField(max_length=40, null=True, blank=True, help_text="Chave de sessão para usuários não logados")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data do Pedido")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name="Status")
    total_geral = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Total do Pedido")
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo")
    email = models.EmailField(verbose_name="Email")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    endereco = models.CharField(max_length=255, verbose_name="Endereço")
    cidade = models.CharField(max_length=100, verbose_name="Cidade")
    estado = models.CharField(max_length=100, verbose_name="Estado")
    cep = models.CharField(max_length=10, verbose_name="CEP")
    metodo_pagamento = models.CharField(max_length=50, blank=True, null=True, verbose_name="Método de Pagamento")
    transacao_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID da Transação")
    pago = models.BooleanField(default=False, verbose_name="Pago")
    data_pagamento = models.DateTimeField(null=True, blank=True, verbose_name="Data do Pagamento")


    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-data_criacao']

    def __str__(self):
        return f"Pedido {self.id} - {self.nome_completo}"

    def calcular_total_geral(self):
        """Calcula o total de todos os itens no pedido."""
        total = sum(item.subtotal for item in self.itens.all())
        self.total_geral = total
        self.save()
    
    def get_absolute_url(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name), args=[self.pk])


# DETALHES DO ITEM DO PEDIDO
class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens', verbose_name="Pedido")
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, verbose_name="Variação do Produto")
    quantidade = models.PositiveIntegerField(default=1, verbose_name="Quantidade")
    preco_unitario_na_compra = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Unitário na Compra") 

    class Meta:
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"
        unique_together = ('pedido', 'product_variant')

    def __str__(self):
        variant_info = ""
        if self.product_variant:
            if self.product_variant.cor and self.product_variant.tamanho:
                variant_info = f" ({self.product_variant.cor}/{self.product_variant.tamanho})"
            elif self.product_variant.cor:
                variant_info = f" ({self.product_variant.cor})"
            elif self.product_variant.tamanho:
                variant_info = f" ({self.product_variant.tamanho})"
            return f"{self.quantidade} x {self.product_variant.produto.nome}{variant_info} - Pedido {self.pedido.id}"
        return f"{self.quantidade} x Produto Desconhecido - Pedido {self.pedido.id}"

    @property
    def subtotal(self): 
        preco = self.preco_unitario_na_compra if self.preco_unitario_na_compra is not None else 0
        return self.quantidade * preco