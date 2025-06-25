from django import forms
from .models import ConfiguracaoSistema, PermissaoUsuario, LogConfig
from django.contrib.auth import get_user_model

User = get_user_model()

class ConfiguracaoSistemaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoSistema
        fields = '__all__'
        widgets = {
            'nome_sistema': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao_sistema': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'versao_sistema': forms.TextInput(attrs={'class': 'form-control'}),
            'host_banco': forms.TextInput(attrs={'class': 'form-control'}),
            'porta_banco': forms.NumberInput(attrs={'class': 'form-control'}),
            'nome_banco': forms.TextInput(attrs={'class': 'form-control'}),
            'usuario_banco': forms.TextInput(attrs={'class': 'form-control'}),
            'senha_banco': forms.PasswordInput(attrs={'class': 'form-control'}),
            'host_email': forms.TextInput(attrs={'class': 'form-control'}),
            'porta_email': forms.NumberInput(attrs={'class': 'form-control'}),
            'usuario_email': forms.TextInput(attrs={'class': 'form-control'}),
            'senha_email': forms.PasswordInput(attrs={'class': 'form-control'}),
            'usar_tls': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tempo_sessao': forms.NumberInput(attrs={'class': 'form-control'}),
            'tentativas_login': forms.NumberInput(attrs={'class': 'form-control'}),
            'tempo_bloqueio': forms.NumberInput(attrs={'class': 'form-control'}),
            'requer_senha_forte': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class PermissoesUsuarioForm(forms.ModelForm):
    class Meta:
        model = PermissaoUsuario
        fields = '__all__'
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-control select2'}),
            'pode_gerenciar_usuarios': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pode_gerenciar_permissoes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pode_gerenciar_configuracoes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pode_gerenciar_logs': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pode_gerenciar_backup': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class LogConfigForm(forms.ModelForm):
    class Meta:
        model = LogConfig
        fields = '__all__'
        widgets = {
            'ativar_logs': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'nivel_log': forms.Select(attrs={'class': 'form-control select2'}),
            'formato_log': forms.Select(attrs={'class': 'form-control select2'}),
            'diretorio_log': forms.TextInput(attrs={'class': 'form-control'}),
            'manter_logs': forms.Select(attrs={'class': 'form-control select2'}),
            'log_acesso': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'log_erro': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'log_seguranca': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'log_auditoria': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'log_desempenho': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notificar_erro': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notificar_seguranca': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notificar_desempenho': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_notificacao': forms.EmailInput(attrs={'class': 'form-control'})
        } 