"""
Integration tests for grading/views.py

This module tests complex integration scenarios, view decorators,
middleware interactions, and end-to-end workflows.
"""

import json
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

import pytest
from django.test import TestCase, RequestFactory, Client, override_settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from docx import Document

from grading.models import (
    Repository, Course, Homework, Semester, GlobalConfig, 
    FileGradeStatus, Tenant, UserProfile, Class
)
from grading.views import (
    index,
    grading_simple,
    grading_page,
    get_dir_file_count,
    require_staff_user,
    validate_file_operation,
    auto_create_or_update_course,
    _resolve_homework_directory,
    _resolve_homework_directory_by_relative_path,
    _fallback_search_homework_folder,
)

User = get_user_model()


class BaseIntegrationTestCase(TestCase):
    """Base test case for integration tests."""
    
    def setUp(self):
        """Set up test data for integration tests."""
        self.factory = RequestFactory()
        self.client = Client()
        
        # Create test users
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True,
            first_name='Staff',
            last_name='User'
        )
        
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='testpass123',
            is_staff=False
        )
        
        # Create tenant and user profiles
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            domain='test.example.com'
        )
        
        self.staff_profile = UserProfile.objects.create(
            user=self.staff_user,
            tenant=self.tenant,
            repo_base_dir='~/test_jobs'
        )
        
        self.regular_profile = UserProfile.objects.create(
            user=self.regular_user,
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
            name='Test Course',
            course_type='theory',
            semester=self.semester,
            teacher=self.staff_user,
            location='Room 101',
            tenant=self.tenant
        )
        
        # Create test class
        self.test_class = Class.objects.create(
            course=self.course,
            name='Class A',
            tenant=self.tenant
        )
        
        # Create test repository
        self.repository = Repository.objects.create(
            name='test-repo',
            url='https://github.com/test/repo.git',
            owner=self.staff_user,
            tenant=self.tenant,
            repo_type='local',
            local_path='/tmp/test-repo',
            class_obj=self.test_class
        )
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        # Set up global config
        GlobalConfig.objects.create(
            key='default_repo_base_dir',
            value=self.temp_dir
        )
    
    def add_middleware_to_request(self, request, user=None):
        """Add necessary middleware to request for testing."""
        # Add session middleware
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        # Add authentication middleware
        auth_middleware = AuthenticationMiddleware(lambda req: None)
        auth_middleware.process_request(request)
        
        # Add user and related attributes
        if user:
            request.user = user
            if hasattr(user, 'userprofile'):
                request.user_profile = user.userprofile
                request.tenant = user.userprofile.tenant
            else:
                request.user_profile = None
                request.tenant = self.tenant
        
        # Add messages middleware
        msg_middleware = MessageMiddleware(lambda req: None)
        msg_middleware.process_request(request)
        
        return request


class TestViewDecorators(BaseIntegrationTestCase):
    """Test view decorators and permission handling."""
    
    def test_require_staff_user_decorator_success(self):
        """Test require_staff_user decorator with staff user."""
        @require_staff_user
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/')
        request = self.add_middleware_to_request(request, self.staff_user)
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
    
    def test_require_staff_user_decorator_non_staff(self):
        """Test require_staff_user decorator with non-staff user."""
        @require_staff_user
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/')
        request = self.add_middleware_to_request(request, self.regular_user)
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], '无权限访问')
    
    def test_require_staff_user_decorator_unauthenticated(self):
        """Test require_staff_user decorator with unauthenticated user."""
        @require_staff_user
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/')
        request = self.add_middleware_to_request(request)
        request.user = Mock()
        request.user.is_authenticated = False
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], '请先登录')
    
    def test_validate_file_operation_decorator_success(self):
        """Test validate_file_operation decorator with valid file."""
        @validate_file_operation()
        def test_view(request):
            return JsonResponse({'path': request.validated_file_path})
        
        # Create test file
        test_file = os.path.join(self.temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        request = self.factory.post('/', {'file_path': 'test.txt'})
        request = self.add_middleware_to_request(request, self.staff_user)
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['path'], test_file)
    
    def test_validate_file_operation_decorator_invalid_file(self):
        """Test validate_file_operation decorator with invalid file."""
        @validate_file_operation()
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.post('/', {'file_path': 'nonexistent.txt'})
        request = self.add_middleware_to_request(request, self.staff_user)
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertIn('文件不存在', data['message'])
    
    def test_validate_file_operation_decorator_missing_path(self):
        """Test validate_file_operation decorator with missing file path."""
        @validate_file_operation()
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.post('/', {})
        request = self.add_middleware_to_request(request, self.staff_user)
        
        response = test_view(request)
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], '未提供文件路径')


