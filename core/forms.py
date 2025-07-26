from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={"autofocus": True, "class": "form-control"}),
        help_text="Obrigatório. Máximo 10 caracteres.",
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        max_length=8,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "class": "form-control"}),
        help_text="Obrigatório. Máximo 8 caracteres.",
    )


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(max_length=10, help_text="Obrigatório. Máximo 10 caracteres.")
    password1 = forms.CharField(
        label="Senha",
        strip=False,
        max_length=8,
        widget=forms.PasswordInput,
        help_text="Obrigatório. Máximo 8 caracteres.",
    )
    password2 = forms.CharField(
        label="Confirmação de senha",
        strip=False,
        max_length=8,
        widget=forms.PasswordInput,
        help_text="Digite a mesma senha novamente.",
    )

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if len(username) > 10:
            raise ValidationError("O nome de usuário deve ter no máximo 10 caracteres.")
        return username

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if len(password1) > 8:
            raise ValidationError("A senha deve ter no máximo 8 caracteres.")
        return password1

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = UserCreationForm.Meta.fields
