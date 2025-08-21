from rest_framework import serializers
from .models import Carrinho, ItemCarrinho
from product.models import ProductVariant, Produto

# Serializer para ProductVariant
class ProductVariantSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    produto_slug = serializers.SlugField(source='produto.slug', read_only=True)
    imagem_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ['id', 'sku', 'cor', 'tamanho', 'quantidade', 'preco_final_variacao', 'produto_nome', 'produto_slug', 'imagem_url']

    def get_imagem_url(self, obj):

        if obj.produto.imagens.first():
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.produto.imagens.first().imagem.url)
        return None


# Serializer para ItemCarrinho
class ItemCarrinhoSerializer(serializers.ModelSerializer):

    product_variant = ProductVariantSerializer(read_only=True)
    product_variant_id = serializers.IntegerField(write_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ItemCarrinho
        fields = ['id', 'product_variant', 'product_variant_id', 'quantidade', 'subtotal']
        read_only_fields = ['id', 'product_variant', 'subtotal']

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


# Serializer para Carrinho
class CarrinhoSerializer(serializers.ModelSerializer):
    itens = ItemCarrinhoSerializer(many=True, read_only=True)
    total_geral = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Carrinho
        fields = ['id', 'usuario', 'session_key', 'data_criacao', 'data_atualizacao', 'itens', 'total_geral']
        read_only_fields = ['id', 'usuario', 'session_key', 'data_criacao', 'data_atualizacao', 'itens', 'total_geral']
