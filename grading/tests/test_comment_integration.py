"""
测试评价缓存和模板集成功能

需求: 5.1.1-5.1.8, 5.2.1-5.2.12
"""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from grading.models import Tenant, UserProfile, CommentTemplate


class CommentIntegrationTestCase(TestCase):
    """测试评价缓存和模板在评价功能中的集成"""

    def setUp(self):
        """设置测试环境"""
        # 创建租户
        self.tenant = Tenant.objects.create(
            name="测试学校",
            description="测试租户"
        )

        # 创建教师用户
        self.teacher = User.objects.create_user(
            username='teacher1',
            password='password123',
            email='teacher1@test.edu.cn'
        )

        # 创建用户配置
        self.teacher_profile = UserProfile.objects.create(
            user=self.teacher,
            tenant=self.tenant
        )

        # 创建客户端并登录
        self.client = Client()
        self.client.login(username='teacher1', password='password123')

        # 创建一些评价模板
        self.personal_template1 = CommentTemplate.objects.create(
            tenant=self.tenant,
            teacher=self.teacher,
            template_type='personal',
            comment_text='作业完成质量很高，继续保持',
            usage_count=10
        )

        self.personal_template2 = CommentTemplate.objects.create(
            tenant=self.tenant,
            teacher=self.teacher,
            template_type='personal',
            comment_text='需要注意代码规范',
            usage_count=8
        )

        self.system_template = CommentTemplate.objects.create(
            tenant=self.tenant,
            teacher=None,
            template_type='system',
            comment_text='按时完成作业',
            usage_count=50
        )

    def test_get_recommended_templates_api(self):
        """测试获取推荐评价模板API"""
        response = self.client.get('/grading/api/comment-templates/recommended/')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data['success'])
        self.assertIn('templates', data)
        self.assertGreater(len(data['templates']), 0)

        # 验证个人模板优先
        templates = data['templates']
        personal_count = sum(1 for t in templates if t['template_type'] == 'personal')
        self.assertGreater(personal_count, 0)

        # 验证模板包含必要字段
        first_template = templates[0]
        self.assertIn('id', first_template)
        self.assertIn('comment_text', first_template)
        self.assertIn('usage_count', first_template)
        self.assertIn('template_type', first_template)
        self.assertIn('template_type_display', first_template)

    def test_record_comment_usage_api(self):
        """测试记录评价使用次数API"""
        comment_text = '作业完成质量很高，继续保持'

        # 获取初始使用次数
        initial_count = self.personal_template1.usage_count

        # 记录使用
        response = self.client.post(
            '/grading/api/comment-templates/record-usage/',
            data=json.dumps({'comment_text': comment_text}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data['success'])
        self.assertIn('template', data)

        # 验证使用次数增加
        self.personal_template1.refresh_from_db()
        self.assertEqual(self.personal_template1.usage_count, initial_count + 1)

    def test_record_new_comment_usage(self):
        """测试记录新评价的使用次数"""
        new_comment = '这是一个全新的评价内容'

        # 确认评价不存在
        self.assertFalse(
            CommentTemplate.objects.filter(
                tenant=self.tenant,
                teacher=self.teacher,
                comment_text=new_comment
            ).exists()
        )

        # 记录使用
        response = self.client.post(
            '/grading/api/comment-templates/record-usage/',
            data=json.dumps({'comment_text': new_comment}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data['success'])

        # 验证创建了新模板
        new_template = CommentTemplate.objects.get(
            tenant=self.tenant,
            teacher=self.teacher,
            comment_text=new_comment
        )
        self.assertEqual(new_template.usage_count, 1)
        self.assertEqual(new_template.template_type, 'personal')

    def test_template_ranking_after_usage(self):
        """测试使用后模板排序更新"""
        # 记录使用次数较少的模板
        response = self.client.post(
            '/grading/api/comment-templates/record-usage/',
            data=json.dumps({'comment_text': self.personal_template2.comment_text}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        # 多次记录使用，使其超过template1
        for _ in range(5):
            self.client.post(
                '/grading/api/comment-templates/record-usage/',
                data=json.dumps({'comment_text': self.personal_template2.comment_text}),
                content_type='application/json'
            )

        # 获取推荐模板
        response = self.client.get('/grading/api/comment-templates/recommended/')
        data = json.loads(response.content)

        templates = data['templates']
        personal_templates = [t for t in templates if t['template_type'] == 'personal']

        # 验证排序：template2应该在template1之前
        if len(personal_templates) >= 2:
            self.assertGreater(
                personal_templates[0]['usage_count'],
                personal_templates[1]['usage_count']
            )

    def test_personal_templates_limit(self):
        """测试个人模板数量限制（最多5个）"""
        # 创建6个个人模板
        for i in range(6):
            CommentTemplate.objects.create(
                tenant=self.tenant,
                teacher=self.teacher,
                template_type='personal',
                comment_text=f'个人评价模板{i}',
                usage_count=i
            )

        # 获取推荐模板
        response = self.client.get('/grading/api/comment-templates/recommended/')
        data = json.loads(response.content)

        templates = data['templates']
        personal_templates = [t for t in templates if t['template_type'] == 'personal']

        # 验证最多返回5个个人模板
        self.assertLessEqual(len(personal_templates), 5)

    def test_system_templates_fill_gap(self):
        """测试系统模板补充到5个"""
        # 删除一些个人模板，只保留2个
        CommentTemplate.objects.filter(
            tenant=self.tenant,
            teacher=self.teacher
        ).exclude(id=self.personal_template1.id).delete()

        # 创建更多系统模板
        for i in range(5):
            CommentTemplate.objects.create(
                tenant=self.tenant,
                teacher=None,
                template_type='system',
                comment_text=f'系统评价模板{i}',
                usage_count=40 - i
            )

        # 获取推荐模板
        response = self.client.get('/grading/api/comment-templates/recommended/')
        data = json.loads(response.content)

        templates = data['templates']
        personal_templates = [t for t in templates if t['template_type'] == 'personal']
        system_templates = [t for t in templates if t['template_type'] == 'system']

        # 验证个人模板数量
        self.assertEqual(len(personal_templates), 1)

        # 验证系统模板补充
        self.assertGreater(len(system_templates), 0)

        # 验证总数不超过5个
        self.assertLessEqual(len(templates), 5)

    def test_comment_deduplication(self):
        """测试评价内容去重"""
        comment_text = '作业完成质量很高，继续保持'

        # 多次记录相同评价
        for _ in range(3):
            response = self.client.post(
                '/grading/api/comment-templates/record-usage/',
                data=json.dumps({'comment_text': comment_text}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)

        # 验证只有一个模板，但使用次数累加
        templates = CommentTemplate.objects.filter(
            tenant=self.tenant,
            teacher=self.teacher,
            comment_text=comment_text
        )

        self.assertEqual(templates.count(), 1)
        # 初始10次 + 新增3次 = 13次
        self.assertEqual(templates.first().usage_count, 13)

    def test_unauthorized_access(self):
        """测试未授权访问"""
        # 登出
        self.client.logout()

        # 尝试获取推荐模板
        response = self.client.get('/grading/api/comment-templates/recommended/')
        # 应该重定向到登录页面
        self.assertEqual(response.status_code, 302)

        # 尝试记录使用
        response = self.client.post(
            '/grading/api/comment-templates/record-usage/',
            data=json.dumps({'comment_text': '测试'}),
            content_type='application/json'
        )
        # 应该重定向到登录页面
        self.assertEqual(response.status_code, 302)

    def test_empty_comment_text(self):
        """测试空评价内容"""
        response = self.client.post(
            '/grading/api/comment-templates/record-usage/',
            data=json.dumps({'comment_text': ''}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('message', data)

    def test_missing_comment_text(self):
        """测试缺少评价内容参数"""
        response = self.client.post(
            '/grading/api/comment-templates/record-usage/',
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('message', data)
