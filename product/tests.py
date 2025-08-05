# product/tests.py

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, datetime
import unittest.mock
import pytz 
from decimal import Decimal
import json
import os

from rest_framework import status

from .models import Produto, Categoria, Marca, ProdutoImagem

# --- Testes para os Modelos ---

class CategoriaModelTest(TestCase):
    """
    Testes para o modelo Categoria.
    """

    def test_categoria_creation(self):
        """
        Verifica se uma categoria pode ser criada com sucesso.
        """
        categoria = Categoria.objects.create(nome='Eletrônicos')
        self.assertEqual(categoria.nome, 'Eletrônicos')
        self.assertEqual(categoria.slug, 'eletronicos')
        self.assertTrue(Categoria.objects.filter(nome='Eletrônicos').exists())

    def test_categoria_slug_uniqueness(self):
        """
        Verifica a unicidade do slug para categorias.
        """
        Categoria.objects.create(nome='Roupas')
        categoria2 = Categoria.objects.create(nome='Roupas')
        self.assertEqual(categoria2.slug, 'roupas-1')

        categoria3 = Categoria.objects.create(nome='Roupas')
        self.assertEqual(categoria3.slug, 'roupas-2')
        
        # Testa atualização de categoria com mesmo nome
        categoria_existente = Categoria.objects.create(nome='Calçados')
        categoria_existente.nome = 'Calçados' # Mantém o mesmo nome
        categoria_existente.save()
        # O slug não deve mudar se o nome não for alterado E ele já for único
        self.assertEqual(categoria_existente.slug, 'calcados') 
        
        # Testar slug gerado a partir de nome com caracteres especiais
        categoria_especial = Categoria.objects.create(nome='Móveis & Decoração')
        self.assertEqual(categoria_especial.slug, 'moveis-decoracao')


    def test_categoria_str_representation(self):
        """
        Verifica a representação __str__ do modelo Categoria.
        """
        categoria = Categoria.objects.create(nome='Livros')
        self.assertEqual(str(categoria), 'Livros')

class MarcaModelTest(TestCase):
    """
    Testes para o modelo Marca.
    """

    def test_marca_creation(self): 
        """
        Verifica se uma marca pode ser criada com sucesso e seu slug gerado.
        """
        marca = Marca.objects.create(nome='Nike')
        self.assertEqual(marca.nome, 'Nike')
        self.assertEqual(marca.slug, 'nike')
        self.assertTrue(Marca.objects.filter(nome='Nike').exists())
        self.assertTrue(Marca.objects.filter(slug='nike').exists())

    def test_marca_slug_generation_on_save(self):
        """
        Verifica que o slug é gerado automaticamente e que caracteres especiais são tratados.
        """
        marca = Marca.objects.create(nome='Marca de Teste XYZ')
        self.assertEqual(marca.slug, 'marca-de-teste-xyz')

        marca_especial = Marca.objects.create(nome='Minha Marca & Cia')
        self.assertEqual(marca_especial.slug, 'minha-marca-cia')

    def test_marca_slug_is_not_regenerated_on_update(self):
        """
        Verifica que o slug não é regenerado ao atualizar a marca se ele já existe.
        """
        marca = Marca.objects.create(nome='Marca Original')
        original_slug = marca.slug
        self.assertEqual(original_slug, 'marca-original')

        # Atualiza outro campo, o slug não deve mudar
        marca.nome = 'Marca Original Atualizada' # Nome pode ser atualizado, mas o slug permanece se já existe
        marca.save()
        self.assertEqual(marca.slug, original_slug) # Slug deve ser o mesmo

    def test_marca_str_representation(self):
        """
        Verifica a representação __str__ do modelo Marca.
        """
        marca = Marca.objects.create(nome='Samsung')
        self.assertEqual(str(marca), 'Samsung')