class TestMainViews(BaseIntegrationTestCase):
    """Test main view functions."""
    
    def test_index_view_authenticated_staff(self):
        """Test index view with authenticated staff user."""
        request = self.factory.get('/')
        request = self.add_middleware_to_request(request, self.staff_user)
        
        response = index(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('current_semester', response.context_data)
        self.assertIn('user_courses', response.context_data)
        self.assertIn('repository_stats', response.context_data)
    
    def test_index_view_unauthenticated(self):
        """Test index view with unauthenticated user."""
        request = self.factory.get('/')
        request = self.add_middleware_to_request(request)
        request.user = Mock()
        request.user.is_authenticated = False
        
        response = index(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['user_courses'], [])
        self.assertEqual(response.context_data['repository_stats'], {})
    
    def test_grading_simple_view_success(self):
        """Test grading_simple view with proper permissions."""
        request = self.factory.get('/')
        request = self.add_middleware_to_request(request, self.staff_user)
        
        response = grading_simple(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('repositories', response.context_data)
        self.assertIn('page_title', response.context_data)
        self.assertEqual(response.context_data['page_title'], '简化评分页面')
    
    def test_grading_simple_view_forbidden(self):
        """Test grading_simple view with insufficient permissions."""
        request = self.factory.get('/')
        request = self.add_middleware_to_request(request, self.regular_user)
        
        response = grading_simple(request)
        
        self.assertIsInstance(response, HttpResponseForbidden)
    
    def test_grading_page_view_success(self):
        """Test grading_page view with proper setup."""
        request = self.factory.get('/')
        request = self.add_middleware_to_request(request, self.staff_user)
        
        response = grading_page(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('repositories', response.context_data)
        self.assertIn('page_title', response.context_data)
    
    def test_get_dir_file_count_json_request(self):
        """Test get_dir_file_count with JSON request."""
        # Create test directory with files
        test_dir = os.path.join(self.temp_dir, 'test_count')
        os.makedirs(test_dir)
        
        # Create some .docx files
        for i in range(3):
            with open(os.path.join(test_dir, f'file{i}.docx'), 'w') as f:
                f.write('test')
        
        request_data = json.dumps({'path': 'test_count'})
        request = self.factory.post(
            '/',
            data=request_data,
            content_type='application/json'
        )
        request = self.add_middleware_to_request(request, self.staff_user)
        
        with patch('grading.views.get_directory_file_count_cached') as mock_count:
            mock_count.return_value = 3
            
            response = get_dir_file_count(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), '3')
    
    def test_get_dir_file_count_form_request(self):
        """Test get_dir_file_count with form request."""
        request = self.factory.post('/', {'path': 'test_dir'})
        request = self.add_middleware_to_request(request, self.staff_user)
        
        with patch('grading.views.get_directory_file_count_cached') as mock_count:
            mock_count.return_value = 5
            
            response = get_dir_file_count(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), '5')


class TestCourseManagement(BaseIntegrationTestCase):
    """Test course management functions."""
    
    def test_auto_create_or_update_course_new_course(self):
        """Test auto_create_or_update_course with new course."""
        result = auto_create_or_update_course('New Lab Course', self.staff_user)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.name, 'New Lab Course')
        self.assertEqual(result.course_type, 'lab')
        self.assertEqual(result.teacher, self.staff_user)
        self.assertEqual(result.semester, self.semester)
    
    def test_auto_create_or_update_course_existing_course(self):
        """Test auto_create_or_update_course with existing course."""
        result = auto_create_or_update_course('Test Course', self.staff_user)
        
        self.assertEqual(result, self.course)
        self.assertEqual(result.course_type, 'theory')  # Should not change
    
    def test_auto_create_or_update_course_no_semester(self):
        """Test auto_create_or_update_course with no available semester."""
        # Delete all semesters
        Semester.objects.all().delete()
        
        result = auto_create_or_update_course('New Course', self.staff_user)
        
        self.assertIsNone(result)
    
    def test_auto_create_or_update_course_no_teacher(self):
        """Test auto_create_or_update_course with no available teacher."""
        # Remove staff status from all users
        User.objects.update(is_staff=False)
        
        result = auto_create_or_update_course('New Course', None)
        
        self.assertIsNone(result)


