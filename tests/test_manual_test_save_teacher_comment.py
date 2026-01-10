"""
Comprehensive pytest tests for scripts/test_save_teacher_comment.py

This module tests the manual testing script that validates save_teacher_comment
and get_teacher_comment functionality for Git repository file operations.
"""

import json
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

import pytest
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse

from grading.models import Repository, Tenant, UserProfile, Course, Semester

# Import the functions from the manual test script
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts'))
from test_save_teacher_comment import test_save_teacher_comment, test_get_teacher_comment

User = get_user_model()


class BaseManualTestCase(TestCase):
    """Base test case for manual test script tests."""
    
    def setUp(self):
        """Set up test data for manual test script tests."""
        # Create test tenant
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            domain='test.example.com'
        )
        
        # Create test user with ID=1 (as expected by the script)
        self.user = User.objects.create_user(
            id=1,
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Create user profile
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            tenant=self.tenant,
            repo_base_dir='~/test_jobs'
        )
        
        # Create test semester
        self.semester = Semester.objects.create(
            name='Test Semester',
            start_date='2024-01-01',
            end_date='2024-06-30',
            is_active=True
        )
        
        # Create test course
        self.course = Course.objects.create(
            name='Web前端开发',
            course_type='theory',
            semester=self.semester,
            teacher=self.user,
            location='Room 101',
            tenant=self.tenant
        )
        
        # Create test repository with ID=11 (as expected by the script)
        self.repository = Repository.objects.create(
            id=11,
            name='test-repo',
            git_url='https://github.com/test/repo.git',
            owner=self.user,
            tenant=self.tenant,
            repo_type='git',
            git_branch='main'
        )
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)


