from django.db import models
from django.contrib.auth.models import User # Importa o modelo de usuário padrão do Django
from django.db.models.signals import post_save # Usado para criar o Profile automaticamente
from django.dispatch import receiver # Usado para o decorator do signal

class Profile(models.Model):
    # Relação OneToOne com o modelo User padrão.
    # Quando um User é deletado, o Profile associado também é deletado.
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Campos adicionais para o seu perfil de usuário
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")

    # Endereço padrão para envio (opcional, pode ser preenchido no perfil ou no checkout)
    endereco_padrao = models.CharField(max_length=255, blank=True, null=True, verbose_name="Endereço Padrão")
    cidade_padrao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade Padrão")
    estado_padrao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Estado Padrão")
    cep_padrao = models.CharField(max_length=10, blank=True, null=True, verbose_name="CEP Padrão")

    # Outros campos que você pode querer adicionar:
    # data_nascimento = models.DateField(blank=True, null=True, verbose_name="Data de Nascimento")
    # foto_perfil = models.ImageField(upload_to='profile_pics/', blank=True, null=True, verbose_name="Foto de Perfil")
    # ...

    def __str__(self):
        return f'Perfil de {self.user.username}'

# --- Signals para criar e salvar o Profile automaticamente ---
# Este receiver garante que um objeto Profile seja criado automaticamente
# sempre que um novo User for criado.
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# Este receiver garante que o Profile seja salvo sempre que o User for salvo.
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()