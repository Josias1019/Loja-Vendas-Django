from rest_framework import serializers
from .models import Carrinho, ItemCarrinho
from product.models import ProductVariant, Produto # Importe ProductVariant e Produto

# Serializer para ProductVariant (para exibir detalhes da variante no carrinho)
class ProductVariantSerializer(serializers.ModelSerializer):
    # Para exibir o nome do produto pai
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    produto_slug = serializers.SlugField(source='produto.slug', read_only=True)
    # Para exibir a URL da imagem principal da variante (se houver)
    # Você precisaria de um campo 'imagem_principal' ou similar em ProductVariant
    # ou uma relação com ProdutoImagem que você possa filtrar por variante.
    # Por enquanto, vou assumir que ProductVariant tem uma imagem direta ou que você pode obtê-la via Produto
    # Se ProductVariant não tiver um campo 'imagem', você pode buscar a imagem principal do Produto pai:
    imagem_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ['id', 'sku', 'cor', 'tamanho', 'quantidade', 'preco_final_variacao', 'produto_nome', 'produto_slug', 'imagem_url']

    def get_imagem_url(self, obj):
        # Assumindo que Produto tem um método ou campo para sua imagem principal
        # Ou que ProductVariant tem uma imagem_url
        if obj.produto.imagens.first(): # Se Produto tiver um related_name 'imagens' para ProdutoImagem
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.produto.imagens.first().imagem.url)
        return None


# Serializer para ItemCarrinho
class ItemCarrinhoSerializer(serializers.ModelSerializer):
    # Usa o ProductVariantSerializer para aninhar os detalhes da variante
    product_variant = ProductVariantSerializer(read_only=True)
    # Campo para receber apenas o ID da variante ao adicionar/atualizar
    product_variant_id = serializers.IntegerField(write_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ItemCarrinho
        fields = ['id', 'product_variant', 'product_variant_id', 'quantidade', 'subtotal']
        read_only_fields = ['id', 'product_variant', 'subtotal'] # product_variant é read_only porque é um objeto aninhado

    def create(self, validated_data):
        # Lógica de criação customizada se necessário, mas ModelSerializer já lida bem
        pass

    def update(self, instance, validated_data):
        # Lógica de atualização customizada se necessário
        pass


# Serializer para Carrinho
class CarrinhoSerializer(serializers.ModelSerializer):
    # Usa o ItemCarrinhoSerializer para aninhar os itens do carrinho
    itens = ItemCarrinhoSerializer(many=True, read_only=True)
    total_geral = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Carrinho
        fields = ['id', 'usuario', 'session_key', 'data_criacao', 'data_atualizacao', 'itens', 'total_geral']
        read_only_fields = ['id', 'usuario', 'session_key', 'data_criacao', 'data_atualizacao', 'itens', 'total_geral']