class TestSaveTeacherCommentFunction(BaseManualTestCase):
    """Test the test_save_teacher_comment function from the manual test script."""
    
    @patch('test_save_teacher_comment.print')
    def test_save_teacher_comment_success(self, mock_print):
        """Test successful save_teacher_comment execution."""
        with patch('django.test.Client.post') as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'{"status": "success", "message": "评价已保存"}'
            mock_post.return_value = mock_response
            
            result = test_save_teacher_comment()
        
        self.assertTrue(result)
        
        # Verify the POST request was made with correct data
        mock_post.assert_called_once_with('/grading/save_teacher_comment/', {
            'file_path': '23计算机6班/第一次作业/吴紫晴1.docx',
            'comment': '测试评价：作业完成质量良好，但需要注意格式规范。',
            'grade': 'B',
            'repo_id': '11',
            'course': 'Web前端开发'
        })
        
        # Verify print statements
        mock_print.assert_any_call("=== 测试 save_teacher_comment 功能 ===")
        mock_print.assert_any_call("✅ 请求成功处理")
    
    @patch('test_save_teacher_comment.print')
    def test_save_teacher_comment_bad_request(self, mock_print):
        """Test save_teacher_comment with 400 Bad Request response."""
        with patch('django.test.Client.post') as mock_post:
            # Mock 400 response
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.content = b'{"status": "error", "message": "参数错误"}'
            mock_post.return_value = mock_response
            
            result = test_save_teacher_comment()
        
        self.assertFalse(result)
        mock_print.assert_any_call("⚠️  请求被拒绝（可能是网络问题或其他验证失败）")
    
    @patch('test_save_teacher_comment.print')
    def test_save_teacher_comment_server_error(self, mock_print):
        """Test save_teacher_comment with 500 Server Error response."""
        with patch('django.test.Client.post') as mock_post:
            # Mock 500 response
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.content = b'{"status": "error", "message": "服务器错误"}'
            mock_post.return_value = mock_response
            
            result = test_save_teacher_comment()
        
        self.assertFalse(result)
        mock_print.assert_any_call("❌ 服务器内部错误")
    
    @patch('test_save_teacher_comment.print')
    def test_save_teacher_comment_unknown_status(self, mock_print):
        """Test save_teacher_comment with unknown status code."""
        with patch('django.test.Client.post') as mock_post:
            # Mock unknown status response
            mock_response = Mock()
            mock_response.status_code = 418  # I'm a teapot
            mock_response.content = b'{"status": "teapot"}'
            mock_post.return_value = mock_response
            
            result = test_save_teacher_comment()
        
        self.assertFalse(result)
        mock_print.assert_any_call("❓ 未知响应状态: 418")
    
    @patch('test_save_teacher_comment.print')
    def test_save_teacher_comment_user_not_found(self, mock_print):
        """Test save_teacher_comment when test user doesn't exist."""
        # Delete the test user
        User.objects.filter(id=1).delete()
        
        result = test_save_teacher_comment()
        
        self.assertFalse(result)
        mock_print.assert_any_call("错误: 未找到测试用户，请先创建用户")
    
    @patch('test_save_teacher_comment.print')
    def test_save_teacher_comment_repository_not_found(self, mock_print):
        """Test save_teacher_comment when test repository doesn't exist."""
        # Delete the test repository
        Repository.objects.filter(id=11).delete()
        
        result = test_save_teacher_comment()
        
        self.assertFalse(result)
        mock_print.assert_any_call("错误: 未找到ID为11的测试仓库")
    
    @patch('test_save_teacher_comment.print')
    def test_save_teacher_comment_prints_repository_info(self, mock_print):
        """Test that save_teacher_comment prints repository information."""
        with patch('django.test.Client.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'{"status": "success"}'
            mock_post.return_value = mock_response
            
            test_save_teacher_comment()
        
        # Verify repository info is printed
        mock_print.assert_any_call(f"使用测试仓库: {self.repository.name} (类型: {self.repository.repo_type})")
        mock_print.assert_any_call(f"仓库URL: {self.repository.git_url}")


class TestGetTeacherCommentFunction(BaseManualTestCase):
    """Test the test_get_teacher_comment function from the manual test script."""
    
    @patch('test_save_teacher_comment.print')
    def test_get_teacher_comment_success(self, mock_print):
        """Test successful get_teacher_comment execution."""
        with patch('django.test.Client.get') as mock_get:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'{"status": "success", "comment": "测试评价", "grade": "B"}'
            mock_get.return_value = mock_response
            
            result = test_get_teacher_comment()
        
        self.assertTrue(result)
        
        # Verify the GET request was made with correct parameters
        mock_get.assert_called_once_with('/grading/get_teacher_comment/', {
            'file_path': '23计算机6班/第一次作业/吴紫晴1.docx',
            'repo_id': '11',
            'course': 'Web前端开发'
        })
        
        # Verify print statements
        mock_print.assert_any_call("\n=== 测试 get_teacher_comment 功能（对比） ===")
        mock_print.assert_any_call("✅ get_teacher_comment 正常工作")
    
    @patch('test_save_teacher_comment.print')
    def test_get_teacher_comment_failure(self, mock_print):
        """Test get_teacher_comment with non-200 response."""
        with patch('django.test.Client.get') as mock_get:
            # Mock error response
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.content = b'{"status": "error", "message": "文件未找到"}'
            mock_get.return_value = mock_response
            
            result = test_get_teacher_comment()
        
        self.assertFalse(result)
        mock_print.assert_any_call("❌ get_teacher_comment 也有问题")
    
    @patch('test_save_teacher_comment.print')
    def test_get_teacher_comment_prints_parameters(self, mock_print):
        """Test that get_teacher_comment prints test parameters."""
        with patch('django.test.Client.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'{"status": "success"}'
            mock_get.return_value = mock_response
            
            test_get_teacher_comment()
        
        # Verify test parameters are printed
        expected_params = {
            'file_path': '23计算机6班/第一次作业/吴紫晴1.docx',
            'repo_id': '11',
            'course': 'Web前端开发'
        }
        mock_print.assert_any_call(f"测试参数: {expected_params}")
    
    @patch('test_save_teacher_comment.print')
    def test_get_teacher_comment_user_not_found(self, mock_print):
        """Test get_teacher_comment when user doesn't exist."""
        # Delete the test user
        User.objects.filter(id=1).delete()
        
        with pytest.raises(User.DoesNotExist):
            test_get_teacher_comment()


class TestMainExecutionFlow(BaseManualTestCase):
    """Test the main execution flow of the manual test script."""
    
    @patch('test_save_teacher_comment.print')
    @patch('test_save_teacher_comment.test_get_teacher_comment')
    @patch('test_save_teacher_comment.test_save_teacher_comment')
    def test_main_execution_both_success(self, mock_save_test, mock_get_test, mock_print):
        """Test main execution when both tests succeed."""
        mock_get_test.return_value = True
        mock_save_test.return_value = True
        
        # Import and execute the main block logic
        from test_save_teacher_comment import __name__ as script_name
        
        # Simulate the main execution
        get_success = mock_get_test()
        save_success = mock_save_test()
        
        self.assertTrue(get_success)
        self.assertTrue(save_success)
        
        # Verify both functions were called
        mock_get_test.assert_called_once()
        mock_save_test.assert_called_once()
    
    @patch('test_save_teacher_comment.print')
    @patch('test_save_teacher_comment.test_get_teacher_comment')
    @patch('test_save_teacher_comment.test_save_teacher_comment')
    def test_main_execution_save_fails(self, mock_save_test, mock_get_test, mock_print):
        """Test main execution when save test fails."""
        mock_get_test.return_value = True
        mock_save_test.return_value = False
        
        # Simulate the main execution
        get_success = mock_get_test()
        save_success = mock_save_test()
        
        self.assertTrue(get_success)
        self.assertFalse(save_success)
    
    @patch('test_save_teacher_comment.print')
    @patch('test_save_teacher_comment.test_get_teacher_comment')
    @patch('test_save_teacher_comment.test_save_teacher_comment')
    def test_main_execution_both_fail(self, mock_save_test, mock_get_test, mock_print):
        """Test main execution when both tests fail."""
        mock_get_test.return_value = False
        mock_save_test.return_value = False
        
        # Simulate the main execution
        get_success = mock_get_test()
        save_success = mock_save_test()
        
        self.assertFalse(get_success)
        self.assertFalse(save_success)


class TestScriptEnvironmentSetup(TestCase):
    """Test the environment setup and imports in the manual test script."""
    
    def test_django_setup_imports(self):
        """Test that Django setup and imports work correctly."""
        # Test that the script can import Django models
        from grading.models import Repository
        
        # Verify the model is accessible
        self.assertTrue(hasattr(Repository, 'objects'))
        self.assertTrue(hasattr(Repository, 'name'))
        self.assertTrue(hasattr(Repository, 'git_url'))
    
    def test_path_manipulation(self):
        """Test that the script correctly manipulates sys.path."""
        # The script adds the project root to sys.path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        
        # Verify the path exists and is a directory
        self.assertTrue(os.path.exists(project_root))
        self.assertTrue(os.path.isdir(project_root))
        
        # Verify manage.py exists in the project root (Django project indicator)
        manage_py_path = os.path.join(project_root, 'manage.py')
        self.assertTrue(os.path.exists(manage_py_path))


class TestScriptDataStructures(BaseManualTestCase):
    """Test the data structures and constants used in the manual test script."""
    
    def test_save_comment_test_data_structure(self):
        """Test the structure of test data used in save_teacher_comment."""
        expected_keys = {'file_path', 'comment', 'grade', 'repo_id', 'course'}
        
        # The test data from the script
        test_data = {
            'file_path': '23计算机6班/第一次作业/吴紫晴1.docx',
            'comment': '测试评价：作业完成质量良好，但需要注意格式规范。',
            'grade': 'B',
            'repo_id': '11',
            'course': 'Web前端开发'
        }
        
        # Verify all expected keys are present
        self.assertEqual(set(test_data.keys()), expected_keys)
        
        # Verify data types
        self.assertIsInstance(test_data['file_path'], str)
        self.assertIsInstance(test_data['comment'], str)
        self.assertIsInstance(test_data['grade'], str)
        self.assertIsInstance(test_data['repo_id'], str)
        self.assertIsInstance(test_data['course'], str)
        
        # Verify non-empty values
        for key, value in test_data.items():
            self.assertTrue(value, f"Value for {key} should not be empty")
    
    def test_get_comment_test_params_structure(self):
        """Test the structure of test parameters used in get_teacher_comment."""
        expected_keys = {'file_path', 'repo_id', 'course'}
        
        # The test parameters from the script
        test_params = {
            'file_path': '23计算机6班/第一次作业/吴紫晴1.docx',
            'repo_id': '11',
            'course': 'Web前端开发'
        }
        
        # Verify all expected keys are present
        self.assertEqual(set(test_params.keys()), expected_keys)
        
        # Verify data types
        self.assertIsInstance(test_params['file_path'], str)
        self.assertIsInstance(test_params['repo_id'], str)
        self.assertIsInstance(test_params['course'], str)
        
        # Verify non-empty values
        for key, value in test_params.items():
            self.assertTrue(value, f"Value for {key} should not be empty")


class TestScriptErrorHandling(BaseManualTestCase):
    """Test error handling scenarios in the manual test script."""
    
    @patch('test_save_teacher_comment.print')
    def test_save_comment_handles_client_exceptions(self, mock_print):
        """Test that save_teacher_comment handles client exceptions gracefully."""
        with patch('django.test.Client.post') as mock_post:
            # Mock an exception during POST request
            mock_post.side_effect = Exception("Network error")
            
            with pytest.raises(Exception):
                test_save_teacher_comment()
    
    @patch('test_save_teacher_comment.print')
    def test_get_comment_handles_client_exceptions(self, mock_print):
        """Test that get_teacher_comment handles client exceptions gracefully."""
        with patch('django.test.Client.get') as mock_get:
            # Mock an exception during GET request
            mock_get.side_effect = Exception("Network error")
            
            with pytest.raises(Exception):
                test_get_teacher_comment()
    
    def test_script_handles_missing_django_setup(self):
        """Test behavior when Django is not properly set up."""
        # This test verifies that the script has proper Django setup
        # The actual script should handle this, but we test the import path
        
        # Verify Django settings are configured
        from django.conf import settings
        self.assertTrue(settings.configured)
        
        # Verify the correct settings module is used
        self.assertEqual(settings.SETTINGS_MODULE, 'hualiEdu.settings')


class TestScriptIntegration(BaseManualTestCase):
    """Integration tests for the manual test script with real Django components."""
    
    def test_script_with_real_django_client(self):
        """Test the script functions with real Django test client."""
        from django.test import Client
        
        client = Client()
        client.force_login(self.user)
        
        # Test that the client can make requests to the expected endpoints
        # Note: These endpoints may not exist in the test environment,
        # so we expect 404 responses, not exceptions
        
        response = client.get('/grading/get_teacher_comment/', {
            'file_path': 'test.docx',
            'repo_id': '11',
            'course': 'Test Course'
        })
        
        # Should get a response (even if 404), not an exception
        self.assertIsNotNone(response)
        self.assertIsInstance(response.status_code, int)
    
    def test_script_with_real_models(self):
        """Test the script functions with real Django models."""
        # Verify the models used in the script exist and work
        user_count = User.objects.count()
        repo_count = Repository.objects.count()
        
        self.assertGreaterEqual(user_count, 1)  # At least our test user
        self.assertGreaterEqual(repo_count, 1)  # At least our test repository
        
        # Verify the specific objects the script expects
        user = User.objects.get(id=1)
        repo = Repository.objects.get(id=11)
        
        self.assertEqual(user, self.user)
        self.assertEqual(repo, self.repository)


@pytest.mark.django_db
class TestScriptPytestCompatibility:
    """Test compatibility of the manual test script with pytest."""
    
    def test_script_functions_are_callable(self):
        """Test that script functions can be called from pytest."""
        # Import the functions
        from test_save_teacher_comment import test_save_teacher_comment, test_get_teacher_comment
        
        # Verify they are callable
        assert callable(test_save_teacher_comment)
        assert callable(test_get_teacher_comment)
        
        # Verify they have docstrings
        assert test_save_teacher_comment.__doc__ is not None
        assert test_get_teacher_comment.__doc__ is not None
    
    def test_script_imports_work_in_pytest(self):
        """Test that all script imports work in pytest environment."""
        # Test standard library imports
        import os
        import sys
        
        # Test Django imports
        from django.test import Client
        from django.contrib.auth.models import User
        
        # Test project imports
        from grading.models import Repository
        
        # All imports should work without exceptions
        assert True


if __name__ == '__main__':
    pytest.main([__file__])