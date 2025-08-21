from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save 
from django.dispatch import receiver 


# PERFIL DO USUÁRIO
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    endereco_padrao = models.CharField(max_length=255, blank=True, null=True, verbose_name="Endereço Padrão")
    cidade_padrao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade Padrão")
    estado_padrao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Estado Padrão")
    cep_padrao = models.CharField(max_length=10, blank=True, null=True, verbose_name="CEP Padrão")
    email_verificado = models.BooleanField(default=False)

    def __str__(self):
        return f'Perfil de {self.user.username}'


# CRIAR E SALVAR USUÁRIO
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# GARANTIA PARA SALVAR
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()