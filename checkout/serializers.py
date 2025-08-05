# checkout/serializers.py

from rest_framework import serializers
from .models import Pedido, ItemPedido
from product.serializers import ProductVariantSerializer # Assumindo que você tem um ProductVariantSerializer

class ItemPedidoSerializer(serializers.ModelSerializer):
    # Usar o serializador da ProductVariant para exibir detalhes da variante
    product_variant = ProductVariantSerializer(read_only=True)
    # Adicionar o ID da product_variant para escrita (quando um item é adicionado ao pedido)
    product_variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), source='product_variant', write_only=True
    )
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ItemPedido
        fields = [
            'id', 'product_variant', 'product_variant_id', 'quantidade', 
            'preco_unitario_na_compra', 'subtotal'
        ]
        read_only_fields = ['preco_unitario_na_compra'] # O preço é capturado no momento da compra

class PedidoSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True, read_only=True)
    # Campo para receber os itens do pedido na criação/atualização
    itens_data = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )
    
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'id', 'usuario', 'usuario_username', 'session_key', 'data_criacao', 
            'data_atualizacao', 'status', 'status_display', 'total_geral', 'nome_completo', 
            'email', 'telefone', 'endereco', 'cidade', 'estado', 'cep', 
            'metodo_pagamento', 'transacao_id', 'pago', 'data_pagamento', 'itens', 'itens_data'
        ]
        read_only_fields = [
            'data_criacao', 'data_atualizacao', 'total_geral', 'transacao_id', 
            'data_pagamento', 'usuario', 'session_key' # Estes são preenchidos por lógica de negócio, não pela API diretamente
        ]

    def create(self, validated_data):
        itens_data = validated_data.pop('itens_data', [])
        
        # Preencher campos que vêm do request, mas não do serializer diretamente
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['usuario'] = request.user
        elif request and request.session.session_key:
            validated_data['session_key'] = request.session.session_key

        pedido = Pedido.objects.create(**validated_data)

        # Criar os itens do pedido
        for item_data in itens_data:
            product_variant = item_data.get('product_variant') or item_data.get('product_variant_id')
            quantidade = item_data.get('quantidade')

            if not product_variant or not quantidade:
                raise serializers.ValidationError("Dados de item de pedido inválidos.")

            # Certifique-se de que product_variant é uma instância do modelo
            if isinstance(product_variant, int):
                product_variant = ProductVariant.objects.get(id=product_variant)

            # Capturar o preço no momento da compra
            preco_unitario_na_compra = product_variant.preco_final_variacao

            ItemPedido.objects.create(
                pedido=pedido,
                product_variant=product_variant,
                quantidade=quantidade,
                preco_unitario_na_compra=preco_unitario_na_compra
            )
            # Reduzir o estoque
            product_variant.quantidade -= quantidade
            product_variant.save()
        
        pedido.calcular_total_geral() # Recalcular o total após adicionar os itens
        return pedido

    def update(self, instance, validated_data):
        # Lógica de atualização de pedido pode ser complexa (status, adição/remoção de itens)
        # Por simplicidade, este exemplo foca principalmente na criação.
        # Para atualizar itens, seria melhor ter endpoints separados ou uma lógica mais robusta aqui.
        
        # Exemplo básico de atualização de status
        instance.status = validated_data.get('status', instance.status)
        instance.nome_completo = validated_data.get('nome_completo', instance.nome_completo)
        instance.email = validated_data.get('email', instance.email)
        instance.telefone = validated_data.get('telefone', instance.telefone)
        instance.endereco = validated_data.get('endereco', instance.endereco)
        instance.cidade = validated_data.get('cidade', instance.cidade)
        instance.estado = validated_data.get('estado', instance.estado)
        instance.cep = validated_data.get('cep', instance.cep)
        
        instance.save()
        instance.calcular_total_geral() # Recalcular se algo afetar o total
        return instance