class TestHomeworkResolution(BaseIntegrationTestCase):
    """Test homework directory resolution functions."""
    
    def setUp(self):
        super().setUp()
        
        # Create homework
        self.homework = Homework.objects.create(
            course=self.course,
            title='Test Homework',
            homework_type='normal',
            folder_name='homework1',
            description='Test homework',
            tenant=self.tenant,
            class_obj=self.test_class
        )
        
        # Create directory structure
        self.repo_dir = os.path.join(self.temp_dir, 'repo')
        self.course_dir = os.path.join(self.repo_dir, 'Test Course')
        self.class_dir = os.path.join(self.course_dir, 'Class A')
        self.homework_dir = os.path.join(self.class_dir, 'homework1')
        
        os.makedirs(self.homework_dir)
        
        # Update repository path
        self.repository.local_path = self.repo_dir
        self.repository.save()
    
    def test_resolve_homework_directory_success(self):
        """Test _resolve_homework_directory with valid structure."""
        repositories = [self.repository]
        
        result, meta = _resolve_homework_directory(self.homework, repositories)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['homework_path'], self.homework_dir)
        self.assertEqual(result['class_path'], self.class_dir)
        self.assertEqual(result['repository'], self.repository)
        self.assertFalse(result['found_via_fallback'])
    
    def test_resolve_homework_directory_fallback_search(self):
        """Test _resolve_homework_directory with fallback search."""
        # Create homework in different location
        fallback_dir = os.path.join(self.repo_dir, 'other_location', 'homework1')
        os.makedirs(fallback_dir)
        
        # Remove the expected location
        shutil.rmtree(self.homework_dir)
        
        repositories = [self.repository]
        
        with patch('grading.views._fallback_search_homework_folder') as mock_fallback:
            mock_fallback.return_value = [fallback_dir]
            
            result, meta = _resolve_homework_directory(self.homework, repositories)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['homework_path'], fallback_dir)
        self.assertTrue(result['found_via_fallback'])
    
    def test_resolve_homework_directory_not_found(self):
        """Test _resolve_homework_directory when homework not found."""
        # Remove homework directory
        shutil.rmtree(self.homework_dir)
        
        repositories = [self.repository]
        
        result, meta = _resolve_homework_directory(self.homework, repositories)
        
        self.assertIsNone(result)
        self.assertIn('attempted_paths', meta)
    
    def test_resolve_homework_directory_by_relative_path_success(self):
        """Test _resolve_homework_directory_by_relative_path with valid path."""
        relative_path = 'Test Course/Class A/homework1'
        repositories = [self.repository]
        
        result, meta = _resolve_homework_directory_by_relative_path(
            relative_path, repositories
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['homework_path'], self.homework_dir)
        self.assertTrue(result['found_via_manual_selection'])
        self.assertEqual(meta['resolved_via'], 'manual_selection')
    
    def test_resolve_homework_directory_by_relative_path_invalid(self):
        """Test _resolve_homework_directory_by_relative_path with invalid path."""
        invalid_paths = [
            '../../../etc/passwd',
            '/absolute/path',
            '',
            None
        ]
        
        repositories = [self.repository]
        
        for invalid_path in invalid_paths:
            with self.subTest(invalid_path=invalid_path):
                result, meta = _resolve_homework_directory_by_relative_path(
                    invalid_path, repositories
                )
                
                self.assertIsNone(result)
                self.assertIn('error', meta)
    
    def test_fallback_search_homework_folder_success(self):
        """Test _fallback_search_homework_folder finds homework."""
        # Create homework in nested location
        nested_dir = os.path.join(self.repo_dir, 'deep', 'nested', 'homework1')
        os.makedirs(nested_dir)
        
        result = _fallback_search_homework_folder(
            self.repo_dir, 'homework1', preferred_root=self.course_dir
        )
        
        self.assertGreater(len(result), 0)
        self.assertIn(self.homework_dir, result)
    
    def test_fallback_search_homework_folder_depth_limit(self):
        """Test _fallback_search_homework_folder respects depth limit."""
        # Create very deep structure
        very_deep_dir = self.repo_dir
        for i in range(10):  # Create 10 levels deep
            very_deep_dir = os.path.join(very_deep_dir, f'level{i}')
        
        very_deep_homework = os.path.join(very_deep_dir, 'homework1')
        os.makedirs(very_deep_homework)
        
        result = _fallback_search_homework_folder(
            self.repo_dir, 'homework1'
        )
        
        # Should not find the very deep homework due to depth limit
        self.assertNotIn(very_deep_homework, result)
    
    def test_fallback_search_homework_folder_count_limit(self):
        """Test _fallback_search_homework_folder respects count limit."""
        # Create many homework folders with same name
        for i in range(10):
            homework_dir = os.path.join(self.repo_dir, f'location{i}', 'homework1')
            os.makedirs(homework_dir)
        
        result = _fallback_search_homework_folder(
            self.repo_dir, 'homework1'
        )
        
        # Should respect the maximum matches limit
        self.assertLessEqual(len(result), 3)  # FALLBACK_HOMEWORK_SEARCH_MAX_MATCHES