class ProdutoModelTest(TestCase):
    """
    Testes para o modelo Produto.
    """

    def setUp(self):
        """
        Configurações iniciais para os testes de Produto.
        """
        self.categoria = Categoria.objects.create(nome='Eletrônicos')
        self.marca = Marca.objects.create(nome='LG') 
        self.produto_data = {
            'nome': 'Smart TV 50',
            'categoria': self.categoria,
            'marca': self.marca,
            'quantidade': 10,
            'preco_compra': Decimal('1500.00'),
            'preco_venda': Decimal('2000.00'),
            'descricao': 'Uma smart TV de alta qualidade.',
            'desconto': 10, 
            'lancamento': True,
            'destaque': False,
        }

    def test_produto_creation(self):
        """
        Verifica se um produto pode ser criado com sucesso.
        """
        produto = Produto.objects.create(**self.produto_data)
        self.assertEqual(produto.nome, 'Smart TV 50')
        self.assertEqual(produto.categoria, self.categoria)
        self.assertEqual(produto.marca, self.marca)
        self.assertEqual(produto.quantidade, 10)
        self.assertEqual(produto.preco_venda, Decimal('2000.00'))
        self.assertEqual(produto.preco_compra, Decimal('1500.00'))
        self.assertEqual(produto.desconto, 10)
        self.assertEqual(produto.lancamento, True)
        self.assertEqual(produto.destaque, False)
        self.assertIsNotNone(produto.data_lancamento) 
        self.assertTrue(Produto.objects.filter(nome='Smart TV 50').exists())

    def test_produto_slug_generation_and_uniqueness(self):
        """
        Verifica a geração e unicidade do slug do produto.
        """
        # Teste de geração de slug automático
        produto1 = Produto.objects.create(nome='Produto Teste', categoria=self.categoria, preco_venda=Decimal('100.00'), preco_compra=Decimal('50.00'))
        self.assertEqual(produto1.slug, 'produto-teste')

        # Teste de unicidade de slug
        produto2 = Produto.objects.create(nome='Produto Teste', categoria=self.categoria, preco_venda=Decimal('100.00'), preco_compra=Decimal('50.00'))
        self.assertEqual(produto2.slug, 'produto-teste-1')

        produto3 = Produto.objects.create(nome='Produto Teste', categoria=self.categoria, preco_venda=Decimal('100.00'), preco_compra=Decimal('50.00'))
        self.assertEqual(produto3.slug, 'produto-teste-2')

        # Teste de atualização com novo nome. O slug não deve mudar pois já foi gerado na criação
        # e a sua lógica 'if not self.slug' impede a regeração.
        produto4 = Produto.objects.create(nome='Outro Produto', categoria=self.categoria, preco_venda=Decimal('100.00'), preco_compra=Decimal('50.00'))
        original_slug_p4 = produto4.slug
        
        produto4.nome = 'Outro Produto Novo'
        produto4.save()
        
        self.assertEqual(produto4.slug, original_slug_p4) 
        self.assertEqual(produto4.slug, 'outro-produto') 

    def test_produto_slug_on_update(self):
        """
        Verifica se o slug é mantido no update se já existe.
        Este teste reforça o comportamento do 'save' que só gera slug se 'not self.slug'.
        """
        produto = Produto.objects.create(
            nome='Produto Atualizacao', 
            categoria=self.categoria, 
            preco_venda=Decimal('100.00'), 
            preco_compra=Decimal('50.00')
        )
        self.assertEqual(produto.slug, 'produto-atualizacao')

        # Atualiza apenas um campo (quantidade), slug não deve mudar
        produto.quantidade = 20
        produto.save()
        self.assertEqual(produto.slug, 'produto-atualizacao')

        # Altera o nome, mas o slug já existe, então não deve mudar pela sua lógica atual
        produto.nome = 'Novo Nome do Produto'
        produto.save()
        self.assertEqual(produto.slug, 'produto-atualizacao') 

    def test_preco_desconto_property(self):
        """
        Verifica o cálculo da propriedade precoDesconto.
        """
        produto_sem_desconto = Produto.objects.create(
            nome='Produto Sem Desconto', categoria=self.categoria, preco_venda=Decimal('100.00'), preco_compra=Decimal('50.00'), desconto=0
        )
        self.assertEqual(produto_sem_desconto.precoDesconto, Decimal('100.00'))

        produto_com_desconto = Produto.objects.create(
            nome='Produto Com Desconto', categoria=self.categoria, preco_venda=Decimal('200.00'), preco_compra=Decimal('100.00'), desconto=25
        )
        self.assertEqual(produto_com_desconto.precoDesconto, Decimal('150.00'))
        
        # Teste com desconto de 100%
        produto_100_desconto = Produto.objects.create(
            nome='Produto 100 Desconto', categoria=self.categoria, preco_venda=Decimal('50.00'), preco_compra=Decimal('20.00'), desconto=100
        )
        self.assertEqual(produto_100_desconto.precoDesconto, Decimal('0.00'))

    def test_lucro_property(self):
        """
        Verifica o cálculo da propriedade lucro.
        """
        produto = Produto.objects.create(
            nome='Produto Lucro', categoria=self.categoria, preco_venda=Decimal('100.00'), preco_compra=Decimal('50.00'), desconto=0
        )
        self.assertEqual(produto.lucro, Decimal('50.00'))

        produto2 = Produto.objects.create(
            nome='Produto Lucro Zero', categoria=self.categoria, preco_venda=Decimal('100.00'), preco_compra=Decimal('100.00'), desconto=0
        )
        self.assertEqual(produto2.lucro, Decimal('0.00'))

        produto3 = Produto.objects.create(
            nome='Produto Prejuízo', categoria=self.categoria, preco_venda=Decimal('50.00'), preco_compra=Decimal('100.00'), desconto=0
        )
        self.assertEqual(produto3.lucro, Decimal('-50.00'))


    def test_lucro_desconto_property(self):
        """
        Verifica o cálculo da propriedade lucroDesconto.
        """
        produto = Produto.objects.create(
            nome='Produto Lucro Desconto', categoria=self.categoria, preco_venda=Decimal('200.00'), preco_compra=Decimal('100.00'), desconto=25
        )
        self.assertEqual(produto.lucroDesconto, Decimal('50.00'))

        produto2 = Produto.objects.create(
            nome='Produto Lucro Sem Desconto', categoria=self.categoria, preco_venda=Decimal('100.00'), preco_compra=Decimal('50.00'), desconto=0
        )
        self.assertEqual(produto2.lucroDesconto, Decimal('50.00'))
        self.assertEqual(produto2.lucroDesconto, produto2.lucro)

        produto3 = Produto.objects.create(
            nome='Produto Lucro 100 Desconto', categoria=self.categoria, preco_venda=Decimal('50.00'), preco_compra=Decimal('20.00'), desconto=100
        )
        self.assertEqual(produto3.lucroDesconto, Decimal('-20.00'))

    def test_produto_str_representation(self):
        """
        Verifica a representação __str__ do modelo Produto.
        """
        produto = Produto.objects.create(nome='Celular XYZ', categoria=self.categoria, preco_venda=Decimal('1000.00'), preco_compra=Decimal('500.00'))
        self.assertEqual(str(produto), 'Celular XYZ')

    def test_produto_with_null_brand(self):
        """
        Verifica se um produto pode ser criado sem marca.
        """
        produto = Produto.objects.create(
            nome='Produto Sem Marca', categoria=self.categoria, preco_venda=Decimal('100.00'), preco_compra=Decimal('50.00'), marca=None
        )
        self.assertIsNone(produto.marca)
        self.assertEqual(produto.nome, 'Produto Sem Marca')

