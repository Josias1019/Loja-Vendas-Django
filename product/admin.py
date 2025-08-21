from django.contrib import admin
from .models import Produto, Categoria, Marca, ProductVariant


# REGISTRO DE VARIANTES DE PRODUTOS
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('cor', 'tamanho', 'quantidade', 'ajuste_preco') 
    readonly_fields = ('sku',) 
    show_change_link = True 



# REGISTRO DE MARCAS
@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug')
    prepopulated_fields = {'slug': ('nome',)}
    search_fields = ('nome',)


# REGISTRO DE CATEGORIAS
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug',)
    prepopulated_fields = {'slug': ('nome',)}
    search_fields = ('nome',)


# ADMINISTRAÇÃO DE PRODUTOS
@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):

    inlines = [ProductVariantInline]

    list_display = ('nome', 'categoria', 'marca', 'total_stock', 
                    'min_variant_price', 'max_variant_price', 'destaque', 'desconto', 
                    'precoDesconto', 'lucro_display', 'lucroDesconto', 'lancamento')
    
    list_editable = ('destaque', 'desconto', 'lancamento')
    list_filter = ('categoria', 'marca', 'destaque', 'desconto', 'lancamento')
    search_fields = ('nome', 'descricao', 'variants__sku')

    readonly_fields = ('slug',) 
    
    fieldsets = (
        (None, {
            'fields': ('nome', 'slug', 'categoria', 'marca', 'imagem', 'descricao')
        }),
        ('Informações de Preço', {
            'fields': ('preco_compra', 'preco_venda', 'desconto')
        }),
        ('Status do Produto', {
            'fields': ('lancamento', 'destaque',)
        }),
    )


    def total_stock(self, obj):
        
        return obj.total_stock
    total_stock.short_description = 'Estoque Total'

    def min_variant_price(self, obj):
        return obj.min_variant_price
    min_variant_price.short_description = 'Preço Mínimo'

    def max_variant_price(self, obj):
        return obj.max_variant_price
    max_variant_price.short_description = 'Preço Máximo'

    def lucro_display(self, obj):
        return obj.lucro
    lucro_display.short_description = 'Lucro'

    def lucroDesconto(self, obj):
        return obj.lucroDesconto
    lucroDesconto.short_description = 'Lucro c/ Desc.'