class TestErrorHandlingIntegration(BaseIntegrationTestCase):
    """Test error handling in integration scenarios."""
    
    def test_view_with_database_error(self):
        """Test view behavior when database errors occur."""
        request = self.factory.get('/')
        request = self.add_middleware_to_request(request, self.staff_user)
        
        with patch('grading.views.get_user_repositories_optimized') as mock_repos:
            mock_repos.side_effect = Exception('Database connection failed')
            
            response = grading_simple(request)
        
        # Should handle error gracefully
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context_data)
    
    def test_view_with_file_system_error(self):
        """Test view behavior when file system errors occur."""
        request = self.factory.get('/')
        request = self.add_middleware_to_request(request, self.staff_user)
        
        with patch('os.path.exists') as mock_exists:
            mock_exists.side_effect = OSError('File system error')
            
            response = grading_simple(request)
        
        # Should handle error gracefully
        self.assertEqual(response.status_code, 200)
    
    def test_middleware_missing_attributes(self):
        """Test view behavior when middleware attributes are missing."""
        request = self.factory.get('/')
        request.user = self.staff_user
        # Missing user_profile and tenant attributes
        
        # Should handle missing attributes gracefully
        try:
            response = index(request)
            # If no exception, the view handled it gracefully
            self.assertEqual(response.status_code, 200)
        except AttributeError:
            # If AttributeError, the view needs better error handling
            self.fail("View should handle missing middleware attributes gracefully")


