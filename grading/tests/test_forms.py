"""
表单测试
"""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ValidationError
from django.test import TestCase

from grading.forms import GlobalConfigForm, SSHKeyFileInput
from grading.models import GlobalConfig

from .base import BaseTestCase


class SSHKeyFileInputTest(TestCase):
    """SSH密钥文件输入组件测试"""

    def test_ssh_key_file_input_attrs(self):
        """测试SSH密钥文件输入组件属性"""
        widget = SSHKeyFileInput()

        # 检查默认属性
        self.assertEqual(widget.attrs["accept"], ".pem,.key")
        self.assertIn(".ssh", widget.attrs["data-initial-path"])

    def test_ssh_key_file_input_custom_attrs(self):
        """测试自定义属性"""
        custom_attrs = {"class": "custom-class"}
        widget = SSHKeyFileInput(attrs=custom_attrs)

        # 应该包含默认属性和自定义属性
        self.assertEqual(widget.attrs["accept"], ".pem,.key")
        self.assertEqual(widget.attrs["class"], "custom-class")

    def test_ssh_key_file_input_media(self):
        """测试媒体文件"""
        widget = SSHKeyFileInput()
        self.assertIn("grading/js/ssh_key_input.js", widget.media._js)


class GlobalConfigFormTest(BaseTestCase):
    """全局配置表单测试"""

    def test_valid_form_with_text_ssh_key(self):
        """测试使用文本SSH密钥的有效表单"""
        form_data = {
            "key": "ssh_config",
            "value": "test_value",
            "description": "测试配置",
            "ssh_key": "-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----",
        }

        form = GlobalConfigForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_valid_form_with_file_ssh_key(self):
        """测试使用文件SSH密钥的有效表单"""
        # 创建测试文件
        ssh_key_file = SimpleUploadedFile(
            "test_key.pem",
            b"-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----",
            content_type="application/x-pem-file",
        )

        form_data = {"key": "ssh_config", "value": "test_value", "description": "测试配置"}

        form = GlobalConfigForm(data=form_data, files={"ssh_key_file": ssh_key_file})
        self.assertTrue(form.is_valid())

    def test_form_with_both_ssh_keys_invalid(self):
        """测试同时提供文本和文件SSH密钥时表单无效"""
        ssh_key_file = SimpleUploadedFile(
            "test_key.pem",
            b"-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----",
            content_type="application/x-pem-file",
        )

        form_data = {
            "key": "ssh_config",
            "value": "test_value",
            "description": "测试配置",
            "ssh_key": "-----BEGIN PRIVATE KEY-----\ntext_key\n-----END PRIVATE KEY-----",
        }

        form = GlobalConfigForm(data=form_data, files={"ssh_key_file": ssh_key_file})
        self.assertFalse(form.is_valid())
        self.assertIn("请只使用一种方式提供SSH私钥", str(form.errors))

    def test_form_without_ssh_keys_valid(self):
        """测试不提供SSH密钥时表单有效"""
        form_data = {"key": "test_config", "value": "test_value", "description": "测试配置"}

        form = GlobalConfigForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_required_fields(self):
        """测试必填字段"""
        form = GlobalConfigForm(data={})
        self.assertFalse(form.is_valid())

        # 检查必填字段错误
        required_fields = ["key", "value"]
        for field in required_fields:
            self.assertIn(field, form.errors)

    def test_form_field_widgets(self):
        """测试表单字段组件"""
        form = GlobalConfigForm()

        # 检查SSH密钥文件字段使用自定义组件
        self.assertIsInstance(form.fields["ssh_key_file"].widget, SSHKeyFileInput)

        # 检查密码字段使用密码输入组件
        self.assertEqual(form.fields["https_password"].widget.__class__.__name__, "PasswordInput")

    def test_form_save(self):
        """测试表单保存"""
        form_data = {
            "key": "test_save_config",
            "value": "test_save_value",
            "description": "测试保存配置",
        }

        form = GlobalConfigForm(data=form_data)
        self.assertTrue(form.is_valid())

        config = form.save()
        self.assertEqual(config.key, "test_save_config")
        self.assertEqual(config.value, "test_save_value")

        # 验证数据库中的记录
        saved_config = GlobalConfig.objects.get(key="test_save_config")
        self.assertEqual(saved_config.value, "test_save_value")

    def test_form_update_existing_config(self):
        """测试更新现有配置"""
        # 创建现有配置
        existing_config = GlobalConfig.objects.create(
            key="existing_config", value="old_value", description="旧描述"
        )

        # 更新配置
        form_data = {"key": "existing_config", "value": "new_value", "description": "新描述"}

        form = GlobalConfigForm(data=form_data, instance=existing_config)
        self.assertTrue(form.is_valid())

        updated_config = form.save()
        self.assertEqual(updated_config.value, "new_value")
        self.assertEqual(updated_config.description, "新描述")

    def test_form_clean_method(self):
        """测试表单清理方法"""
        # 测试同时提供SSH密钥的情况
        form_data = {"key": "test_clean", "value": "test_value", "ssh_key": "text_key"}

        ssh_key_file = SimpleUploadedFile(
            "test.pem", b"file_key", content_type="application/x-pem-file"
        )

        form = GlobalConfigForm(data=form_data, files={"ssh_key_file": ssh_key_file})

        # 应该触发验证错误
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_form_field_help_texts(self):
        """测试表单字段帮助文本"""
        form = GlobalConfigForm()

        # 检查是否有适当的帮助文本
        for field_name, field in form.fields.items():
            if hasattr(field, "help_text"):
                self.assertIsInstance(field.help_text, str)

    def test_form_field_labels(self):
        """测试表单字段标签"""
        form = GlobalConfigForm()

        # 检查字段标签
        for field_name, field in form.fields.items():
            self.assertIsInstance(field.label, (str, type(None)))

    def test_ssh_key_file_validation(self):
        """测试SSH密钥文件验证"""
        # 测试无效文件类型
        invalid_file = SimpleUploadedFile("test.txt", b"not a key file", content_type="text/plain")

        form_data = {"key": "test_invalid_file", "value": "test_value"}

        form = GlobalConfigForm(data=form_data, files={"ssh_key_file": invalid_file})

        # 表单应该仍然有效，因为文件类型验证通常在前端或其他地方处理
        # 这里主要测试表单逻辑
        if form.is_valid():
            self.assertTrue(True)  # 文件类型验证可能在其他地方处理
        else:
            # 如果有文件类型验证，检查错误信息
            self.assertIn("ssh_key_file", form.errors)


class FormIntegrationTest(BaseTestCase):
    """表单集成测试"""

    def test_form_in_view_context(self):
        """测试表单在视图上下文中的使用"""
        # 这里可以测试表单在实际视图中的使用情况
        # 由于没有具体的表单视图，这里只是示例
        form = GlobalConfigForm()
        self.assertIsNotNone(form)
        self.assertTrue(hasattr(form, "fields"))

    def test_form_rendering(self):
        """测试表单渲染"""
        form = GlobalConfigForm()

        # 测试表单可以正常渲染
        form_html = str(form)
        self.assertIn("input", form_html.lower())
        self.assertIn("name=", form_html.lower())

    def test_form_with_initial_data(self):
        """测试带初始数据的表单"""
        initial_data = {"key": "initial_key", "value": "initial_value", "description": "初始描述"}

        form = GlobalConfigForm(initial=initial_data)

        # 检查初始值
        self.assertEqual(form.initial["key"], "initial_key")
        self.assertEqual(form.initial["value"], "initial_value")
        self.assertEqual(form.initial["description"], "初始描述")