class ProdutoImagemModelTest(TestCase):
    """
    Testes para o modelo ProdutoImagem.
    """

    def setUp(self):
        self.categoria = Categoria.objects.create(nome='Acessórios')
        self.produto = Produto.objects.create(
            nome='Fone de Ouvido', categoria=self.categoria, preco_venda=Decimal('150.00'), preco_compra=Decimal('75.00')
        )
        self.upload_dir = 'produtos_fotos'
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    def tearDown(self):
        # Para testes, o sistema de arquivos temporário do Django é mais seguro
        # e geralmente não requer remoção manual de diretórios.
        # Se você estiver realmente criando arquivos no disco durante o teste,
        # considere usar `shutil.rmtree(self.upload_dir)` com cautela.
        pass 


    def test_produto_imagem_creation(self):
        """
        Verifica se uma imagem de produto pode ser criada e associada.
        """
        imagem = ProdutoImagem.objects.create(
            produto=self.produto, 
            imagem='produtos_fotos/fone_teste.jpg', 
            descricao='Imagem principal do fone'
        )
        self.assertEqual(imagem.produto, self.produto)
        self.assertEqual(imagem.descricao, 'Imagem principal do fone')
        self.assertEqual(imagem.imagem.name, 'produtos_fotos/fone_teste.jpg') 

    def test_produto_imagem_str_representation(self):
        """
        Verifica a representação __str__ do modelo ProdutoImagem.
        """
        imagem = ProdutoImagem.objects.create(
            produto=self.produto, 
            imagem='produtos_fotos/fone_teste.jpg'
        )
        self.assertEqual(str(imagem), f"Imagem de {self.produto.nome}")

    def test_produto_imagem_related_name(self):
        """
        Verifica o related_name 'imagens_extra' no Produto.
        """
        imagem1 = ProdutoImagem.objects.create(produto=self.produto, imagem='produtos_fotos/img1.jpg')
        imagem2 = ProdutoImagem.objects.create(produto=self.produto, imagem='produtos_fotos/img2.jpg')

        self.assertIn(imagem1, self.produto.imagens_extra.all())
        self.assertIn(imagem2, self.produto.imagens_extra.all())
        self.assertEqual(self.produto.imagens_extra.count(), 2)


