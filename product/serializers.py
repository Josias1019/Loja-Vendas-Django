from rest_framework import serializers
from .models import Produto, Categoria, Marca, ProductVariant


# Serializer para API de Categoria
class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nome', 'slug']


# Serializer para API de Marca
class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ['id', 'nome', 'slug']


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ('id', 'cor', 'tamanho', 'sku', 'quantidade', 'ajuste_preco', 'preco_final_variacao')



# Serializer para API de pesquisa de produtos
class ProdutoSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    marca = MarcaSerializer(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Produto
        fields = (
            'id', 'nome', 'slug', 'categoria', 'marca', 'preco_compra', 
            'preco_venda', 'imagem', 'descricao', 'data_lancamento', 
            'destaque', 'desconto', 'lancamento', 
            'precoDesconto', 'lucro', 'lucroDesconto', 'total_stock', 
            'unique_colors', 'unique_sizes', 'variants',
            'min_variant_price', 'max_variant_price'
        )
        
    def get_imagem_url(self, obj):
        if obj.imagem and hasattr(obj.imagem, 'url'):
            return obj.imagem.url
        return None