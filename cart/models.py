# cart/models.py (Versão Corrigida - Reafirmando)

from django.db import models
from django.conf import settings
from product.models import Produto, ProductVariant # Importe ProductVariant

class Carrinho(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True, unique=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.usuario:
            return f"Carrinho de {self.usuario.username}"
        return f"Carrinho da sessão {self.session_key or 'N/A'}"

    @property
    def total_geral(self):
        return sum(item.subtotal for item in self.itens.all())


class ItemCarrinho(models.Model):
    carrinho = models.ForeignKey(Carrinho, related_name='itens', on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE) # <--- ESSA É A MUDANÇA CRUCIAL
    quantidade = models.PositiveIntegerField(default=1)
    data_adicao = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('carrinho', 'product_variant') # <--- ESSA TAMBÉM

    def __str__(self):
        variant_info = f"({self.product_variant.cor}/{self.product_variant.tamanho})" if self.product_variant.cor or self.product_variant.tamanho else ""
        return f"{self.quantidade} x {self.product_variant.produto.nome} {variant_info} no Carrinho {self.carrinho.id}"

    @property
    def subtotal(self):
        return self.quantidade * self.product_variant.preco_final_variacao