## Testes para as Views (Django e DRF)

class BasicProductViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.categoria_eletronicos = Categoria.objects.create(nome='Eletrônicos')
        self.categoria_roupas = Categoria.objects.create(nome='Roupas')
        self.marca_samsung = Marca.objects.create(nome='Samsung')
        self.marca_apple = Marca.objects.create(nome='Apple')
        
        self.marca_nike, created = Marca.objects.get_or_create(nome='Nike') 
        
        # Definindo uma data fixa para consistência dos testes de lançamento
        self.fixed_test_date = datetime(2025, 7, 1, 10, 0, 0, tzinfo=pytz.utc)
        
        # Mocking timezone.now() para retornar a data fixa durante os testes
        self.patcher = unittest.mock.patch('django.utils.timezone.now', return_value=self.fixed_test_date)
        self.mock_now = self.patcher.start()

        self.produto1 = Produto.objects.create(
            nome='Smart TV Ultra HD',
            categoria=self.categoria_eletronicos,
            marca=self.marca_samsung,
            quantidade=5,
            preco_compra=Decimal('1000.00'),
            preco_venda=Decimal('1500.00'),
            destaque=True,
            desconto=0,
            lancamento=False, # Este não será um lançamento se o filtro for por `lancamento=True`
            data_lancamento=self.fixed_test_date - timedelta(days=5) 
        )
        self.produto2 = Produto.objects.create(
            nome='Celular XYZ',
            categoria=self.categoria_eletronicos,
            marca=self.marca_apple,
            quantidade=10,
            preco_compra=Decimal('500.00'),
            preco_venda=Decimal('800.00'),
            destaque=False,
            desconto=10, 
            lancamento=True, # ESTE é o único lançamento pelo campo booleano
            data_lancamento=self.fixed_test_date - timedelta(days=15) 
        )
        self.produto3 = Produto.objects.create(
            nome='Camiseta Esportiva',
            categoria=self.categoria_roupas,
            marca=self.marca_nike,
            quantidade=20,
            preco_compra=Decimal('20.00'),
            preco_venda=Decimal('50.00'),
            destaque=False,
            desconto=0,
            lancamento=False, # Este não será um lançamento pelo campo booleano
            data_lancamento=self.fixed_test_date - timedelta(days=29) 
        )
        self.produto_antigo = Produto.objects.create(
            nome='Notebook Velho',
            categoria=self.categoria_eletronicos,
            marca=self.marca_samsung,
            quantidade=1,
            preco_compra=Decimal('100.00'),
            preco_venda=Decimal('200.00'),
            destaque=False,
            desconto=0,
            lancamento=False, # Este não será um lançamento pelo campo booleano
            data_lancamento=self.fixed_test_date - timedelta(days=31) 
        )

    def tearDown(self):
        self.patcher.stop()

    def test_home_view(self):
        """
        Testa a view 'home' e o contexto que ela passa para o template.
        """
        response = self.client.get(reverse('product:home')) 
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

        self.assertIn('produtos', response.context)
        self.assertIn('produtoDestaque', response.context)
        self.assertIn('produtoDesconto', response.context)
        self.assertIn('lancamento', response.context)

        # Verifica 'produtos': todos os produtos criados devem estar presentes
        self.assertIn(self.produto1, response.context['produtos'])
        self.assertIn(self.produto2, response.context['produtos'])
        self.assertIn(self.produto3, response.context['produtos'])
        self.assertIn(self.produto_antigo, response.context['produtos']) 
        self.assertEqual(response.context['produtos'].count(), 4)

        # Verifica 'produtoDestaque'
        self.assertIn(self.produto1, response.context['produtoDestaque']) 
        self.assertNotIn(self.produto2, response.context['produtoDestaque'])
        self.assertEqual(response.context['produtoDestaque'].count(), 1) 

        # Verifica 'produtoDesconto'
        self.assertIn(self.produto2, response.context['produtoDesconto']) 
        self.assertNotIn(self.produto1, response.context['produtoDesconto'])
        self.assertEqual(response.context['produtoDesconto'].count(), 1)

        # MODIFICAÇÃO AQUI: Agora espera 1 lançamento se a view filtra por 'lancamento=True'
        self.assertEqual(response.context['lancamento'].count(), 1) 
        self.assertIn(self.produto2, response.context['lancamento']) 
        self.assertNotIn(self.produto1, response.context['lancamento'])
        self.assertNotIn(self.produto3, response.context['lancamento']) 
        self.assertNotIn(self.produto_antigo, response.context['lancamento']) 

    def test_produto_detail_view_success(self):
        """
        Testa a view 'produto' com um slug existente.
        """
        response = self.client.get(reverse('product:produto', args=[self.produto1.slug]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'productmain.html')
        self.assertIn('produtos', response.context)
        self.assertEqual(response.context['produtos'], self.produto1)
        self.assertContains(response, self.produto1.nome)

    def test_produto_detail_view_not_found(self):
        """
        Testa a view 'produto' com um slug que não existe.
        """
        response = self.client.get(reverse('product:produto', args=['slug-inexistente']))
        self.assertEqual(response.status_code, 404)


## Testes para APIs (REST Framework)

class ProductAPIViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.categoria_api = Categoria.objects.create(nome='API Categorias')
        self.marca_api = Marca.objects.create(nome='API Marcas')
        self.produto_api_1 = Produto.objects.create(
            nome='Produto API 1',
            categoria=self.categoria_api,
            marca=self.marca_api,
            preco_venda=Decimal('100.00'),
            preco_compra=Decimal('50.00')
        )
        self.produto_api_2 = Produto.objects.create(
            nome='Outro Produto API',
            categoria=self.categoria_api,
            marca=self.marca_api,
            preco_venda=Decimal('200.00'),
            preco_compra=Decimal('100.00')
        )
        self.produto_api_3 = Produto.objects.create(
            nome='Produto API Diferente',
            categoria=self.categoria_api,
            marca=Marca.objects.create(nome='Outra Marca API'),
            preco_venda=Decimal('50.00'),
            preco_compra=Decimal('25.00')
        )

        # Usando os nomes de URL de API corretos do seu urls.py
        self.busca_url = reverse('product:api_busca_produtos') 
        self.produto_list_api_url = reverse('product:api_lista_produtos')
        self.produto_detail_api_url = reverse('product:api_detalhe_produto', args=[self.produto_api_1.slug])
        self.categoria_list_api_url = reverse('product:api_lista_categorias')
        self.marca_list_api_url = reverse('product:api_lista_marcas')

    def test_busca_produtos_api_no_params(self):
        """
        Testa a API de busca sem parâmetros, deve retornar todos os produtos.
        """
        response = self.client.get(self.busca_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('produtos', data)
        self.assertEqual(len(data['produtos']), 3)

    def test_busca_produtos_api_query(self):
        """
        Testa a busca por termo 'q'.
        """
        response = self.client.get(f'{self.busca_url}?q=API 1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['produtos']), 1)
        self.assertEqual(data['produtos'][0]['nome'], self.produto_api_1.nome)

    def test_busca_produtos_api_categoria_id(self):
        """
        Testa a busca por categoria_id.
        """
        response = self.client.get(f'{self.busca_url}?categoria_id={self.categoria_api.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['produtos']), 3)

    def test_busca_produtos_api_categoria_slug(self):
        """
        Testa a busca por categoria_slug.
        """
        response = self.client.get(f'{self.busca_url}?categoria_slug={self.categoria_api.slug}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['produtos']), 3)

    def test_busca_produtos_api_marca_id(self):
        """
        Testa a busca por marca_id.
        """
        response = self.client.get(f'{self.busca_url}?marca_id={self.marca_api.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['produtos']), 2)
        self.assertIn(self.produto_api_1.nome, [p['nome'] for p in data['produtos']])
        self.assertIn(self.produto_api_2.nome, [p['nome'] for p in data['produtos']])
        self.assertNotIn(self.produto_api_3.nome, [p['nome'] for p in data['produtos']])

    def test_busca_produtos_api_marca_slug(self):
        """
        Testa a busca por marca_slug.
        """
        response = self.client.get(f'{self.busca_url}?marca_slug={self.marca_api.slug}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['produtos']), 2)

    def test_busca_produtos_api_combination(self):
        """
        Testa a busca com combinação de query e filtro.
        """
        response = self.client.get(f'{self.busca_url}?q=Produto API&marca_id={self.marca_api.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['produtos']), 2)

    def test_produto_list_api_view(self):
        """
        Testa a listagem de produtos da API.
        """
        response = self.client.get(self.produto_list_api_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), Produto.objects.count()) 
        self.assertIn(self.produto_api_1.nome, [p['nome'] for p in data])

    def test_produto_detail_api_view_success(self):
        """
        Testa o detalhe de produto da API com um slug existente.
        """
        response = self.client.get(self.produto_detail_api_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['nome'], self.produto_api_1.nome)
        self.assertEqual(data['slug'], self.produto_api_1.slug)

    def test_produto_detail_api_view_not_found(self):
        """
        Testa o detalhe de produto da API com um slug inexistente.
        """
        response = self.client.get(reverse('product:api_detalhe_produto', args=['slug-nao-existe']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_categoria_list_api_view(self):
        """
        Testa a listagem de categorias da API.
        """
        response = self.client.get(self.categoria_list_api_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), Categoria.objects.count())
        self.assertIn(self.categoria_api.nome, [c['nome'] for c in data])

    def test_marca_list_api_view(self):
        """
        Testa a listagem de marcas da API.
        """
        response = self.client.get(self.marca_list_api_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), Marca.objects.count())
        self.assertIn(self.marca_api.nome, [m['nome'] for m in data])