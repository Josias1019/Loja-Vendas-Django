from django.core.validators import MinValueValidator, MaxValueValidator
from django_ckeditor_5.fields import CKEditor5Field
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from decimal import Decimal
import os
import re

# CATEGORIA DE PRODUTOS
class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(blank=True, null=True, unique=True)

    # UNICIDADE DE SLUG (categorias)
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        
        original_slug = self.slug
        count = 1
        
        while Categoria.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{count}"
            count += 1
        super(Categoria, self).save(*args, **kwargs)

    def __str__(self):
        return self.nome
    

# NOVO: MODELO DE MARCA
class Marca(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(blank=True, null=True, unique=True)

    class Meta:
        verbose_name_plural = "Marcas"

    # UNICIDADE SLUG (marca)
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)

        original_slug = self.slug
        count = 1
        
        while Marca.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{count}"
            count += 1
        super(Marca, self).save(*args, **kwargs)

    def __str__(self):
        return self.nome


# REGISTRO DE PRODUTOS
class Produto(models.Model):
    nome = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=255)
    categoria = models.ForeignKey(Categoria, related_name='produto', on_delete=models.CASCADE)
    marca = models.ForeignKey(Marca, related_name='produtos', on_delete=models.SET_NULL, null=True, blank=True)
    preco_compra = models.DecimalField(max_digits=10, decimal_places=2)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2) 
    imagem = models.ImageField(upload_to='produtos_fotos', default='default.jpg', blank=True)
    descricao = CKEditor5Field(blank=True, null=True, config_name='default')
    data_lancamento = models.DateField(auto_now_add=True)
    destaque = models.BooleanField(default=False)
    desconto = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    lancamento = models.BooleanField(default=False)

    # UNICIDADE DE SLUG (produtos)
    def save(self, *args, **kwargs):
        if not self.slug: 
            base_slug = slugify(self.nome)
            unique_slug = base_slug
            num = 1

            while Produto.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

    # CALCULAR E APLICA DESCONTO
    @property
    def precoDesconto(self):
        if self.desconto > 0:
            desconto_decimal = Decimal(self.desconto) / Decimal(100)
            preco_com_desconto = self.preco_venda * (1 - desconto_decimal)
            return preco_com_desconto.quantize(Decimal('0.01'))
        return self.preco_venda.quantize(Decimal('0.01'))

    @property
    def lucro(self):
        return (self.preco_venda - self.preco_compra).quantize(Decimal('0.01'))

    @property
    def lucroDesconto(self):
        preco_final = self.precoDesconto
        lucro_final = preco_final - self.preco_compra
        return lucro_final.quantize(Decimal('0.01'))
    
    # PROPRIEDADE PARA ESTOQUE TOTAL DAS VARIAÇÕES (RECOMENDADO)
    @property
    def total_stock(self):

        return sum(variant.quantidade for variant in self.variants.all())

    @property
    def unique_colors(self):

        return list(set(self.variants.values_list('cor', flat=True).distinct()))

    @property
    def unique_sizes(self):
        
        return list(set(self.variants.values_list('tamanho', flat=True).distinct()))
    
    @property
    def min_variant_price(self):
        """Retorna o menor preço de venda entre todas as variações."""
        if self.variants.exists():
            return min(variant.preco_final_variacao for variant in self.variants.all())
        return self.preco_venda 

    @property
    def max_variant_price(self):
        """Retorna o maior preço de venda entre todas as variações."""
        if self.variants.exists():
            return max(variant.preco_final_variacao for variant in self.variants.all())
        return self.preco_venda 


# MODELO DE VARIAÇÃO DE PRODUTO (Tamanho e Cor)
class ProductVariant(models.Model):
    produto = models.ForeignKey(Produto, related_name='variants', on_delete=models.CASCADE)
    cor = models.CharField(max_length=50, blank=True, null=True)
    tamanho = models.CharField(max_length=50, blank=True, null=True)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True,
                           help_text="SKU (Stock Keeping Unit) para esta variação.")
    quantidade = models.PositiveIntegerField(default=0, 
                                            help_text="Estoque para esta combinação específica.")
    ajuste_preco = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    


    class Meta:
        verbose_name = "Variação de Produto"
        verbose_name_plural = "Variações de Produtos"
        unique_together = ('produto', 'cor', 'tamanho')
        ordering = ['cor', 'tamanho']

    def __str__(self):
        variant_name = f"{self.produto.nome}"
        if self.cor:
            variant_name += f" - {self.cor}"
        if self.tamanho:
            variant_name += f" - {self.tamanho}"
        return variant_name
    

    def save(self, *args, **kwargs):
        if not self.sku: 
            base_sku = slugify(self.produto.nome)[:50] 
            color_part = slugify(self.cor)[:20] if self.cor else ""
            size_part = slugify(self.tamanho)[:10] if self.tamanho else ""

            potential_sku = f"{base_sku}-{color_part}-{size_part}".upper()
            
            potential_sku = re.sub(r'[^A-Z0-9]+', '-', potential_sku).strip('-')


            # Garante a unicidade do SKU
            original_potential_sku = potential_sku
            count = 1
            while ProductVariant.objects.filter(sku=potential_sku).exists():
                potential_sku = f"{original_potential_sku}-{count}"
                count += 1
            self.sku = potential_sku
            
        super().save(*args, **kwargs)
    
    @property
    def preco_final_variacao(self):

        return self.produto.preco_venda + self.ajuste_preco


# REGISTRO DE IMAGENS DOS PRODUTOS
class ProdutoImagem(models.Model):
    produto = models.ForeignKey('Produto', related_name='imagens_extra', on_delete=models.CASCADE)
    imagem = models.ImageField(upload_to='produtos_fotos')
    descricao = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Imagem de {self.produto.nome}"