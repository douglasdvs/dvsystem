from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        max_length=8,
        widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'}),
        help_text='Obrigatório. 8 caracteres ou menos. Letras, números e @/./+/-/_ apenas.'
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control'}),
        help_text='Obrigatório. 8 caracteres ou menos. Letras, números e @/./+/-/_ apenas.'
    )

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = UserCreationForm.Meta.fields
