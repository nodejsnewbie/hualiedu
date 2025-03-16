from django import forms
from django.forms.widgets import FileInput
from pathlib import Path

class SSHKeyFileInput(FileInput):
    def __init__(self, attrs=None):
        default_attrs = {
            'accept': '.pem,.key',
            'data-initial-path': str(Path.home() / '.ssh')  # 设置初始路径为 ~/.ssh
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    class Media:
        js = ('grading/js/ssh_key_input.js',)

class GlobalConfigForm(forms.ModelForm):
    class Meta:
        from .models import GlobalConfig
        model = GlobalConfig
        fields = '__all__'
        widgets = {
            'ssh_key_file': SSHKeyFileInput(),
            'https_password': forms.PasswordInput(render_value=True),
        }

    def clean(self):
        cleaned_data = super().clean()
        ssh_key = cleaned_data.get('ssh_key')
        ssh_key_file = cleaned_data.get('ssh_key_file')

        if ssh_key and ssh_key_file:
            raise forms.ValidationError('请只使用一种方式提供SSH私钥（文本输入或文件上传）')
        
        return cleaned_data 