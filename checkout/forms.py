# checkout/forms.py

from django import forms

class CheckoutForm(forms.Form):
    nome_completo = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'placeholder': 'Seu nome completo'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Seu e-mail'}))
    telefone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'placeholder': 'Telefone (opcional)'}))
    endereco = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'placeholder': 'Endereço completo'}))
    cidade = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Cidade'}))
    estado = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Estado'}))
    cep = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'placeholder': 'CEP'}))

    # Você pode adicionar campos de pagamento aqui ou em um formulário separado
    # metodo_pagamento = forms.ChoiceField(choices=[('Cartao', 'Cartão de Crédito'), ('Boleto', 'Boleto')], widget=forms.RadioSelect)