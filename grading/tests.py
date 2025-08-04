from django.test import TestCase
from grading.views import volcengine_score_homework

class TestVolcengineScoreHomework(TestCase):
    def test_normal(self):
        content = "这是一篇测试作文，内容充实，结构完整。"
        score, comment = volcengine_score_homework(content)
        self.assertTrue(isinstance(score, int) or score is None)
        self.assertIsInstance(comment, str)

    def test_empty(self):
        content = ""
        score, comment = volcengine_score_homework(content)
        self.assertTrue(isinstance(score, int) or score is None)
        self.assertIsInstance(comment, str)

    def test_long_content(self):
        content = "测试内容" * 10000
        score, comment = volcengine_score_homework(content)
        self.assertTrue(isinstance(score, int) or score is None)
        self.assertIsInstance(comment, str)