class TestMultiTenantIntegration(BaseIntegrationTestCase):
    """Test multi-tenant functionality integration."""
    
    def setUp(self):
        super().setUp()
        
        # Create second tenant
        self.tenant2 = Tenant.objects.create(
            name='Second Tenant',
            domain='tenant2.example.com'
        )
        
        # Create user for second tenant
        self.tenant2_user = User.objects.create_user(
            username='tenant2user',
            email='tenant2@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.tenant2_profile = UserProfile.objects.create(
            user=self.tenant2_user,
            tenant=self.tenant2,
            repo_base_dir='~/tenant2_jobs'
        )
        
        # Create course for second tenant
        self.tenant2_course = Course.objects.create(
            name='Tenant2 Course',
            course_type='lab',
            semester=self.semester,
            teacher=self.tenant2_user,
            location='Room 202',
            tenant=self.tenant2
        )
    
    def test_tenant_isolation_in_course_creation(self):
        """Test that course creation respects tenant isolation."""
        # Create course as tenant1 user
        request = self.factory.get('/')
        request = self.add_middleware_to_request(request, self.staff_user)
        
        course1 = auto_create_or_update_course('Shared Course Name', self.staff_user)
        
        # Create course with same name as tenant2 user
        request2 = self.factory.get('/')
        request2 = self.add_middleware_to_request(request2, self.tenant2_user)
        
        course2 = auto_create_or_update_course('Shared Course Name', self.tenant2_user)
        
        # Should create separate courses for different tenants
        self.assertNotEqual(course1.id, course2.id)
        self.assertEqual(course1.name, course2.name)
        self.assertNotEqual(course1.teacher, course2.teacher)
    
    def test_repository_access_tenant_isolation(self):
        """Test that repository access respects tenant boundaries."""
        # Create repository for tenant2
        tenant2_repo = Repository.objects.create(
            name='tenant2-repo',
            url='https://github.com/tenant2/repo.git',
            owner=self.tenant2_user,
            tenant=self.tenant2,
            repo_type='local',
            local_path='/tmp/tenant2-repo'
        )
        
        # Staff user from tenant1 should not see tenant2's repositories
        request = self.factory.get('/')
        request = self.add_middleware_to_request(request, self.staff_user)
        
        with patch('grading.views.get_user_repositories_optimized') as mock_repos:
            # Mock should only return repositories for the user's tenant
            mock_repos.return_value = Repository.objects.filter(
                owner=self.staff_user,
                tenant=self.staff_user.userprofile.tenant
            )
            
            response = grading_simple(request)
        
        # Verify tenant isolation was respected
        mock_repos.assert_called_with(self.staff_user, is_active=True)


@pytest.mark.django_db
class TestEndToEndWorkflows:
    """End-to-end workflow tests."""
    
    def test_complete_grading_workflow(self, client, django_user_model):
        """Test complete grading workflow from login to grade submission."""
        # Create user and login
        user = django_user_model.objects.create_user(
            username='teacher',
            password='testpass123',
            is_staff=True
        )
        
        # Create tenant and profile
        tenant = Tenant.objects.create(
            name='Test School',
            domain='school.example.com'
        )
        
        profile = UserProfile.objects.create(
            user=user,
            tenant=tenant,
            repo_base_dir='~/school_jobs'
        )
        
        client.force_login(user)
        
        # 1. Access grading page
        response = client.get('/grading/')
        assert response.status_code == 200
        
        # 2. Get course info (auto-create)
        response = client.get('/api/course_info/', {
            'course_name': 'Computer Science 101',
            'auto_create': 'true'
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['success']
        assert data['course']['auto_created']
        
        # 3. Update course type to lab
        response = client.post('/api/update_course_type/', {
            'course_name': 'Computer Science 101',
            'course_type': 'lab'
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['success']
        assert data['course']['course_type'] == 'lab'
        
        # 4. Create homework (auto-create)
        response = client.get('/api/homework_info/', {
            'course_name': 'Computer Science 101',
            'homework_folder': 'lab1',
            'auto_create': 'true'
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['success']
        assert data['homework']['folder_name'] == 'lab1'
        assert data['homework']['is_lab_report']  # Should be True for lab course
    
    def test_repository_management_workflow(self, client, django_user_model):
        """Test repository management workflow."""
        # Create user and login
        user = django_user_model.objects.create_user(
            username='teacher',
            password='testpass123',
            is_staff=True
        )
        
        # Create tenant and profile
        tenant = Tenant.objects.create(
            name='Test School',
            domain='school.example.com'
        )
        
        profile = UserProfile.objects.create(
            user=user,
            tenant=tenant,
            repo_base_dir='~/school_jobs'
        )
        
        # Create repository
        repo = Repository.objects.create(
            name='test-repo',
            url='https://github.com/school/assignments.git',
            owner=user,
            tenant=tenant,
            repo_type='local',
            local_path='/tmp/assignments'
        )
        
        client.force_login(user)
        
        # 1. Get courses list
        response = client.get('/api/courses_list/', {
            'repo_id': str(repo.id)
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        
        # 2. Get directory tree
        response = client.get('/api/directory_tree/', {
            'repo_id': str(repo.id),
            'course': 'Computer Science',
            'path': ''
        })
        
        assert response.status_code == 200
        data = response.json()
        assert 'children' in data


if __name__ == '__main__':
    pytest.main([__file__])